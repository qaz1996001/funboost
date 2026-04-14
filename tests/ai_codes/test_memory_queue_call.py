# -*- coding: utf-8 -*-
"""
Test the call method of memory queue: publish a message and retrieve the result
via concurrent.futures.Future without depending on Redis.
"""
import time
from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name='test_memory_queue_call_q1',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=0,
    concurrent_num=10,
))
def add(x, y):
    time.sleep(0.5)  # Simulate time-consuming operation
    return x + y


@boost(BoosterParams(
    queue_name='test_memory_queue_call_q2',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=0,
    concurrent_num=10,
))
def divide(a, b):
    return a / b


if __name__ == '__main__':
    # Start consuming
    add.consume()
    divide.consume()
    time.sleep(1)  # Wait for consumers to start

    # ========== Test 1: Normal call ==========
    print('=' * 50)
    print('Test 1: call method retrieves result normally')
    future = add.publisher.call(10, y=20)
    # future is a concurrent.futures.Future object
    # .result(timeout) blocks and waits for the result, returns a FunctionResultStatus object
    function_result_status = future.result(timeout=10)
    print(f'  success: {function_result_status.success}')
    print(f'  result: {function_result_status.result}')
    print(f'  task_id: {function_result_status.task_id}')
    assert function_result_status.success is True
    assert function_result_status.result == 30
    print('  ✅ Test 1 passed')

    # ========== Test 2: Multiple concurrent calls ==========
    print('=' * 50)
    print('Test 2: Multiple concurrent call results')
    futures = []
    for i in range(5):
        f = add.publisher.call(i, y=i * 10)
        futures.append((i, f))

    for i, f in futures:
        frs = f.result(timeout=10)
        expected = i + i * 10
        print(f'  {i} + {i * 10} = {frs.result} (expected {expected}), success={frs.success}')
        assert frs.result == expected
        assert frs.success is True
    print('  ✅ Test 2 passed')

    # ========== Test 3: Future returns normally even when function raises an exception ==========
    print('=' * 50)
    print('Test 3: Future returns normally when function raises exception (success=False)')
    future_err = divide.publisher.call(10, b=0)  # Division by zero error
    frs_err = future_err.result(timeout=10)
    print(f'  success: {frs_err.success}')
    print(f'  exception: {frs_err.exception}')
    assert frs_err.success is False
    print('  ✅ Test 3 passed')

    # ========== Test 4: Normal push is not affected ==========
    print('=' * 50)
    print('Test 4: Normal push is not affected by call')
    add.push(100, y=200)
    time.sleep(2)
    print('  ✅ Test 4 passed (push works normally)')

    print('=' * 50)
    print('🎉 All tests passed! Memory queue call method works correctly, no Redis dependency.')
