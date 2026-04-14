# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57
import time
import random
from funboost import boost, LogManager,BrokerEnum




@boost('queue_test2', qps=30, broker_kind=BrokerEnum.REDIS, function_result_status_persistance_conf=)  # By setting broker_kind, you can switch middleware to mq, redis, or 13 other middlewares/packages with one click.
def f2(a, b):
    print(f'Consuming message {a} + {b}.....')
    time.sleep(random.randint(1,1000)/100.0)  # Simulate randomly consuming time doing something; precise frequency control
    print(f'Result of computing {a} + {b} is  {a + b}')


if __name__ == '__main__':
    f2.clear()
    for i in range(200000):
        f2.push(i, i * 2)
    print(f2.publisher.get_message_count())
    f2.consume()