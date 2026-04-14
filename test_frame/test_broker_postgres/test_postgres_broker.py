# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/18
"""
PostgreSQL native message queue Broker test.

Unique advantages of PostgreSQL over MySQL:
1. FOR UPDATE SKIP LOCKED - High-concurrency lock-free competition, multiple consumers do not block each other
2. LISTEN/NOTIFY - Native publish-subscribe mechanism, real-time push without polling
3. RETURNING - Returns data directly after insert/update, reducing queries
4. Stronger transaction isolation and concurrency control

Before using, make sure:
1. Install psycopg2: pip install psycopg2-binary
2. Configure POSTGRES_DSN in funboost_config.py
"""
import time

from funboost import boost, BrokerEnum, BoosterParams

print('Clickable jump')

@boost(BoosterParams(
    queue_name='test_postgres_broker',
    broker_kind=BrokerEnum.POSTGRES,
    qps=50,  # 50 times per second
    broker_exclusive_config={
        'use_listen_notify': True,  # Use LISTEN/NOTIFY for real-time push
        'poll_interval': 30,  # Polling timeout
        'timeout_minutes': 10,  # Timed-out tasks automatically requeued
    }
))
def my_postgres_task(x, y):
    """PostgreSQL message queue test task"""
    time.sleep(2)
    result = x + y
    print(f"PostgreSQL Task: {x} + {y} = {result}")
    return result


@boost(BoosterParams(
    queue_name='test_postgres_priority',
    broker_kind=BrokerEnum.POSTGRES,
    qps=20,
    # Test priority feature
))
def priority_task(value, priority_level):
    """Priority task test"""
    print(f"Priority Task: value={value}, priority={priority_level}")
    return {'value': value, 'priority': priority_level}


def test_basic_publish_consume():
    """Test basic publish and consume"""
    print("=" * 50)
    print("Test PostgreSQL Broker basic functionality")
    print("=" * 50)

    # Publish messages
    for i in range(10):
        my_postgres_task.push(i, i * 2)
        print(f"Published: x={i}, y={i * 2}")

    # Start consuming
    my_postgres_task.consume()


def test_priority():
    """Test priority feature"""
    print("=" * 50)
    print("Test PostgreSQL Broker priority feature")
    print("=" * 50)

    # Publish messages with different priorities
    for i in range(10):
        # Use task_options to set priority
        from funboost import TaskOptions
        priority = i % 3  # 3 priority levels: 0, 1, 2
        priority_task.publish(
            {'value': i, 'priority_level': priority},
            task_options=TaskOptions(other_extra_params={'priority': priority})
        )
        print(f"Published priority task: value={i}, priority={priority}")

    # Start consuming (higher priority messages will be consumed first)
    priority_task.consume()


def test_concurrent_consumers():
    """Test multi-consumer concurrency (FOR UPDATE SKIP LOCKED feature)"""
    print("=" * 50)
    print("Test PostgreSQL Broker multi-consumer concurrency")
    print("=" * 50)
    print("Using FOR UPDATE SKIP LOCKED, multiple consumers can acquire tasks concurrently without locking")

    # Publish a large number of messages
    for i in range(100):
        my_postgres_task.push(i, i * 2)

    # Multi-process consumption
    my_postgres_task.multi_process_consume(4)


if __name__ == '__main__':
    # Run the basic test demo directly
    # test_basic_publish_consume()

    # To test other features, uncomment the corresponding line:
    # test_priority()           # Test priority feature
    test_concurrent_consumers()  # Test multi-consumer concurrency
