# -*- coding: utf-8 -*-
"""
Test token bucket rate limiting (TokenBucketRateLimitConsumerMixin)

Compare the difference between Funboost's native qps rate limiting and
Celery-style token bucket rate limiting.

Usage:
    python test_token_bucket_rate_limit.py

Expected behavior:
1. task_token_bucket: The first few tasks execute in a "burst" (instantaneously),
   then the rate settles to a steady pace.
2. task_native_qps: Always executes at a uniform rate.

Observe the timestamps in the logs to clearly see the difference between the two rate limiting methods.
"""

import time
import datetime
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv
from funboost.contrib.override_publisher_consumer_cls.token_bucket_rate_limit_mixin import (
    TokenBucketRateLimitConsumerMixin,
    TokenBucketBoosterParams,
)


# Scenario 1: Token bucket rate limiting (Celery style)
# rate_limit='6/m' = 6 times per minute = once every 10 seconds
# burst_size=3 = up to 3 tasks can burst
@boost(BoosterParams(
    queue_name='test_token_bucket_queue',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    consumer_override_cls=TokenBucketRateLimitConsumerMixin,
    user_options={
        'rate_limit': '6/m',  # 6 times per minute
        'burst_size': 1,      # Burst capacity of 3
    },
    qps=1,  # Disable native qps rate limiting
))
def task_token_bucket(x):
    print(f'[Token Bucket] Executing task x={x}, time: {datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]}')


# Scenario 2: Funboost native qps rate limiting (uniform)
# qps = 6/60 = 0.1 = once every 10 seconds
@boost(BoosterParams(
    queue_name='test_native_qps_queue',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=0.1,  # Once every 10 seconds
))
def task_native_qps(x):
    print(f'[Native QPS] Executing task x={x}, time: {datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]}')


if __name__ == '__main__':
    print("=" * 60)
    print("Token Bucket Rate Limiting vs Native QPS Rate Limiting Comparison Test")
    print("=" * 60)
    print()
    print("Configuration:")
    print("  - Token Bucket: rate_limit='6/m' (6 times per minute), burst_size=3 (burst 3)")
    print("  - Native QPS: qps=0.1 (once every 10 seconds)")
    print()
    print("Expected behavior:")
    print("  Token Bucket: first 3 tasks execute instantly (burst), then once every 10 seconds")
    print("  Native QPS: once every 10 seconds from start to finish (uniform rate)")
    print()
    print("=" * 60)
    print()

    # Publish tasks
    for i in range(10):
        task_token_bucket.push(i)
        task_native_qps.push(i)

    print(f"Published 10 tasks to each queue, starting consumption... (time: {datetime.datetime.now().strftime('%H:%M:%S')})")
    print()

    # Start consuming
    task_token_bucket.consume()
    # task_native_qps.consume()

    ctrl_c_recv()
