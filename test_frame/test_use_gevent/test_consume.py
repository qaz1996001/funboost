# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57
import multiprocessing

import gevent.monkey;gevent.monkey.patch_all()  # Monkey patching is required.
# import eventlet;eventlet.monkey_patch(all=True)
import time
from funboost import ConcurrentModeEnum, BoosterParams,run_forever


@BoosterParams(queue_name='queue_test62', concurrent_num=200, log_level=10, logger_prefix='zz platform consumer',
               function_timeout=20, is_print_detail_exception=True,
               msg_expire_seconds=500, concurrent_mode=ConcurrentModeEnum.GEVENT)
def f2(a, b):
    print(f'Consuming message {a} + {b} ...')
    time.sleep(10)  # Simulate blocking for 10 seconds doing something; concurrency must be used to work around this block.
    print(f'Result of {a} + {b} is  {a + b}')


@BoosterParams(queue_name='queue_test63', concurrent_num=200, log_level=10, logger_prefix='zz platform consumer',
               function_timeout=20, is_print_detail_exception=True,
               msg_expire_seconds=500, concurrent_mode=ConcurrentModeEnum.GEVENT)
def f3(a, b):
    print(f'Consuming message {a} + {b} ...')
    time.sleep(10)  # Simulate blocking for 10 seconds doing something; concurrency must be used to work around this block.
    print(f'Result of {a} + {b} is  {a + b}')


def start_many_fun_consume():
    f2.consume()
    f3.consume()
    run_forever()

if __name__ == '__main__':
    for i in range(100):
        f2.push(1 * i, 2 * i)
        f3.push(1 * i, 2 * i)
    # f2.consume()
    # f3.consume()
    for i in range(6):
        multiprocessing.Process(target=start_many_fun_consume).start()
