# -*- coding: utf-8 -*-
"""
Test DuckDB as message queue middleware

DuckDB is an embedded OLAP database with the following features:
1. No need to deploy external services
2. Supports file persistence and in-memory mode
3. High-performance SQL queries
4. Very suitable for single-machine scenarios
"""
import time
import os
from pathlib import Path

# Import DuckDB broker (this automatically registers BROKER_KIND_DUCKDB)
from duckdb_broker import BROKER_KIND_DUCKDB
from funboost import boost, BoosterParams


# Using file storage mode
@boost(BoosterParams(
    queue_name='test_duckdb_file_queue',
    broker_kind=BROKER_KIND_DUCKDB,
    qps=10,
    concurrent_num=5,
    broker_exclusive_config={
        'db_path': Path(__file__).parent / 'test_duckdb_queue.db',  # File storage, messages are persistent
        'poll_interval': 0.5,
    }
))
def add_numbers(x, y):
    """Test function: addition"""
    result = x + y
    print(f"[File mode] {x} + {y} = {result}")
    time.sleep(0.2)
    return result


# Using in-memory mode (faster, but messages are lost on restart)
@boost(BoosterParams(
    queue_name='test_duckdb_memory_queue',
    broker_kind=BROKER_KIND_DUCKDB,
    qps=20,
    concurrent_num=10,
    broker_exclusive_config={
        'db_path': ':memory:',  # In-memory mode
        'poll_interval': 0.1,
    }
))
def multiply_numbers(a, b):
    """Test function: multiplication"""
    result = a * b
    print(f"[Memory mode] {a} * {b} = {result}")
    time.sleep(0.1)
    return result


def test_publish():
    """Test publishing messages"""
    print("=" * 50)
    print("Testing publishing messages to DuckDB queue")
    print("=" * 50)

    # Clear queues
    add_numbers.clear()
    multiply_numbers.clear()

    # Publish messages to file mode queue
    for i in range(10):
        add_numbers.push(i, y=i * 2)

    # Publish messages to in-memory mode queue
    for i in range(10):
        multiply_numbers.push(i, b=i + 1)

    print(f"File mode queue message count: {add_numbers.publisher.get_message_count()}")
    print(f"Memory mode queue message count: {multiply_numbers.publisher.get_message_count()}")

    print("\nPublishing complete!")


def test_consume_file_mode():
    """Test file mode consumption"""
    print("=" * 50)
    print("Testing file mode consumption")
    print("=" * 50)

    # Publish some messages
    add_numbers.clear()
    for i in range(20):
        add_numbers.push(i, y=i * 3)

    print(f"Published 20 messages, queue count: {add_numbers.publisher.get_message_count()}")

    # Start consuming
    add_numbers.consume()


def test_consume_memory_mode():
    """Test in-memory mode consumption"""
    print("=" * 50)
    print("Testing in-memory mode consumption")
    print("=" * 50)

    # Publish some messages
    multiply_numbers.clear()
    for i in range(30):
        multiply_numbers.push(i, b=i + 5)

    print(f"Published 30 messages, queue count: {multiply_numbers.publisher.get_message_count()}")

    # Start consuming
    multiply_numbers.consume()


if __name__ == '__main__':
    import sys

    print("""
    DuckDB Broker Test Program
    ==========================

    Usage:
        python test_duckdb_broker.py publish     # Test publishing messages
        python test_duckdb_broker.py file        # Test file mode consumption
        python test_duckdb_broker.py memory      # Test in-memory mode consumption
        python test_duckdb_broker.py             # Publish and consume (file mode)
    """)

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'publish':
            test_publish()
        elif cmd == 'file':
            test_consume_file_mode()
        elif cmd == 'memory':
            test_consume_memory_mode()
        else:
            print(f"Unknown command: {cmd}")
    else:
        # Default: publish and consume
        test_publish()
        print("\nStarting consumption...")
        test_consume_file_mode()
