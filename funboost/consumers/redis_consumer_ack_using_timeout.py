# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2024/8/11 0011 13:32
import json
import time
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.serialization import Serialization
from funboost.utils.decorators import RedisDistributedLockContextManager
from funboost.utils.redis_manager import RedisMixin


class RedisConsumerAckUsingTimeout(AbstractConsumer, RedisMixin):
    """
    Consumer implemented using Redis as middleware.
    Uses timeout-based automatic re-queueing: if a message is not acked within the timeout (e.g., due to sudden power loss, restart, or other reasons preventing active ack), it is automatically re-queued.
    """





    def custom_init(self):
        self._unack_zset_name = f'{self._queue_name}__unack_using_timeout'
        self._ack_timeout = self.consumer_params.broker_exclusive_config['ack_timeout']
        self._last_show_unack_ts = time.time()

    def start_consuming_message(self):
        self.consumer_params.is_send_consumer_heartbeat_to_redis = True
        super().start_consuming_message()
        self.keep_circulating(10, block=False)(self._requeue_tasks_which_unconfirmed)()

    # def _add_task_str_to_unack_zset(self, task_str, ):
    #     self.redis_db_frame.zadd(self._unack_zset_name, {task_str: time.time()})

    def _confirm_consume(self, kw):
        self.redis_db_frame.zrem(self._unack_zset_name, kw['task_str'])

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, Serialization.to_json_str(kw['body']))

    def _dispatch_task(self):
        lua = '''
                     local v = redis.call("lpop", KEYS[1])
                     if v then
                     redis.call('zadd',KEYS[2],ARGV[1],v)
                      end
                     return v
                '''
        script = self.redis_db_frame.register_script(lua)
        while True:
            return_v = script(keys=[self._queue_name, self._unack_zset_name], args=[time.time()])
            if return_v:
                task_str = return_v
                kw = {'body': task_str, 'task_str': task_str}
                self._submit_task(kw)
            else:
                time.sleep(0.1)

    def _requeue_tasks_which_unconfirmed(self):
        """This approach is not suitable for inherently long-running functions, it is too rigid"""
        # Prevent simultaneous scanning and re-queueing of unconfirmed tasks across multiple processes or machines. Use a distributed lock.
        lock_key = f'funboost_lock__requeue_tasks_which_unconfirmed_timeout:{self._queue_name}'
        with RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ) as lock:
            if lock.has_aquire_lock:
                time_max = time.time() - self._ack_timeout
                for value in self.redis_db_frame.zrangebyscore(self._unack_zset_name, 0, time_max):
                    self.logger.warning(f'Failed to confirm consumption within {self._ack_timeout} seconds, re-queuing unacknowledged task {value} to queue {self._queue_name}')
                    self._requeue({'body': value})
                    self.redis_db_frame.zrem(self._unack_zset_name, value)
                if time.time() - self._last_show_unack_ts > 600:  # Don't display too frequently
                    self.logger.info(f'{self._unack_zset_name} has '
                                     f'{self.redis_db_frame.zcard(self._unack_zset_name)} pending consumption confirmation tasks')
                    self._last_show_unack_ts = time.time()
