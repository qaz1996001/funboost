# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2026/3/8
"""
Circuit Breaker Consumer Mixin

Functionality: Automatically trips the circuit breaker when the consuming function fails and reaches
a threshold. During the circuit break period, it either blocks waiting for recovery or executes a fallback function.

=== Three-State State Machine ===

CLOSED (normal) -> trigger condition met -> OPEN (tripped/circuit broken)
OPEN -> after recovery_timeout seconds -> HALF_OPEN (probing)
HALF_OPEN -> consecutive successes >= half_open_max_calls -> CLOSED
HALF_OPEN -> any single failure -> OPEN
HALF_OPEN -> exceeds half_open_ttl -> OPEN (optional)

=== Two Trigger Strategies ===

1. consecutive (consecutive failure count, default):
   Triggers circuit break when consecutive failures >= failure_threshold. Any single success resets the count.

2. rate (error rate sliding window):
   Within a sliding window of `period` seconds, triggers circuit break when call count >= min_calls
   and error rate >= errors_rate.

=== Two Counter Backends ===

1. local (local memory, default):
   Effective within a single process, uses threading.Lock for thread safety.

2. redis (Redis distributed):
   Shared circuit breaker state across multiple processes/machines; all consumers of the same queue share counts.

=== Two Circuit Break Behaviors ===

1. Blocking mode (default, no fallback):
   Blocks _submit_task during circuit break; messages remain in the broker waiting for recovery.

2. Fallback mode (with fallback specified):
   Executes the fallback function instead of the original function during circuit break.

=== user_options['circuit_breaker_options'] Parameter Description ===

All circuit breaker parameters are placed in the 'circuit_breaker_options' dict within user_options,
to avoid key conflicts with other mixins' user_options (e.g. period may conflict with PeriodicQuotaConsumerMixin).

    strategy:               'consecutive' (consecutive failure count) or 'rate' (error rate sliding window), default 'consecutive'
    counter_backend:        'local' (local memory) or 'redis' (Redis distributed), default 'local'

    failure_threshold:      Consecutive failure count threshold (consecutive strategy), default 5
    errors_rate:            Error rate threshold 0.0~1.0 (rate strategy), default 0.5
    period:                 Statistics window in seconds (rate strategy), default 60.0
    min_calls:              Minimum call count in window before evaluation (rate strategy), default 5

    recovery_timeout:       Seconds to wait for recovery after circuit break (equivalent to cashews' ttl), default 60.0
    half_open_max_calls:    Number of consecutive successes needed in half-open state, default 3
    half_open_ttl:          Half-open state timeout in seconds; re-enters OPEN after timeout (None means no timeout), default None

    exceptions:             Tuple of exception types to track (None tracks all), default None
    fallback:               Fallback/degradation function (None means blocking mode), default None

=== Hook Methods (override in subclass) ===

    _on_circuit_open(self,info_dict):   Called when circuit break triggers; can send WeChat/DingTalk/email alerts
    _on_circuit_close(self,info_dict):  Called when circuit break recovers; can send recovery notifications

=== Usage Examples ===

    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin import (
        CircuitBreakerConsumerMixin,
        CircuitBreakerBoosterParams,
    )

    # Method 1: Consecutive failure strategy + local counter (simplest usage)
    @boost(CircuitBreakerBoosterParams(
        queue_name='my_task',
        broker_kind=BrokerEnum.REDIS,
        user_options={
            'circuit_breaker_options': {
                'failure_threshold': 5,
                'recovery_timeout': 60,
            },
        },
    ))
    def my_task(x):
        return call_external_api(x)

    # Method 2: Error rate strategy + Redis distributed counter
    @boost(BoosterParams(
        queue_name='my_task_rate',
        broker_kind=BrokerEnum.REDIS,
        consumer_override_cls=CircuitBreakerConsumerMixin,
        user_options={
            'circuit_breaker_options': {
                'strategy': 'rate',
                'counter_backend': 'redis',
                'errors_rate': 0.5,
                'period': 60,
                'min_calls': 10,
                'recovery_timeout': 30,
                'exceptions': (ConnectionError, TimeoutError),
            },
        },
    ))
    def my_task_rate(x):
        return call_external_api(x)

    # Method 3: Inherit and override hooks to send alerts on circuit break/recovery
    class MyAlertCircuitBreakerMixin(CircuitBreakerConsumerMixin):
        def _on_circuit_open(self, info_dict):
            send_dingtalk(f'[ALERT] Queue {info_dict["queue_name"]} circuit broken! {info_dict["failure_count"]} failures')

        def _on_circuit_close(self, info_dict):
            send_wechat(f'[RECOVERY] Queue {info_dict["queue_name"]} has recovered')

    @boost(BoosterParams(
        queue_name='my_task_alert',
        broker_kind=BrokerEnum.REDIS,
        consumer_override_cls=MyAlertCircuitBreakerMixin,
        user_options={
            'circuit_breaker_options': {
                'failure_threshold': 5,
                'recovery_timeout': 60,
            },
        },
    ))
    def my_task_alert(x):
        return call_external_api(x)

    # Method 4: Fallback degradation
    def my_fallback(x):
        return {'status': 'degraded', 'x': x}

    @boost(BoosterParams(
        queue_name='my_task_fb',
        broker_kind=BrokerEnum.REDIS,
        consumer_override_cls=CircuitBreakerConsumerMixin,
        user_options={
            'circuit_breaker_options': {
                'failure_threshold': 3,
                'recovery_timeout': 30,
                'fallback': my_fallback,
            },
        },
    ))
    def my_task_fb(x):
        return call_external_api(x)
"""

"""
Funboost's circuit breaker implementation reaches the level of top-tier circuit breaker frameworks.
It follows the industry-standard three-state state machine model, supports two trigger strategies,
provides comprehensive configuration options and extension hooks, and additionally supports distributed counting,
making it well-suited for building highly available distributed systems.
The configuration approach is clear and intuitive, allowing developers to use it as easily as Hystrix or resilience4j.
"""

"""
funboost supports both automatic circuit breaker management and manual circuit breaker management.

Manual circuit breaker management:
You manually judge and operate whether to pause and resume consumption.
When you proactively discover large-scale errors or detect them through Prometheus alerts, you can manually pause consumption of a specific queue.
- You can set a pause flag on the Redis queue_name,
- You can also use the FaaS endpoints /funboost/pause_consume and /funboost/resume_consume to pause and resume message pulling
- You can also use the funboost web manager page to set pause and resume

Automatic circuit breaker management:
Through CircuitBreakerConsumerMixin, it intelligently and automatically transitions between the three states: circuit broken, half-open, and recovered.
"""



import asyncio
import collections
import inspect
import threading
import time
import typing
import uuid

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.func_params_model import BoosterParams
from funboost.core.function_result_status_saver import FunctionResultStatus
from funboost.concurrent_pool.async_helper import simple_run_in_executor


class CircuitState:
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'


def _parse_exception_names(exceptions) -> typing.Optional[set]:
    """Convert exception type tuple to a set of exception class name strings. None means track all exceptions"""
    if exceptions is None:
        return None
    names = set()
    for exc in exceptions:
        if isinstance(exc, str):
            names.add(exc)
        elif isinstance(exc, type) and issubclass(exc, BaseException):
            names.add(exc.__name__)
        else:
            names.add(str(exc))
    return names


# ================================================================
# Local Memory Circuit Breaker
# ================================================================

class CircuitBreaker:
    """
    Thread-safe three-state circuit breaker (local memory counter)

    Supports two trigger strategies:
    - consecutive: Trips when consecutive failures >= failure_threshold
    - rate: Trips when error rate >= errors_rate and call count >= min_calls within sliding window

    HALF_OPEN state logic is independent of strategy: consecutive successes >= half_open_max_calls -> CLOSED, any failure -> OPEN.
    """

    def __init__(self,
                 strategy: str = 'consecutive',
                 failure_threshold: int = 5,
                 errors_rate: float = 0.5,
                 period: float = 60.0,
                 min_calls: int = 5,
                 recovery_timeout: float = 60.0,
                 half_open_max_calls: int = 3,
                 half_open_ttl: float = None,
                 ):
        self.strategy = strategy
        self.failure_threshold = failure_threshold
        self.errors_rate = errors_rate
        self.period = period
        self.min_calls = min_calls
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.half_open_ttl = half_open_ttl

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._half_open_success_count = 0
        self._last_open_time = 0.0
        self._last_half_open_time = 0.0
        self._lock = threading.Lock()

        # Sliding window for rate strategy: (timestamp, is_success)
        self._call_records: typing.Deque[typing.Tuple[float, bool]] = collections.deque()

    @property
    def state(self) -> str:
        with self._lock:
            return self._get_state_unlocked()

    def _get_state_unlocked(self) -> str:
        now = time.time()
        if self._state == CircuitState.OPEN:
            if now - self._last_open_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_success_count = 0
                self._last_half_open_time = now
        elif self._state == CircuitState.HALF_OPEN and self.half_open_ttl is not None:
            if now - self._last_half_open_time >= self.half_open_ttl:
                self._state = CircuitState.OPEN
                self._last_open_time = now
        return self._state

    @property
    def failure_count(self) -> int:
        with self._lock:
            return self._failure_count

    def time_until_half_open(self) -> float:
        with self._lock:
            if self._state != CircuitState.OPEN:
                return 0.0
            remaining = self.recovery_timeout - (time.time() - self._last_open_time)
            return max(0.0, remaining)

    def get_error_rate_info(self) -> dict:
        """Get error rate info for the current sliding window (only meaningful for rate strategy)"""
        with self._lock:
            self._cleanup_old_records_unlocked()
            total = len(self._call_records)
            if total == 0:
                return {'total': 0, 'failures': 0, 'rate': 0.0}
            failures = sum(1 for _, success in self._call_records if not success)
            return {'total': total, 'failures': failures, 'rate': failures / total}

    def record_success(self) -> str:
        with self._lock:
            state = self._get_state_unlocked()
            if state == CircuitState.CLOSED:
                if self.strategy == 'consecutive':
                    self._failure_count = 0
                elif self.strategy == 'rate':
                    self._call_records.append((time.time(), True))
                    self._cleanup_old_records_unlocked()
            elif state == CircuitState.HALF_OPEN:
                self._half_open_success_count += 1
                if self._half_open_success_count >= self.half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._half_open_success_count = 0
                    self._call_records.clear()
            return self._state

    def record_failure(self) -> str:
        with self._lock:
            state = self._get_state_unlocked()
            if state == CircuitState.CLOSED:
                if self.strategy == 'consecutive':
                    self._failure_count += 1
                    if self._failure_count >= self.failure_threshold:
                        self._transition_to_open_unlocked()
                elif self.strategy == 'rate':
                    self._call_records.append((time.time(), False))
                    self._cleanup_old_records_unlocked()
                    self._failure_count += 1
                    if self._should_open_by_rate_unlocked():
                        self._transition_to_open_unlocked()
            elif state == CircuitState.HALF_OPEN:
                self._transition_to_open_unlocked()
                self._half_open_success_count = 0
            return self._state

    def _transition_to_open_unlocked(self):
        self._state = CircuitState.OPEN
        self._last_open_time = time.time()

    def _should_open_by_rate_unlocked(self) -> bool:
        total = len(self._call_records)
        if total < self.min_calls:
            return False
        failures = sum(1 for _, success in self._call_records if not success)
        return (failures / total) >= self.errors_rate

    def _cleanup_old_records_unlocked(self):
        cutoff = time.time() - self.period
        while self._call_records and self._call_records[0][0] < cutoff:
            self._call_records.popleft()


# ================================================================
# Redis Distributed Circuit Breaker
# ================================================================

class RedisCircuitBreaker:
    """
    Redis distributed three-state circuit breaker

    Shares circuit breaker state across multiple processes/machines; all consumers of the same queue_name share counts.
    Uses Redis hash to store state and sorted set to store sliding window call records.

    Note: Redis operations do not use Lua scripts, so there is a small race condition window under extremely high concurrency,
    but for a circuit breaker these races are benign (at most delayed by 1-2 calls for triggering/recovery).
    """

    HASH_KEY_PREFIX = 'funboost:circuit_breaker:'
    CALLS_KEY_SUFFIX = ':calls'

    def __init__(self,
                 queue_name: str,
                 strategy: str = 'consecutive',
                 failure_threshold: int = 5,
                 errors_rate: float = 0.5,
                 period: float = 60.0,
                 min_calls: int = 5,
                 recovery_timeout: float = 60.0,
                 half_open_max_calls: int = 3,
                 half_open_ttl: float = None,
                 ):
        self.queue_name = queue_name
        self.strategy = strategy
        self.failure_threshold = failure_threshold
        self.errors_rate = errors_rate
        self.period = period
        self.min_calls = min_calls
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.half_open_ttl = half_open_ttl

        from funboost.utils.redis_manager import RedisMixin
        self._redis = RedisMixin().redis_db_frame

        self._hash_key = f'{self.HASH_KEY_PREFIX}{queue_name}'
        self._calls_key = f'{self._hash_key}{self.CALLS_KEY_SUFFIX}'

        self._init_redis_state()

    def _hash_ttl_seconds(self) -> int:
        """Maximum TTL for the hash key: automatically cleaned up if there's no traffic after circuit break recovery"""
        return int(self.recovery_timeout * 10 + self.period * 2 + 3600)

    def _init_redis_state(self):
        defaults = {
            'state': CircuitState.CLOSED,
            'failure_count': '0',
            'half_open_success_count': '0',
            'last_open_time': '0',
            'last_half_open_time': '0',
        }
        for field, value in defaults.items():
            self._redis.hsetnx(self._hash_key, field, value)
        # Set a fallback TTL to prevent keys from remaining permanently after abnormal process exit
        self._redis.expire(self._hash_key, self._hash_ttl_seconds())

    def _get_hash_fields(self) -> dict:
        data = self._redis.hgetall(self._hash_key)
        # hgetall returns {bytes: bytes}, need to decode first
        decoded = {
            k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
            for k, v in data.items()
        }
        return {
            'state': decoded.get('state', CircuitState.CLOSED),
            'failure_count': int(decoded.get('failure_count', '0')),
            'half_open_success_count': int(decoded.get('half_open_success_count', '0')),
            'last_open_time': float(decoded.get('last_open_time', '0')),
            'last_half_open_time': float(decoded.get('last_half_open_time', '0')),
        }

    @property
    def state(self) -> str:
        fields = self._get_hash_fields()
        now = time.time()
        current_state = fields['state']

        if current_state == CircuitState.OPEN:
            if now - fields['last_open_time'] >= self.recovery_timeout:
                self._redis.hset(self._hash_key, mapping={
                    'state': CircuitState.HALF_OPEN,
                    'half_open_success_count': '0',
                    'last_half_open_time': str(now),
                })
                return CircuitState.HALF_OPEN
        elif current_state == CircuitState.HALF_OPEN and self.half_open_ttl is not None:
            if now - fields['last_half_open_time'] >= self.half_open_ttl:
                self._redis.hset(self._hash_key, mapping={
                    'state': CircuitState.OPEN,
                    'last_open_time': str(now),
                })
                return CircuitState.OPEN
        return current_state

    @property
    def failure_count(self) -> int:
        val = self._redis.hget(self._hash_key, 'failure_count')
        if val is None:
            return 0
        return int(val.decode() if isinstance(val, bytes) else val)

    def time_until_half_open(self) -> float:
        fields = self._get_hash_fields()
        if fields['state'] != CircuitState.OPEN:
            return 0.0
        remaining = self.recovery_timeout - (time.time() - fields['last_open_time'])
        return max(0.0, remaining)

    @staticmethod
    def _is_failure_member(m) -> bool:
        """Check if a sorted set member is a failure record (compatible with bytes/str)"""
        if isinstance(m, bytes):
            return m.endswith(b':0')
        return str(m).endswith(':0')

    def get_error_rate_info(self) -> dict:
        self._cleanup_old_calls()
        members = self._redis.zrangebyscore(self._calls_key, time.time() - self.period, '+inf')
        total = len(members)
        if total == 0:
            return {'total': 0, 'failures': 0, 'rate': 0.0}
        failures = sum(1 for m in members if self._is_failure_member(m))
        return {'total': total, 'failures': failures, 'rate': failures / total}

    def record_success(self) -> str:
        current_state = self.state

        if current_state == CircuitState.CLOSED:
            if self.strategy == 'consecutive':
                self._redis.hset(self._hash_key, 'failure_count', '0')
            elif self.strategy == 'rate':
                self._redis.zadd(self._calls_key, {f'{uuid.uuid4().hex}:1': time.time()})
                self._cleanup_old_calls()

        elif current_state == CircuitState.HALF_OPEN:
            new_count = self._redis.hincrby(self._hash_key, 'half_open_success_count', 1)
            if new_count >= self.half_open_max_calls:
                self._redis.hset(self._hash_key, mapping={
                    'state': CircuitState.CLOSED,
                    'failure_count': '0',
                    'half_open_success_count': '0',
                })
                self._redis.expire(self._hash_key, self._hash_ttl_seconds())
                self._redis.delete(self._calls_key)
                return CircuitState.CLOSED

        return self.state

    def record_failure(self) -> str:
        current_state = self.state

        if current_state == CircuitState.CLOSED:
            if self.strategy == 'consecutive':
                new_count = self._redis.hincrby(self._hash_key, 'failure_count', 1)
                if new_count >= self.failure_threshold:
                    self._transition_to_open()
            elif self.strategy == 'rate':
                self._redis.zadd(self._calls_key, {f'{uuid.uuid4().hex}:0': time.time()})
                self._redis.hincrby(self._hash_key, 'failure_count', 1)
                self._cleanup_old_calls()
                if self._should_open_by_rate():
                    self._transition_to_open()

        elif current_state == CircuitState.HALF_OPEN:
            self._transition_to_open()
            self._redis.hset(self._hash_key, 'half_open_success_count', '0')

        return self.state

    def _transition_to_open(self):
        now = time.time()
        self._redis.hset(self._hash_key, mapping={
            'state': CircuitState.OPEN,
            'last_open_time': str(now),
        })
        self._redis.expire(self._hash_key, self._hash_ttl_seconds())
        # After entering OPEN, clean up expired old records in the sorted set to free memory
        self._cleanup_old_calls()

    def _should_open_by_rate(self) -> bool:
        members = self._redis.zrangebyscore(
            self._calls_key, time.time() - self.period, '+inf'
        )
        total = len(members)
        if total < self.min_calls:
            return False
        failures = sum(1 for m in members if self._is_failure_member(m))
        return (failures / total) >= self.errors_rate

    def _cleanup_old_calls(self):
        cutoff = time.time() - self.period
        self._redis.zremrangebyscore(self._calls_key, '-inf', cutoff)
        # sorted set TTL = 2x period as fallback, to prevent memory leaks when no one cleans up in extreme cases
        self._redis.expire(self._calls_key, int(self.period * 2) + 60)


# ================================================================
# CircuitBreakerConsumerMixin
# ================================================================

class CircuitBreakerConsumerMixin(AbstractConsumer):
    """
    Circuit Breaker Consumer Mixin

    All parameters are configured via user_options['circuit_breaker_options']. See module docstring for details.
    """

    def custom_init(self):
        super().custom_init()

        user_options = self.consumer_params.user_options
        cb_options = user_options['circuit_breaker_options']
        strategy = cb_options.get('strategy', 'consecutive')
        counter_backend = cb_options.get('counter_backend', 'local')

        common_kwargs = dict(
            strategy=strategy,
            failure_threshold=cb_options.get('failure_threshold', 5),
            errors_rate=cb_options.get('errors_rate', 0.5),
            period=cb_options.get('period', 60.0),
            min_calls=cb_options.get('min_calls', 5),
            recovery_timeout=cb_options.get('recovery_timeout', 60.0),
            half_open_max_calls=cb_options.get('half_open_max_calls', 3),
            half_open_ttl=cb_options.get('half_open_ttl', None),
        )

        if counter_backend == 'redis':
            self._circuit_breaker = RedisCircuitBreaker(
                queue_name=self.queue_name, **common_kwargs
            )
        else:
            self._circuit_breaker = CircuitBreaker(**common_kwargs)

        self._circuit_breaker_fallback = cb_options.get('fallback', None)
        self._tracked_exception_names = _parse_exception_names(
            cb_options.get('exceptions', None)
        )

        self.logger.info(
            f"CircuitBreaker initialized: strategy={strategy}, backend={counter_backend}, "
            f"{'failure_threshold=' + str(common_kwargs['failure_threshold']) if strategy == 'consecutive' else 'errors_rate=' + str(common_kwargs['errors_rate']) + ', period=' + str(common_kwargs['period']) + 's, min_calls=' + str(common_kwargs['min_calls'])}, "
            f"recovery_timeout={common_kwargs['recovery_timeout']}s, "
            f"half_open_max_calls={common_kwargs['half_open_max_calls']}, "
            f"half_open_ttl={common_kwargs['half_open_ttl']}, "
            f"exceptions={self._tracked_exception_names or 'all'}, "
            f"fallback={'yes' if self._circuit_breaker_fallback else 'no'}"
        )

    def _on_circuit_open(self, info_dict: dict):
        """
        Hook called when circuit break triggers. Subclasses can override this method to send alerts (WeChat/DingTalk/email, etc.).

        info_dict contains:
            old_state:       State before transition
            new_state:       State after transition (always 'open')
            queue_name:      Queue name
            failure_count:   Accumulated failure count
            strategy:        Current strategy ('consecutive' or 'rate')
            error_rate_info: Error rate details (rate strategy only, contains total/failures/rate)

        Usage example::

            class MyCircuitBreakerMixin(CircuitBreakerConsumerMixin):
                def _on_circuit_open(self, info_dict):
                    send_dingtalk(f'Queue {info_dict["queue_name"]} circuit broken!')
        """
        pass

    def _on_circuit_close(self, info_dict: dict):
        """
        Hook called when circuit break recovers. Subclasses can override this method to send recovery notifications.

        info_dict contents are the same as _on_circuit_open, with new_state always being 'closed'.

        Usage example::

            class MyCircuitBreakerMixin(CircuitBreakerConsumerMixin):
                def _on_circuit_close(self, info_dict):
                    send_wechat(f'Queue {info_dict["queue_name"]} has recovered')
        """
        pass

    def _submit_task(self, kw):
        if not self._circuit_breaker_fallback:
            while self._circuit_breaker.state == CircuitState.OPEN:
                remaining = self._circuit_breaker.time_until_half_open()
                sleep_secs = min(remaining, 5.0) if remaining > 0 else 0.1
                self.logger.warning(
                    f"CircuitBreaker OPEN for queue [{self.queue_name}], "
                    f"waiting {remaining:.1f}s for recovery"
                )
                time.sleep(sleep_secs)
        super()._submit_task(kw)

    _CB_FALLBACK_FLAG = '__funboost_cb_fallback__'

    # noinspection PyProtectedMember
    def _run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times,
                                                       function_result_status: FunctionResultStatus):
        if self._circuit_breaker_fallback and self._circuit_breaker.state == CircuitState.OPEN:
            kw[self._CB_FALLBACK_FLAG] = True
            function_only_params = kw['function_only_params'] if self._do_not_delete_extra_from_msg is False else kw['body']
            try:
                result = self._circuit_breaker_fallback(
                    **self._convert_real_function_only_params_by_conusuming_function_kind(
                        function_only_params, kw['body']['extra']
                    )
                )
                function_result_status.result = result
                function_result_status.success = True
                self.logger.debug(
                    f"CircuitBreaker fallback executed for [{self.consuming_function.__name__}], "
                    f"params={function_only_params}"
                )
            except BaseException as e:
                function_result_status.exception = f'{e.__class__.__name__}    {str(e)}'
                function_result_status.exception_msg = str(e)
                function_result_status.exception_type = e.__class__.__name__
                function_result_status.result = FunctionResultStatus.FUNC_RUN_ERROR
                self.logger.error(f"CircuitBreaker fallback error: {type(e)} {e}")
            return function_result_status

        kw.pop(self._CB_FALLBACK_FLAG, None)
        return super()._run_consuming_function_with_confirm_and_retry(kw, current_retry_times, function_result_status)

    # noinspection PyProtectedMember
    async def _async_run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times,
                                                                   function_result_status: FunctionResultStatus):
        if self._circuit_breaker_fallback and self._circuit_breaker.state == CircuitState.OPEN:
            kw[self._CB_FALLBACK_FLAG] = True
            function_only_params = kw['function_only_params'] if self._do_not_delete_extra_from_msg is False else kw['body']
            try:
                result = self._circuit_breaker_fallback(
                    **self._convert_real_function_only_params_by_conusuming_function_kind(
                        function_only_params, kw['body']['extra']
                    )
                )
                if asyncio.iscoroutine(result) or inspect.isawaitable(result):
                    result = await result
                function_result_status.result = result
                function_result_status.success = True
                self.logger.debug(
                    f"CircuitBreaker fallback executed for [{self.consuming_function.__name__}], "
                    f"params={function_only_params}"
                )
            except BaseException as e:
                function_result_status.exception = f'{e.__class__.__name__}    {str(e)}'
                function_result_status.exception_msg = str(e)
                function_result_status.exception_type = e.__class__.__name__
                function_result_status.result = FunctionResultStatus.FUNC_RUN_ERROR
                self.logger.error(f"CircuitBreaker fallback error: {type(e)} {e}")
            return function_result_status

        kw.pop(self._CB_FALLBACK_FLAG, None)
        return await super()._async_run_consuming_function_with_confirm_and_retry(kw, current_retry_times, function_result_status)

    def _is_tracked_exception(self, function_result_status: FunctionResultStatus) -> bool:
        """Check if this failure belongs to the exception types that should be tracked by the circuit breaker"""
        if self._tracked_exception_names is None:
            return True
        if not function_result_status.exception_type:
            return True
        return function_result_status.exception_type in self._tracked_exception_names

    def _frame_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus, kw: dict):
        """
        After task execution completes (including retry exhaustion), update circuit breaker state based on the final result.
        - Successful fallback executions are not counted toward recovery statistics
        - Exceptions not in the exceptions list are not counted by the circuit breaker
        """
        super()._frame_custom_record_process_info_func(current_function_result_status, kw)

        if (current_function_result_status._has_requeue
                or current_function_result_status._has_to_dlx_queue
                or current_function_result_status._has_kill_task):
            return

        if kw.get(self._CB_FALLBACK_FLAG):
            return

        old_state = self._circuit_breaker.state
        if current_function_result_status.success:
            new_state = self._circuit_breaker.record_success()
        else:
            if not self._is_tracked_exception(current_function_result_status):
                return
            new_state = self._circuit_breaker.record_failure()

        if old_state != new_state:
            info_dict = {
                'old_state': old_state,
                'new_state': new_state,
                'queue_name': self.queue_name,
                'failure_count': self._circuit_breaker.failure_count,
                'strategy': self._circuit_breaker.strategy,
            }
            if self._circuit_breaker.strategy == 'rate':
                info_dict['error_rate_info'] = self._circuit_breaker.get_error_rate_info()

            extra_info = ''
            if 'error_rate_info' in info_dict:
                ri = info_dict['error_rate_info']
                extra_info = f", error_rate={ri['rate']:.2%} ({ri['failures']}/{ri['total']})"
            self.logger.warning(
                f"CircuitBreaker state changed: {old_state} -> {new_state} "
                f"for queue [{self.queue_name}], "
                f"failure_count={info_dict['failure_count']}"
                f"{extra_info}"
            )

            try:
                if new_state == CircuitState.OPEN:
                    self._on_circuit_open(info_dict)
                elif new_state == CircuitState.CLOSED:
                    self._on_circuit_close(info_dict)
            except Exception as e:
                self.logger.error(f"circuit breaker hook error: {type(e).__name__} {e}")

    async def _aio_frame_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus, kw: dict):
        await super()._aio_frame_custom_record_process_info_func(current_function_result_status, kw)
        await simple_run_in_executor(self._frame_custom_record_process_info_func, current_function_result_status, kw)


# ================================================================
# Pre-configured BoosterParams
# ================================================================

class CircuitBreakerBoosterParams(BoosterParams):
    """
    Pre-configured BoosterParams with circuit breaker

    Usage examples:

        # Consecutive failure strategy (default)
        @boost(CircuitBreakerBoosterParams(
            queue_name='my_task',
            broker_kind=BrokerEnum.REDIS,
            user_options={
                'circuit_breaker_options': {
                    'failure_threshold': 5,
                    'recovery_timeout': 60,
                },
            },
        ))
        def my_task(x):
            return call_external_api(x)

        # Error rate strategy + Redis distributed
        @boost(CircuitBreakerBoosterParams(
            queue_name='my_task',
            broker_kind=BrokerEnum.REDIS,
            user_options={
                'circuit_breaker_options': {
                    'strategy': 'rate',
                    'counter_backend': 'redis',
                    'errors_rate': 0.5,
                    'period': 60,
                    'min_calls': 10,
                    'recovery_timeout': 30,
                },
            },
        ))
        def my_task(x):
            return call_external_api(x)
    """
    consumer_override_cls: typing.Optional[typing.Type] = CircuitBreakerConsumerMixin
    user_options: dict = {
        'circuit_breaker_options': {
            'strategy': 'consecutive',
            'counter_backend': 'local',
            'failure_threshold': 5,
            'recovery_timeout': 60.0,
            'half_open_max_calls': 3,
        },
    }


__all__ = [
    'CircuitState',
    'CircuitBreaker',
    'RedisCircuitBreaker',
    'CircuitBreakerConsumerMixin',
    'CircuitBreakerBoosterParams',
]
