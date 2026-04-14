# -*- coding: utf-8 -*-
"""
AWS SQS broker test example

Before using, make sure:
1. Install boto3: pip install boto3
2. Configure AWS credentials (via environment variables, ~/.aws/credentials, or in funboost_config.py)

For local testing you can use LocalStack:
1. Install LocalStack: pip install localstack
2. Start: localstack start
3. Set SQS_ENDPOINT_URL = 'http://localhost:4566' in funboost_config.py
"""

import time
from funboost import boost, BrokerEnum, BoosterParams,ctrl_c_recv


@boost(BoosterParams(
    queue_name='test_sqs_queue',
    broker_kind=BrokerEnum.SQS,
    concurrent_num=5,
    log_level=10,
    is_show_message_get_from_broker=True,
    # SQS 专用配置
    broker_exclusive_config={
        'wait_time_seconds': 20,  # long-poll wait time (seconds), max 20
        'max_number_of_messages': 10,  # max number of messages per pull, max 10
        'visibility_timeout': 300,  # visibility timeout (seconds)
    }
))
def process_sqs_task(x, y):
    """Function to process SQS tasks"""
    print(f'Starting task: x={x}, y={y}')
    time.sleep(1)  # Simulate time-consuming operation
    result = x + y
    print(f'Task complete: {x} + {y} = {result}')
    return result


if __name__ == '__main__':
    # Publish tasks
    print("Publishing 10 tasks to SQS...")
    for i in range(10):
        process_sqs_task.push(x=i, y=i * 2)

    print(f"Number of messages in queue: {process_sqs_task.get_message_count()}")

    # Start consuming
    print("Starting task consumption...")
    process_sqs_task.consume()
    ctrl_c_recv()
