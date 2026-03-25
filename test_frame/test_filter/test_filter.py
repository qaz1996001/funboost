


# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57
import threading

import time
from funboost import BoosterParams, BrokerEnum,ctrl_c_recv,TaskOptions,ConcurrentModeEnum


# Set broker_kind to switch middleware to mq or redis and 20+ other middleware/packages with one line.
# Set concurrent_mode to choose concurrency mode; changing this one parameter automatically supports threading/eventlet/gevent/asyncio concurrency.
# Set qps to precisely specify how many times per second the function runs, regardless of how long the function takes.
# Set concurrent_num to set concurrency size. In this example, with a thread pool of 300, qps=6, and function taking 5 seconds,
#    the smart thread pool automatically opens only 30 threads, avoiding too many threads degrading performance.
#    The smart thread pool can automatically expand and shrink thread count. If the function takes longer, it increases threads to meet qps;
#    if the function takes less time, it reduces threads. The framework doesn't need to know the exact function duration in advance.
# There are 30+ other function execution control parameters; see the function parameter descriptions in the code.

# @boost('queue_test2', )  # @task_deco only requires one parameter.

@BoosterParams(queue_name='queue_test2', qps=6, broker_kind=BrokerEnum.REDIS,
               do_task_filtering=True, # Whether to enable task input parameter filtering
               task_filtering_expire_seconds=3600, # Task input filter expiry time, e.g., if Shenzhen weather is queried within 1 hour, a repeated query within 1 hour will be filtered since it was already queried; a query after 1 hour will not be filtered.
               concurrent_num=1)
def f2(a, b):
    sleep_time = 1
    result = a + b
    print(f'Consuming message {a} + {b}..., will take {sleep_time} seconds')
    time.sleep(sleep_time)  # Simulate blocking for n seconds; must use concurrency to bypass this.
    print(f'Result of {a} + {b} is {result}')
    return result


@BoosterParams(queue_name='queue_test3', qps=6, broker_kind=BrokerEnum.REDIS,do_task_filtering=True,
               concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD)
def f3(a, b):
    sleep_time = 1
    result = a + b
    print(f'Consuming message {a} + {b}..., will take {sleep_time} seconds')
    time.sleep(sleep_time)  # Simulate blocking for n seconds; must use concurrency to bypass this.
    print(f'Result of {a} + {b} is {result}')
    return result

if __name__ == '__main__':
    pass
    # print(f2.__name__)
    # f2.clear()
    f2.consume()
    f3.consume()
    for i in range(200):
        f2.push(i, i * 2)  # Default is to sort all input parameters a and b as JSON and add to filter
        f3.publish(msg={'a':i,'b':i*2},task_options=TaskOptions(filter_str=str(i)))  # This uses only a as the filter condition.
    time.sleep(5)  # funboost adds to filter only after confirming consumption. If a message takes long, concurrency is high, and two identical messages are consecutive, the second one will still execute. So here we demonstrate sleeping briefly.
    for i in range(200):
        f2.push(i, i * 2)
        f3.publish(msg={'a':i,'b':i*2},task_options=TaskOptions(filter_str=str(i)))

    
    ctrl_c_recv()


