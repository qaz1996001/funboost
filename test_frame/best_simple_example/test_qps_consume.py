# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57
import time
import threading
from funboost import boost, BrokerEnum,ConcurrentModeEnum

t_start = time.time()

@boost('queue_test2_qps', qps=2, broker_kind=BrokerEnum.REDIS, concurrent_mode=ConcurrentModeEnum.THREADING, )
def f2(a, b):
    """
    concurrent_num = 600 is fine because this is a smart thread pool. If the function is fast, it won't actually open that many threads.
    This example tests dynamic function execution time, making it impossible to predict via fixed parameter pre-estimation. Let's see if stable qps and auto thread pool scaling can be achieved.
    Note that the printed thread count also includes a few other threads started by the framework, so the number is not exactly the same as the calculated required threads.

    ## Search for the keyword "new thread started" in the console to see when it's appropriate to expand the thread count.
    ## Search for the keyword "thread stopped" in the console to see when it's appropriate to shrink the thread count.
    """
    result = a + b
    sleep_time = 0.01
    if time.time() - t_start > 60:  # First test with slowly increasing function execution time to see if the framework can auto-scale threads as needed
        sleep_time = 7
    if time.time() - t_start > 120:
        sleep_time = 31
    if time.time() - t_start > 200:
        sleep_time = 79
    if time.time() - t_start > 400: # Finally reduce function execution time again to see if the framework can automatically shrink the thread count.
        sleep_time = 0.8
    if time.time() - t_start > 500:
        sleep_time = None
    print(f'{time.strftime("%H:%M:%S")}  , current thread count is {threading.active_count()},   result of {a} + {b} is {result}, sleep {sleep_time} seconds')
    if sleep_time is not None:
        time.sleep(sleep_time)  # Simulate blocking for n seconds doing something; must use concurrency to bypass this blocking.
    return result

if __name__ == '__main__':
    f2.clear()
    for i in range(1400):
        f2.push(i, i * 2)
    f2.consume()