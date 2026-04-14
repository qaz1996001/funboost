# -*- coding: utf-8 -*-
"""
Test basic functionality of the librabbitmq broker

Notes:
1. Need to install librabbitmq first: pip install librabbitmq
2. librabbitmq primarily supports Linux; building and installing on Windows may have issues
3. Ensure RabbitMQ service is running
"""
from auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote()
from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name='test_librabbitmq_queue',
    broker_kind=BrokerEnum.RABBITMQ_LIBRABBITMQ,
    concurrent_num=10,
    qps=5,
))
def test_librabbitmq_task(x, y):
    """Test task function"""
    print(f'{x} + {y} = {x + y}')
    return x + y


if __name__ == '__main__':
    # Publish 5 test tasks
    for i in range(5):
        test_librabbitmq_task.push(i, i * 2)

    print("Published 5 tasks to the test_librabbitmq_queue queue")

    # Start consuming
    test_librabbitmq_task.consume()
