# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57
import time
import socket
from funboost import boost, BrokerEnum, ConcurrentModeEnum, fabric_deploy

import os


def get_host_ip():
    ip = ''
    host_name = ''
    # noinspection PyBroadException
    try:
        sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sc.connect(('8.8.8.8', 80))
        ip = sc.getsockname()[0]
        host_name = socket.gethostname()
        sc.close()
    except Exception:
        pass
    return ip, host_name


computer_ip, computer_name = get_host_ip()


# Set broker_kind to switch middleware to mq or redis and 20+ other middleware/packages with one line.
# Set concurrent_mode to choose concurrency mode; changing this one parameter automatically supports threading/eventlet/gevent/asyncio concurrency.
# Set qps to precisely specify how many times per second the function runs, regardless of how long the function takes.
# Set concurrent_num to set concurrency size. In this example, with a thread pool of 300, qps=6, and function taking 5 seconds,
#    the smart thread pool automatically opens only 30 threads, avoiding too many threads degrading performance.
#    The smart thread pool can automatically expand and shrink thread count. If the function takes longer, it increases threads to meet qps;
#    if the function takes less time, it reduces threads. The framework doesn't need to know the exact function duration in advance.
# There are 30+ other function execution control parameters; see the function parameter descriptions in the code.

# @boost('queue_test2', )  # @task_deco only requires one parameter.
@boost('queue_test30', qps=0.2, broker_kind=BrokerEnum.REDIS)
def f2(a, b):
    sleep_time = 7
    result = a + b
    # print(f'Machine: {get_host_ip()} Process: {os.getpid()}, consuming message {a} + {b}..., will take {sleep_time} seconds')
    time.sleep(sleep_time)  # Simulate blocking for n seconds; must use concurrency to bypass this.
    print(f'Machine: {get_host_ip()} Process: {os.getpid()}, result of {a} + {b} is {result}')
    return result


@boost('queue_test31', qps=0.2, broker_kind=BrokerEnum.REDIS)
def f3(a, b):
    print(f'Machine: {get_host_ip()} Process: {os.getpid()}, result of {a} - {b} is {a - b}')
    return a - b


if __name__ == '__main__':
    print(f2.__name__)
    # f2.clear()
    for i in range(20):
        # f2.push(i, i * 2)
        f3.push(i, i * 2)
    # f2.consume()
    # f3.multi_process_consume(2)
    # # 192.168.114.135  192.168.6.133
    # f2.fabric_deploy('192.168.6.133', 22, 'ydf', '372148', process_num=2)
    f3.fabric_deploy('106.55.244.xx', 22, 'root', 'xxxxx',
                     only_upload_within_the_last_modify_time=1 * 24 * 60 * 60,
                     file_volume_limit=100 * 1000, process_num=2)
