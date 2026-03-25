# -*- coding: utf-8 -*-
"""
Performance optimization test script

Test the publish and consume performance of the optimized funboost memory queue
"""
import time
import threading
from queue import Queue

# Test the performance of the optimized get_func_only_params function
def test_delete_keys_performance():
    """Test optimization effect of get_func_only_params"""
    from funboost.core.helper_funs import get_func_only_params

    # Simulate message dict
    test_msg = {
        'a': 1,
        'b': 2,
        'c': {'nested': 'value'},
        'extra': {
            'task_id': 'test_task_123',
            'publish_time': 1234567890.1234,
            'publish_time_format': '2025-01-19 12:00:00'
        }
    }

    # Performance test
    iterations = 100000
    start = time.perf_counter()
    for _ in range(iterations):
        result = get_func_only_params(test_msg)
    end = time.perf_counter()

    elapsed = end - start
    ops_per_sec = iterations / elapsed
    print(f"get_func_only_params performance test:")
    print(f"  - {iterations} operations took: {elapsed:.4f} seconds")
    print(f"  - Operations per second: {ops_per_sec:,.0f} ops/sec")
    print(f"  - Result correctness: {'a' in result and 'extra' not in result}")
    print()


def test_function_result_status_performance():
    """Test optimization effect of FunctionResultStatus initialization"""
    from funboost.core.function_result_status_saver import FunctionResultStatus

    test_msg = {
        'a': 1,
        'b': 2,
        'extra': {
            'task_id': 'test_task_123',
            'publish_time': 1234567890.1234,
            'publish_time_format': '2025-01-19 12:00:00'
        }
    }

    iterations = 50000
    start = time.perf_counter()
    for _ in range(iterations):
        status = FunctionResultStatus('test_queue', 'test_func', test_msg)
    end = time.perf_counter()

    elapsed = end - start
    ops_per_sec = iterations / elapsed
    print(f"FunctionResultStatus initialization performance test:")
    print(f"  - {iterations} operations took: {elapsed:.4f} seconds")
    print(f"  - Operations per second: {ops_per_sec:,.0f} ops/sec")
    print()

    # Test lazy attribute
    status = FunctionResultStatus('test_queue', 'test_func', test_msg)
    start = time.perf_counter()
    for _ in range(iterations):
        _ = status.params_str  # Cached after first access
    end = time.perf_counter()
    print(f"  - params_str attribute access (cached): {(end - start) * 1000:.4f} ms / {iterations} times")
    print()


def test_async_result_performance():
    """Test AsyncResult creation performance (AsyncResult is lazy-loaded by design)"""
    from funboost.core.msg_result_getter import AsyncResult

    iterations = 100000

    # Test AsyncResult creation performance
    start = time.perf_counter()
    for i in range(iterations):
        result = AsyncResult(f'task_{i}', timeout=1800)
    end = time.perf_counter()
    elapsed = end - start

    print(f"AsyncResult creation performance test:")
    print(f"  - {iterations} creations took: {elapsed:.4f} seconds")
    print(f"  - Creations per second: {iterations / elapsed:,.0f} ops/sec")
    print()


def test_serialization_performance():
    """Test serialization performance"""
    from funboost.core.serialization import Serialization

    test_data = {
        'a': 1,
        'b': 'hello',
        'c': [1, 2, 3],
        'd': {'nested': 'value'},
        'extra': {
            'task_id': 'test_123',
            'publish_time': 1234567890.1234,
        }
    }

    iterations = 100000

    # JSON serialization
    start = time.perf_counter()
    for _ in range(iterations):
        json_str = Serialization.to_json_str(test_data)
    end = time.perf_counter()
    serialize_time = end - start

    # JSON deserialization
    start = time.perf_counter()
    for _ in range(iterations):
        data = Serialization.to_dict(json_str)
    end = time.perf_counter()
    deserialize_time = end - start

    print(f"Serialization performance test:")
    print(f"  - to_json_str: {iterations / serialize_time:,.0f} ops/sec")
    print(f"  - to_dict: {iterations / deserialize_time:,.0f} ops/sec")
    print()


def test_memory_queue_end_to_end():
    """Test end-to-end performance of memory queue"""
    from funboost import boost, BoosterParams, BrokerEnum
    import logging

    counter = {'count': 0}
    completed = threading.Event()
    target_count = 10000

    @boost(BoosterParams(
        queue_name='perf_test_queue',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=50,
        log_level=logging.WARNING,  # Reduce log output
    ))
    def test_func(x):
        counter['count'] += 1
        if counter['count'] >= target_count:
            completed.set()
        return x * 2

    # Publish messages first
    print(f"Memory queue end-to-end performance test ({target_count} messages):")

    start = time.perf_counter()
    for i in range(target_count):
        test_func.push(i)
    publish_time = time.perf_counter() - start
    print(f"  - Publishing {target_count} messages took: {publish_time:.4f} seconds")
    print(f"  - Publish rate: {target_count / publish_time:,.0f} msgs/sec")

    # Wait for consumption to complete
    completed.wait(timeout=60)
    total_time = time.perf_counter() - start

    print(f"  - Total processing time: {total_time:.4f} seconds")
    print(f"  - End-to-end throughput: {target_count / total_time:,.0f} msgs/sec")
    print()


if __name__ == '__main__':
    print("=" * 60)
    print("Funboost performance optimization tests")
    print("=" * 60)
    print()

    test_delete_keys_performance()
    test_function_result_status_performance()
    test_async_result_performance()
    test_serialization_performance()

    # Note: End-to-end test requires a complete funboost environment
    # test_memory_queue_end_to_end()

    print("=" * 60)
    print("Tests complete!")
    print("=" * 60)
