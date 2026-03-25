# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57
import threading

import time
from funboost import boost, BrokerEnum, BoosterParams


# By setting broker_kind, you can switch the middleware to mq, redis, or 20 other middlewares/packages with one click.
# By setting concurrent_mode, you set the concurrency mode. Changing this one parameter automatically supports threading, eventlet, gevent, and asyncio concurrency.
# By setting qps, you can precisely specify how many times per second the function runs, regardless of how long the function takes.
# By setting concurrent_num, you set the concurrency size. In this example, the thread pool size is 300, but qps is 6 and the function takes 5 seconds,
#    the framework's smart thread pool will automatically open only 30 threads, avoiding too many threads switching and affecting efficiency.
#    The smart thread pool can automatically expand and shrink the number of threads. For example, if the function is slow for a period, it will increase threads to reach qps; if the function becomes faster, it will automatically reduce threads. The framework doesn't need to know the exact function duration in advance.
# There are 30 other function execution control parameters. See the function parameter descriptions in the code for detailed explanations.


@boost(BoosterParams(queue_name='queue_test2', qps=6, broker_kind=BrokerEnum.REDIS))
def f2(a, b):
    sleep_time = 7
    result = a + b
    print(f'Consuming message {a} + {b}....., this time needs {sleep_time} seconds')
    time.sleep(sleep_time)  # Simulate blocking for n seconds doing something; must use concurrency to bypass this blocking.
    print(f'The result of {a} + {b} is {result}')
    return result


def f3(user,sex,age):
    print(user,sex,age)

if __name__ == '__main__':
    pass
    f2(1,2) # Test calling the function directly
    # print(f2.__name__)
    f2.clear()
    for i in range(200):
        f2.push(i, i * 2)
    f2.consume()

    



