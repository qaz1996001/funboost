# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57

from auto_run_on_remote import run_current_script_on_remote
# run_current_script_on_remote()

import random

import time

from funboost import boost, BrokerEnum,ExceptionForRequeue


@boost('test_rpc_queue', is_using_rpc_mode=True, broker_kind=BrokerEnum.REDIS_ACK_ABLE, qps=100,max_retry_times=5)
def add(a, b):
    time.sleep(2)
    if random.random() >0.5:
        raise ValueError('Simulating consumer function error, triggering retry')
        # raise ExceptionForRequeue('Simulating possible consumer function error; raising ExceptionForRequeue will immediately requeue the message')
    return a + b


if __name__ == '__main__':
    add.consume()

