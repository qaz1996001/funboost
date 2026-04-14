# -*- coding: utf-8 -*-
# @Author  : AI Assistan
"""
Micro batch consumer test

Tests for MicroBatchConsumerMixin functionality:
1. Basic functionality test: publish messages and verify batch processing
2. Timeout trigger test: trigger when batch_size is not reached within timeout

For example, you can batch insert 100 items into a database for better performance in table sync scenarios.
"""
from funboost import boost, BrokerEnum,ctrl_c_recv
from funboost.contrib.override_publisher_consumer_cls.funboost_micro_batch_mixin import (
    MicroBatchConsumerMixin,MicroBatchBoosterParams
)


@boost(MicroBatchBoosterParams(
    queue_name='test_micro_batch_queue',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    user_options={
        'micro_batch_size': 10,        # Force trigger user function every 10 items per batch
        'micro_batch_timeout': 3.0,    # If fewer than n items, force trigger after 3 seconds timeout
    },
))
def batch_insert_task(items: list):
    """
    Simulated batch insert task

    :param items: List of messages, each element is a dict (function parameters)

    items is like [{'x': 10, 'y': 20}, {'x': 11, 'y': 22}, {'x': 12, 'y': 24}, ...]
    """
    print(f"Batch processing {len(items)} messages: {items}")
    return len(items)


if __name__ == '__main__':
    # Run basic test
    # Start consuming
    batch_insert_task.consume()  # Consumption automatically does micro-batch operation

    print("Publishing 25 messages, batch_size=10, expected: 2 full batches + 1 timeout batch")
    print("=" * 60)

    # Publish 25 messages; the reason for 25 is to trigger micro_batch_timeout for messages 21-25
    for i in range(25):
        batch_insert_task.push(x=i, y=i * 2)  # Publishing is still per single message; consumption does the micro-batch automatically
        print(f"Published message: x={i}, y={i * 2}")
    ctrl_c_recv()
