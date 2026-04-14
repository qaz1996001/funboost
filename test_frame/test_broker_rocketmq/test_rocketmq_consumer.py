# -*- coding: utf-8 -*-
"""
RocketMQ 5.x SimpleConsumer test.

Usage:
1. First ensure the RocketMQ 5.x server is started.
   Default gRPC endpoint address is 127.0.0.1:8081.

2. Run the publisher to publish messages first:
   python test_rocketmq_publisher.py

3. Then run the consumer:
   python test_rocketmq_consumer.py

Install dependencies:
    pip install rocketmq-python-client

Features:
    - SimpleConsumer mode: supports out-of-order ACK for individual messages, does not depend on offset
    - Based on gRPC protocol, pure Python implementation
    - Supports Windows / Linux / macOS
"""
from auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote()
import time
from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name='test_rocketmq_5x_queue',
    broker_kind=BrokerEnum.ROCKETMQ,
    concurrent_num=5,
    log_level=10,  # DEBUG
    is_show_message_get_from_broker=True,
    # RocketMQ 5.x exclusive config
    broker_exclusive_config={
        'endpoints': '127.0.0.1:8081',  # RocketMQ 5.x gRPC endpoint
        'consumer_group': 'funboost_test_group',
        # 'access_key': 'your_access_key',  # Required for Alibaba Cloud etc. with AK/SK
        # 'secret_key': 'your_secret_key',
        # 'namespace': 'your_namespace',  # Optional
        'invisible_duration': 15,  # Message invisibility duration (seconds)
        'max_message_num': 32,  # Maximum number of messages to pull at a time
        'tag': '*',  # Message filter tag; '*' means no filtering
    }
))
def test_rocketmq_task(x, y):
    """Test RocketMQ consumer function"""
    result = x + y
    print(f'Calculation result: {x} + {y} = {result}')
    time.sleep(0.5)  # Simulate time-consuming operation
    return result


if __name__ == '__main__':
    # Start consumer
    print('Starting RocketMQ 5.x SimpleConsumer...')
    print('Feature: supports out-of-order ACK for individual messages, does not depend on offset')
    print('Press Ctrl+C to stop')
    test_rocketmq_task.consume()
