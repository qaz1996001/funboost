# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
"""
This is the enhanced version of Redis consumption with acknowledgment, much more complex than the redis_consumer implementation.
This ensures that tasks are not lost with arbitrary repeated restarts. Without lua, there is an extremely small probability of losing one task during arbitrary restarts.

This is a Redis queue implementation that supports task priority.
"""
import json
import time

import redis5

from funboost.consumers.redis_consumer_ack_able import RedisConsumerAckAble


class RedisPriorityConsumer(RedisConsumerAckAble):
    """
       Uses multiple Redis lists to implement Redis queue priority support. brpop can monitor multiple Redis keys.
       Determines which queue to send to based on the message's priority. This idea is the same as kombu's Redis queue priority implementation used by celery.

       Note: rabbitmq and celery queue priorities refer to each message in the same queue having different priorities. Messages don't follow FIFO; higher priority messages are fetched first.
              Queue priority is actually the priority of messages within a specific queue, which is the native concept of x-max-priority.

              Some people mistakenly think queue priority means having two queues queuexx and queueyy, and consuming queuexx messages first. This is completely wrong.
              Queue priority means each message within a queue can have different priorities, not comparing which queue name has higher priority among different queue names.
    """
    """Usage is as follows.
    First, if using Redis as a priority-supporting message queue, select broker_kind = BrokerEnum.REDIS_PRIORITY in @boost.
    Second, broker_exclusive_config={'x-max-priority':4} means how many priority levels task messages in this queue support. Generally 5 is sufficient.
    Third, when publishing messages, use publish instead of push. Publishing requires adding task_options=TaskOptions(other_extra_params={'priroty': priorityxx}),
         where priorityxx must be an integer, greater than or equal to 0 and less than the queue's x-max-priority. The x-max-priority concept is native to RabbitMQ, and the parameter name is the same in Celery.

         The higher the priority of a published message, the earlier it is fetched, thus breaking the FIFO rule. For example, high-priority messages can be used for real-time function execution for VIP users, while low-priority messages can be used for offline batch processing.

    from funboost import register_custom_broker, boost, TaskOptions,BrokerEnum

    @boost('test_redis_priority_queue3', broker_kind=BrokerEnum.REDIS_PRIORITY, qps=5,concurrent_num=2,broker_exclusive_config={'x-max-priority':4})
    def f(x):
        print(x)


    if __name__ == '__main__':
        for i in range(1000):
            randx = random.randint(1, 4)
            f.publish({'x': randx}, task_options=TaskOptions(other_extra_params={'priroty': randx}))
        print(f.get_message_count())
        f.consume()
    """



    def _dispatch_task0000(self):

        while True:
            # task_str_list = script(keys=[queues_str, self._unack_zset_name], args=[time.time()])
            task_tuple = self.redis_db_frame.blpop(keys=self.publisher_of_same_queue.queue_list, timeout=60)  # Monitors multiple key names, indirectly implementing priority — the same design idea as kombu's Redis priority support.
            if task_tuple:
                msg = task_tuple[1]
                self.redis_db_frame.zadd(self._unack_zset_name, {msg: time.time()})
                # self.logger.debug(task_tuple)
                # self.logger.debug(f'Message fetched from redis queue [{self._queue_name}]:  {task_str_list}  ')
                kw = {'body': msg, 'task_str': msg}
                self._submit_task(kw)

    def _dispatch_task(self):
        """https://redis.readthedocs.io/en/latest/advanced_features.html#default-pipelines """
        while True:
            # task_str_list = script(keys=[queues_str, self._unack_zset_name], args=[time.time()])
            while True:
                try:
                    with self.redis_db_frame.pipeline() as p:
                        p.watch(self._unack_zset_name, *self.publisher_of_same_queue.queue_list, )
                        task_tuple = p.blpop(keys=self.publisher_of_same_queue.queue_list, timeout=60)  # Monitors multiple key names, indirectly implementing priority — the same design idea as kombu's Redis priority support.
                        # print(task_tuple)
                        if task_tuple:
                            msg = task_tuple[1]
                            p.zadd(self._unack_zset_name, {msg: time.time()})
                            # self.logger.debug(task_tuple)
                            p.unwatch()
                            p.execute()
                            break
                except redis5.WatchError:
                    continue
            if task_tuple:
                # self.logger.debug(f'Message fetched from redis queue [{self._queue_name}]:  {task_str_list}  ')
                kw = {'body': msg, 'task_str': msg}
                self._submit_task(kw)

    def _requeue(self, kw):
        self.publisher_of_same_queue.publish(kw['body'])
