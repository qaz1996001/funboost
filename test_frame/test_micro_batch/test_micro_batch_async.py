# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/18
"""
Micro batch consumer asyncio test

Validates the behavior of MicroBatchConsumerMixin in ASYNC mode
"""
import asyncio
import time
from funboost import boost, BrokerEnum, BoosterParams, ConcurrentModeEnum
from funboost.contrib.override_publisher_consumer_cls.funboost_micro_batch_mixin import (
    MicroBatchConsumerMixin,
)

# Record batch processing results
batch_results = []

@boost(BoosterParams(
    queue_name='test_micro_batch_async_queue',
    broker_kind=BrokerEnum.REDIS,
    concurrent_mode=ConcurrentModeEnum.ASYNC,  # Enable async mode
    consumer_override_cls=MicroBatchConsumerMixin,
    user_options={
        'micro_batch_size': 10,
        'micro_batch_timeout': 3.0,
    },
    qps=100,
    should_check_publish_func_params=False,
))
async def batch_async_task(items: list):
    """
    Simulated async batch processing task
    """
    # Simulate async I/O operation
    await asyncio.sleep(0.1)

    print(f"[Async] Batch processing {len(items)} messages: {items}")
    return len(items)


def test_async_batch():
    """Test async batch functionality"""
    print("=" * 60)
    print("Test: Asyncio batch functionality")
    print("Publishing 25 messages, verifying execution via _async_run_batch")
    print("=" * 60)

    # Publish 25 messages
    for i in range(25):
        batch_async_task.push(x=i, y=i * 2)

    # Start consuming
    batch_async_task.consume()


if __name__ == '__main__':
    test_async_batch()
