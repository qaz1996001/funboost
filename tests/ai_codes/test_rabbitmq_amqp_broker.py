# -*- coding: utf-8 -*-
"""
Test basic functionality of the RABBITMQ_AMQP broker

amqp is the high-efficiency AMQP client used internally by Celery/Kombu,
and requires no additional installation (already installed with celery/kombu)
"""
from auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote()

import time
from funboost import boost, BoosterParams, BrokerEnum,ctrl_c_recv


@boost(BoosterParams(
    queue_name='test_rabbitmq_amqp_queue',
    broker_kind=BrokerEnum.RABBITMQ_AMQP,
    concurrent_num=200,
    # qps=5,
    log_level=20,
    broker_exclusive_config= {'no_ack':True}
))
def test_rabbitmq_amqp_task(x, y):
    """Test task function"""
    # print(f'{x} + {y} = {x + y}')
    if x % 10000 == 0:
        print(f'{x} + {y} = {x + y}')
    return x + y


if __name__ == '__main__':
    # print('hello')

    # Publish 50000 test tasks
    for i in range(50000):
        if i % 10000 == 0:
            print(f'Published {i} tasks to the test_rabbitmq_amqp_queue queue')
        test_rabbitmq_amqp_task.push(i, i * 2)

    # print("Published 5 tasks to the test_rabbitmq_amqp_queue queue")

     # Start consuming
    test_rabbitmq_amqp_task.consume()


    # ctrl_c_recv()


    # time.sleep(1000)

    # test_rabbitmq_amqp_task.push(10, 20)
