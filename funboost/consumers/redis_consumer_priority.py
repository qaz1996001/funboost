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
    """用法如下。
    第一，如果使用redis做支持优先级的消息队列， @boost中要选择 broker_kind = BrokerEnum.REDIS_PRIORITY
    第二，broker_exclusive_config={'x-max-priority':4} 意思是这个队列中的任务消息支持多少种优先级，一般写5就完全够用了。
    第三，发布消息时候要使用publish而非push,发布要加入参  task_options=TaskOptions(other_extra_params={'priroty': priorityxx})，
         其中 priorityxx 必须是整数，要大于等于0且小于队列的x-max-priority。x-max-priority这个概念是rabbitmq的原生概念，celery中也是这样的参数名字。

         发布的消息priroty 越大，那么该消息就越先被取出来，这样就达到了打破先进先出的规律。比如优先级高的消息可以给vip用户来运行函数实时，优先级低的消息可以离线跑批。

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
            task_tuple = self.redis_db_frame.blpop(keys=self.publisher_of_same_queue.queue_list, timeout=60)  # 监听了多个键名，所以间接实现了优先级，和kombu的redis 支持优先级的设计思路不谋而合。
            if task_tuple:
                msg = task_tuple[1]
                self.redis_db_frame.zadd(self._unack_zset_name, {msg: time.time()})
                # self.logger.debug(task_tuple)
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {task_str_list}  ')
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
                        task_tuple = p.blpop(keys=self.publisher_of_same_queue.queue_list, timeout=60)  # 监听了多个键名，所以间接实现了优先级，和kombu的redis 支持优先级的设计思路不谋而合。
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
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {task_str_list}  ')
                kw = {'body': msg, 'task_str': msg}
                self._submit_task(kw)

    def _requeue(self, kw):
        self.publisher_of_same_queue.publish(kw['body'])
