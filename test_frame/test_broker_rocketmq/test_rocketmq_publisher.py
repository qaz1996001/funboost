# -*- coding: utf-8 -*-
"""
RocketMQ 5.x publisher test.

Usage:
1. First ensure the RocketMQ 5.x server is started.
   Default gRPC endpoint address is 127.0.0.1:8081.

2. Run this script to publish messages:
   python test_rocketmq_publisher.py

Install dependencies:
    pip install rocketmq-python-client

Features:
    - Based on gRPC protocol, pure Python implementation
    - Supports Windows / Linux / macOS
"""

# Import the function defined in the consumer
from test_rocketmq_consumer import test_rocketmq_task


if __name__ == '__main__':
    print('Starting to publish messages to RocketMQ 5.x...')

    # Publish 20 test messages
    for i in range(20):
        # Use push method to publish messages (shorthand)
        test_rocketmq_task.push(i, i * 2)
        print(f'Published message: x={i}, y={i * 2}')

    print('Message publishing complete!')
    print('You can now run test_rocketmq_consumer.py to consume the messages')
