# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/12/18 0018 10:06
"""
This is the most minimal "beggar version" of a Redis-based distributed function execution implementation.
Compared to the full version, all features are stripped away to demonstrate the most essential and minimal implementation of the framework.
The main purpose is to greatly simplify the code by removing many features, demonstrating the core idea of how to execute
Python functions in a distributed manner. This is only for simplified demonstration - do not use it in production as it is too limited.

The full version supports 3 concurrency types; the beggar version only supports multi-threaded concurrency.
The full version's thread pool has a bounded queue with dynamically scaling thread sizes;
the beggar version's thread pool can only increase threads and cannot proactively shrink.

The full version supports 15 types of function auxiliary controls, including rate limiting, timeout killing,
consumption acknowledgment, and 15 other features. The beggar version does not support any of these for code simplicity.

The full version supports 10 types of message queue middleware; here we only demonstrate Redis as middleware since it's popular.
"""
import json
import redis
from concurrent.futures import ThreadPoolExecutor
from funboost.funboost_config_deafult import BrokerConnConfig

redis_db_frame = redis.Redis(host=BrokerConnConfig.REDIS_HOST, password=BrokerConnConfig.REDIS_PASSWORD,
                             port=BrokerConnConfig.REDIS_PORT, db=BrokerConnConfig.REDIS_DB,
                             ssl=BrokerConnConfig.REDIS_USE_SSL,
                             decode_responses=True)


class BeggarRedisConsumer:
    """Maintains a code structure similar to the full version. For a simplified version like this, a single function implementation would also suffice. See the function below."""

    def __init__(self, queue_name, consume_function, threads_num):
        self.pool = ThreadPoolExecutor(threads_num)  # It's better to use BoundedThreadPoolExecutor or CustomThreadPoolExecutor. An unbounded queue will rapidly consume all Redis messages.
        self.consume_function = consume_function
        self.queue_name = queue_name

    def start_consuming_message(self):
        while True:
            try:
                redis_task = redis_db_frame.blpop(self.queue_name, timeout=60)
                if redis_task:
                    task_str = redis_task[1]
                    print(f'Message retrieved from Redis queue [{self.queue_name}]: {task_str}  ')
                    task_dict = json.loads(task_str)
                    self.pool.submit(self.consume_function, **task_dict)
                else:
                    print(f'No tasks in Redis queue {self.queue_name}')
            except redis.RedisError as e:
                print(e)


def start_consuming_message(queue_name, consume_function, threads_num=50):
    """
    The functionality and middleware in this example are too simple, so a single function is best.
    If you can't understand the class-based code, ignore the class above and just look at this function -
    it implements the beggar version distributed function execution framework in about 10 lines of code.
    """
    pool = ThreadPoolExecutor(threads_num)
    while True:
        try:
            redis_task = redis_db_frame.brpop(queue_name, timeout=60)
            if redis_task:
                task_str = redis_task[1]
                # print(f'Message retrieved from Redis queue {queue_name}: {task_str}')
                pool.submit(consume_function, **json.loads(task_str))
            else:
                print(f'No tasks in Redis queue {queue_name}')
        except redis.RedisError as e:
            print(e)


if __name__ == '__main__':
    import time


    def add(x, y):
        time.sleep(5)
        print(f'The result of {x} + {y} is {x + y}')


    # Push tasks
    for i in range(100):
        print(i)
        redis_db_frame.lpush('test_beggar_redis_consumer_queue', json.dumps(dict(x=i, y=i * 2)))

    # Consume tasks
    # consumer = BeggarRedisConsumer('test_beggar_redis_consumer_queue', consume_function=add, threads_num=100)
    # consumer.start_consuming_message()

    start_consuming_message('test_beggar_redis_consumer_queue', consume_function=add, threads_num=10)
