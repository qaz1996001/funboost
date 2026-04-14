# -*- coding: utf-8 -*-
"""
CircuitBreakerConsumerMixin test

Part 1: CircuitBreaker state machine unit tests (local memory, no funboost runtime needed)
  - 1a: consecutive strategy
  - 1b: rate strategy
  - 1c: half_open_ttl timeout
  - 1d: multi-thread concurrency safety
Part 2: Integration tests with funboost MEMORY_QUEUE
  - 2a: blocking mode (consecutive strategy)
  - 2b: Fallback mode (consecutive strategy)
  - 2c: error rate strategy + exceptions filter
"""
import time
import threading

from funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin import (
    CircuitState,
    CircuitBreaker,
    _parse_exception_names,
)


def _elapsed(t0):
    """Return a string showing elapsed seconds since t0"""
    return f'[T+{time.time() - t0:.1f}s]'


# ================================================================
# Part 1a: consecutive 策略
# ================================================================

def test_initial_state():
    cb = CircuitBreaker(strategy='consecutive', failure_threshold=3, recovery_timeout=5, half_open_max_calls=2)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    print('  [PASS] Initial state is CLOSED')


def test_success_resets_failure_count():
    cb = CircuitBreaker(failure_threshold=5)
    cb.record_failure()
    cb.record_failure()
    assert cb.failure_count == 2
    cb.record_success()
    assert cb.failure_count == 0
    assert cb.state == CircuitState.CLOSED
    print('  [PASS] Success resets failure count')


def test_failures_trigger_open():
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    print('  [PASS] Consecutive failures >= threshold triggers OPEN')


def test_open_to_half_open_after_timeout():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    remaining = cb.time_until_half_open()
    assert remaining > 0
    print(f'  Waiting for recovery ({remaining:.1f}s)...')
    time.sleep(1.1)

    assert cb.state == CircuitState.HALF_OPEN
    assert cb.time_until_half_open() == 0.0
    print('  [PASS] OPEN -> HALF_OPEN automatic transition after timeout')


def test_half_open_success_closes():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5, half_open_max_calls=2)
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.6)
    assert cb.state == CircuitState.HALF_OPEN

    cb.record_success()
    assert cb.state == CircuitState.HALF_OPEN
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    print('  [PASS] HALF_OPEN consecutive successes -> CLOSED')


def test_half_open_failure_reopens():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5, half_open_max_calls=3)
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.6)
    assert cb.state == CircuitState.HALF_OPEN

    cb.record_success()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    print('  [PASS] HALF_OPEN failure -> re-OPEN')


# ================================================================
# Part 1b: rate 策略
# ================================================================

def test_rate_strategy_no_open_below_min_calls():
    cb = CircuitBreaker(strategy='rate', errors_rate=0.5, period=10.0, min_calls=5, recovery_timeout=5)
    for _ in range(4):
        cb.record_failure()
    assert cb.state == CircuitState.CLOSED, 'Should not trigger OPEN when calls < min_calls'
    print('  [PASS] rate: does not trigger OPEN when calls < min_calls')


def test_rate_strategy_opens_on_high_error_rate():
    cb = CircuitBreaker(strategy='rate', errors_rate=0.5, period=10.0, min_calls=4, recovery_timeout=5)
    cb.record_success()
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    info = cb.get_error_rate_info()
    print(f'  Current error rate: {info["rate"]:.0%} ({info["failures"]}/{info["total"]})')
    assert cb.state == CircuitState.OPEN, f'Error rate 75% >= 50%, should trigger OPEN, actual {cb.state}'
    print('  [PASS] rate: error rate at threshold triggers OPEN')


def test_rate_strategy_no_open_below_threshold():
    cb = CircuitBreaker(strategy='rate', errors_rate=0.5, period=10.0, min_calls=4, recovery_timeout=5)
    cb.record_success()
    cb.record_success()
    cb.record_success()
    cb.record_failure()
    info = cb.get_error_rate_info()
    print(f'  Current error rate: {info["rate"]:.0%} ({info["failures"]}/{info["total"]})')
    assert cb.state == CircuitState.CLOSED, 'Error rate 25% < 50%, should not trigger OPEN'
    print('  [PASS] rate: error rate below threshold does not trigger OPEN')


def test_rate_strategy_window_expiry():
    cb = CircuitBreaker(strategy='rate', errors_rate=0.5, period=1.0, min_calls=2, recovery_timeout=5)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    cb._state = CircuitState.CLOSED
    cb._failure_count = 0
    cb._call_records.clear()

    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    cb._state = CircuitState.CLOSED
    cb._failure_count = 0

    print('  Waiting for window expiry (1s)...')
    time.sleep(1.1)

    cb.record_failure()
    assert cb.state == CircuitState.CLOSED, 'After old records expire, 1 failure should not reach min_calls=2'
    print('  [PASS] rate: old records no longer counted after sliding window expires')


# ================================================================
# Part 1c: half_open_ttl 超时
# ================================================================

def test_half_open_ttl_timeout():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5, half_open_max_calls=10, half_open_ttl=0.5)
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.6)
    assert cb.state == CircuitState.HALF_OPEN

    cb.record_success()
    print('  Waiting for half_open_ttl timeout (0.5s)...')
    time.sleep(0.6)

    assert cb.state == CircuitState.OPEN, 'Half-open state timeout should return to OPEN'
    print('  [PASS] HALF_OPEN exceeds half_open_ttl -> OPEN')


# ================================================================
# Part 1d: 多线程并发安全 + 异常名解析
# ================================================================

def test_thread_safety():
    cb = CircuitBreaker(failure_threshold=100, recovery_timeout=10)
    errors = []

    def record_many(is_success):
        try:
            for _ in range(500):
                if is_success:
                    cb.record_success()
                else:
                    cb.record_failure()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=record_many, args=(i % 2 == 0,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert cb.state in (CircuitState.CLOSED, CircuitState.OPEN)
    print('  [PASS] Multi-thread concurrency safe')


def test_parse_exception_names():
    assert _parse_exception_names(None) is None
    assert _parse_exception_names((ValueError, TimeoutError)) == {'ValueError', 'TimeoutError'}
    assert _parse_exception_names(('RuntimeError',)) == {'RuntimeError'}
    assert _parse_exception_names((ConnectionError, 'CustomError')) == {'ConnectionError', 'CustomError'}
    print('  [PASS] _parse_exception_names correctly parses exception types')


def run_unit_tests():
    print('=' * 60)
    print('Part 1: CircuitBreaker State Machine Unit Tests')
    print('=' * 60)

    print('--- 1a: consecutive strategy ---')
    test_initial_state()
    test_success_resets_failure_count()
    test_failures_trigger_open()
    test_open_to_half_open_after_timeout()
    test_half_open_success_closes()
    test_half_open_failure_reopens()

    print('--- 1b: rate strategy ---')
    test_rate_strategy_no_open_below_min_calls()
    test_rate_strategy_opens_on_high_error_rate()
    test_rate_strategy_no_open_below_threshold()
    test_rate_strategy_window_expiry()

    print('--- 1c: half_open_ttl ---')
    test_half_open_ttl_timeout()

    print('--- 1d: other ---')
    test_thread_safety()
    test_parse_exception_names()

    print('-' * 60)
    print('Part 1 all passed!')
    print()


# ================================================================
# Part 2: 与 funboost 集成测试
# ================================================================

def run_integration_test_block_mode():
    """
    Blocking mode: consecutive strategy + local counting

    Expected timing (recovery_timeout=2.0s):
      T+0.0  consume() starts
      T+0.3  consumer ready, push 3 messages
      T+0.5  3 messages consumed, 3 consecutive failures -> OPEN
      T+1.3  assert OPEN ok, push(100)
      T+1.3  _submit_task blocks waiting (remaining~1.2s)
      T+2.5  recovery_timeout expires -> HALF_OPEN, task 100 executed (should_fail=False -> success)
      T+4.3  main thread wakes, verify task 100 executed ok
    """
    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin import (
        CircuitBreakerConsumerMixin,
    )

    print('=' * 60)
    print('Part 2a: Integration test - blocking mode (consecutive)')
    print('=' * 60)

    call_log = []
    should_fail = True

    @boost(BoosterParams(
        queue_name='test_cb_block_v3',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        qps=0,
        concurrent_num=1,
        max_retry_times=0,
        consumer_override_cls=CircuitBreakerConsumerMixin,
        user_options={
            'circuit_breaker_options': {
                'strategy': 'consecutive',
                'failure_threshold': 3,
                'recovery_timeout': 2.0,
                'half_open_max_calls': 2,
            },
        },
    ))
    def task_block(x):
        call_log.append(('call', x, time.time()))
        if should_fail:
            raise RuntimeError(f'simulated failure for {x}')
        return x * 10

    task_block.consume()
    time.sleep(0.3)
    t0 = time.time()
    print(f'  {_elapsed(t0)} consumer started')

    for i in range(3):
        task_block.push(i)
    time.sleep(1.0)

    cb = task_block.consumer._circuit_breaker
    print(f'  {_elapsed(t0)} State after 3 failures: {cb.state}, failure_count={cb.failure_count}')
    assert cb.state == CircuitState.OPEN

    should_fail = False
    task_block.push(100)
    print(f'  {_elapsed(t0)} Sent message 100, waiting recovery_timeout=2.0s to recover...')
    time.sleep(3.0)

    success_calls = [log for log in call_log if log[1] == 100]
    if success_calls:
        print(f'  {_elapsed(t0)} Message 100 executed at T+{success_calls[0][2] - t0:.1f}s (expected T+~2.2s, about recovery_timeout=2.0s after OPEN)')
    else:
        print(f'  {_elapsed(t0)} Message 100 was not executed!')
    assert len(success_calls) >= 1
    print(f'  {_elapsed(t0)} [PASS] Blocking mode consecutive test passed')
    print()


def run_integration_test_fallback_mode():
    """
    Fallback mode: consecutive strategy + local counting

    Expected timing (recovery_timeout=2.0s):
      T+0.0  consume() starts
      T+0.3  consumer ready, push 3 messages (all fail)
      T+0.5  OPEN
      T+1.3  assert OPEN ok, push(100), push(101) -> fallback executes immediately
      T+1.5  fallback complete
      T+2.3  assert fallback ok
      T+2.5  recovery_timeout expires -> HALF_OPEN (lazy trigger)
      T+3.8  push(200), state is now HALF_OPEN -> real function executes
      T+4.8  assert task 200 success ok
    """
    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin import (
        CircuitBreakerConsumerMixin,
    )

    print('=' * 60)
    print('Part 2b: Integration test - Fallback mode (consecutive)')
    print('=' * 60)

    call_log = []
    fallback_log = []
    should_fail = True

    def my_fallback(x):
        fallback_log.append(('fallback', x, time.time()))
        return f'fallback_result_{x}'

    @boost(BoosterParams(
        queue_name='test_cb_fallback_v3',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        qps=0,
        concurrent_num=1,
        max_retry_times=0,
        consumer_override_cls=CircuitBreakerConsumerMixin,
        user_options={
            'circuit_breaker_options': {
                'failure_threshold': 3,
                'recovery_timeout': 2.0,
                'half_open_max_calls': 2,
                'fallback': my_fallback,
            },
        },
    ))
    def task_fb(x):
        call_log.append(('call', x, time.time()))
        if should_fail:
            raise RuntimeError(f'simulated failure for {x}')
        return x * 10

    task_fb.consume()
    time.sleep(0.3)
    t0 = time.time()
    print(f'  {_elapsed(t0)} consumer started')

    for i in range(3):
        task_fb.push(i)
    time.sleep(1.0)

    cb = task_fb.consumer._circuit_breaker
    print(f'  {_elapsed(t0)} State after 3 failures: {cb.state}')
    assert cb.state == CircuitState.OPEN

    task_fb.push(100)
    task_fb.push(101)
    time.sleep(1.0)

    print(f'  {_elapsed(t0)} fallback call count: {len(fallback_log)}')
    assert len(fallback_log) >= 2
    for log in fallback_log:
        print(f'    -> T+{log[2] - t0:.1f}s fallback({log[1]})')

    should_fail = False
    print(f'  {_elapsed(t0)} Current state: {cb.state}, remaining until HALF_OPEN {cb.time_until_half_open():.1f}s')
    print(f'  {_elapsed(t0)} Waiting to ensure past recovery_timeout before sending new message...')
    time.sleep(1.5)

    task_fb.push(200)
    time.sleep(1.0)

    success_calls = [log for log in call_log if log[1] == 200]
    if success_calls:
        print(f'  {_elapsed(t0)} Message 200 truly executed at T+{success_calls[0][2] - t0:.1f}s (state should be HALF_OPEN)')
    else:
        print(f'  {_elapsed(t0)} Message 200 was not executed!')
    assert len(success_calls) >= 1
    print(f'  {_elapsed(t0)} [PASS] Fallback mode test passed')
    print()


def run_integration_test_rate_with_exceptions():
    """
    Error rate strategy + exceptions filter

    Expected timing:
      T+0.3  push 3 messages -> RuntimeError (not in exceptions, not tracked)
      T+1.3  assert CLOSED ok
      T+1.3  push 3 messages -> ConnectionError (tracked)
      T+2.3  error rate = 3/3 = 100% >= 50%, min_calls=3 satisfied -> OPEN ok
    """
    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin import (
        CircuitBreakerConsumerMixin,
    )

    print('=' * 60)
    print('Part 2c: Integration test - rate strategy + exceptions filter')
    print('=' * 60)

    call_log = []
    error_type = 'runtime'

    @boost(BoosterParams(
        queue_name='test_cb_rate_exc_v3',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        qps=0,
        concurrent_num=1,
        max_retry_times=0,
        consumer_override_cls=CircuitBreakerConsumerMixin,
        user_options={
            'circuit_breaker_options': {
                'strategy': 'rate',
                'errors_rate': 0.5,
                'period': 30.0,
                'min_calls': 3,
                'recovery_timeout': 2.0,
                'half_open_max_calls': 2,
                'exceptions': (ConnectionError,),
            },
        },
    ))
    def task_rate(x):
        call_log.append(('call', x, time.time()))
        if error_type == 'runtime':
            raise RuntimeError(f'untracked error for {x}')
        elif error_type == 'connection':
            raise ConnectionError(f'tracked error for {x}')
        return x * 10

    task_rate.consume()
    time.sleep(0.3)
    t0 = time.time()
    print(f'  {_elapsed(t0)} consumer started')

    for i in range(3):
        task_rate.push(i)
    time.sleep(1.0)

    cb = task_rate.consumer._circuit_breaker
    print(f'  {_elapsed(t0)} State after 3 RuntimeErrors: {cb.state} (expected CLOSED, because RuntimeError is not tracked)')
    assert cb.state == CircuitState.CLOSED, f'RuntimeError is not tracked and should not trigger OPEN, actual {cb.state}'

    error_type = 'connection'
    for i in range(10, 13):
        task_rate.push(i)
    time.sleep(1.0)

    print(f'  {_elapsed(t0)} State after 3 ConnectionErrors: {cb.state}')
    rate_info = cb.get_error_rate_info()
    print(f'  {_elapsed(t0)} Error rate info: {rate_info}')
    assert cb.state == CircuitState.OPEN, f'ConnectionError is tracked and error rate >= 50%, should trigger OPEN, actual {cb.state}'

    print(f'  {_elapsed(t0)} [PASS] rate strategy + exceptions filter test passed')
    print()


if __name__ == '__main__':
    run_unit_tests()
    run_integration_test_block_mode()
    run_integration_test_fallback_mode()
    run_integration_test_rate_with_exceptions()
    print('=' * 60)
    print('All tests passed!')
    print('=' * 60)
