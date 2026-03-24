# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2021/4/3 0008 13:32
import json
import redis5
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.utils import decorators
from funboost.utils.redis_manager import RedisMixin


class RedisStreamConsumer(AbstractConsumer, RedisMixin):
    """
    Consumer implemented using Redis stream structure as middleware. Requires Redis 5.0+. Redis stream structure is Redis's message queue, similar in concept to kafka, with functionality far exceeding the list structure.
    """

    def custom_init(self):
        self.group = self.consumer_params.broker_exclusive_config['group']

    def start_consuming_message(self):
        redis_server_info_dict = self.redis_db_frame.info()
        # print(redis_server_info_dict)
        if float(redis_server_info_dict['redis_version'][0]) < 5:
            raise EnvironmentError('Redis server version 5.0 or above is required to support the stream data structure. '
                                   'Please upgrade the server, otherwise use REDIS_ACK_ABLE mode with Redis list structure')
        if self.redis_db_frame.type(self._queue_name) == 'list':
            raise EnvironmentError(f'Detected existing key {self._queue_name} with type list. Must use a different queue name or delete this list-type key. '
                                   f'RedisStreamConsumer uses the stream data structure')
        self.consumer_params.is_send_consumer_heartbeat_to_redis = True
        super().start_consuming_message()
        self.keep_circulating(60, block=False)(self._requeue_tasks_which_unconfirmed)()

    def _dispatch_task(self):
        pull_msg_batch_size = self.consumer_params.broker_exclusive_config['pull_msg_batch_size']

        try:
            self.redis_db_frame.xgroup_create(self._queue_name,self.group , id=0, mkstream=True)
        except redis5.exceptions.ResponseError as e:
            self.logger.info(e)  # BUSYGROUP Consumer Group name already exists. Cannot create consumer group repeatedly.
        while True:
            # Redis server must be 5.0+, and ensure the key type is stream, not list data structure.
            results = self.redis_db_frame.xreadgroup(self.group, self.consumer_identification,
                                                              {self.queue_name: ">"}, count=pull_msg_batch_size, block=60 * 1000)
            if results:
                # self.logger.debug(f'从redis的 [{self._queue_name}] stream 中 取出的消息是：  {results}  ')
                self._print_message_get_from_broker( results)
                # print(results[0][1])
                for msg_id, msg in results[0][1]:
                    kw = {'body': msg[''], 'msg_id': msg_id}
                    self._submit_task(kw)

    def _confirm_consume(self, kw):
        # self.redis_db_frame.xack(self._queue_name, 'distributed_frame_group', kw['msg_id'])
        # self.redis_db_frame.xdel(self._queue_name, kw['msg_id']) # 便于xlen
        with self.redis_db_frame.pipeline() as pipe:
            pipe.xack(self._queue_name, self.group, kw['msg_id'])
            pipe.xdel(self._queue_name, kw['msg_id'])  # Delete directly without retaining, for accurate xlen
            pipe.execute()

    def _requeue(self, kw):
        self.redis_db_frame.xack(self._queue_name, self.group, kw['msg_id'])
        self.redis_db_frame.xadd(self._queue_name, {'': json.dumps(kw['body'])})
        # print(self.redis_db_frame.xclaim(self._queue_name,
        #                                     'distributed_frame_group', self.consumer_identification,
        #                                     min_idle_time=0, message_ids=[kw['msg_id']]))

    def _requeue_tasks_which_unconfirmed(self):
        lock_key = f'funboost_lock__requeue_tasks_which_unconfirmed:{self._queue_name}'
        with decorators.RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ) as lock:
            if lock.has_aquire_lock:
                self._distributed_consumer_statistics.send_heartbeat()
                current_queue_hearbeat_ids = self._distributed_consumer_statistics.get_queue_heartbeat_ids(without_time=True)
                xinfo_consumers = self.redis_db_frame.xinfo_consumers(self._queue_name, self.group)
                # print(current_queue_hearbeat_ids)
                # print(xinfo_consumers)
                for xinfo_item in xinfo_consumers:
                    # print(xinfo_item)
                    if xinfo_item['idle'] > 7 * 24 * 3600 * 1000 and xinfo_item['pending'] == 0:
                        self.redis_db_frame.xgroup_delconsumer(self._queue_name, self.group, xinfo_item['name'])
                    if xinfo_item['name'] not in current_queue_hearbeat_ids and xinfo_item['pending'] > 0:  # 说明这个消费者掉线断开或者关闭了。
                        pending_msg_list = self.redis_db_frame.xpending_range(
                            self._queue_name, self.group, '-', '+', 1000, xinfo_item['name'])
                        if pending_msg_list:
                            # min_idle_time is not needed because a distributed lock is used, so idle minimum time based judgment is not needed. Also, the heartbeat-based consumption confirmation helper is started, with 100% accuracy in detecting disconnected or closed consumers.
                            xclaim_task_list = self.redis_db_frame.xclaim(self._queue_name, self.group,
                                                                                   self.consumer_identification, force=True,
                                                                                   min_idle_time=0 * 1000,
                                                                                   message_ids=[task_item['message_id'] for task_item in pending_msg_list])
                            if xclaim_task_list:
                                self.logger.warning(f' Consumer {self.consumer_identification} in group {self.group} of {self._queue_name} claimed {len(xclaim_task_list)} tasks from disconnected consumer {xinfo_item["name"]}'
                                                    f', details: {xclaim_task_list} ')
                                for task in xclaim_task_list:
                                    kw = {'body': task[1][''], 'msg_id': task[0]}
                                    self._submit_task(kw)
