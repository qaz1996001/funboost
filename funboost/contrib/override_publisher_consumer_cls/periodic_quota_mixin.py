# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/2/1
"""
Periodic Quota Rate Limiter Consumer Mixin

Functionality: Limits the number of executions within a specified period; the quota automatically resets
when the period ends. This concept goes beyond Celery's rate_limit.

For example, suppose ChatGPT allows you to use it 24 times per day. That does not mean you need to wait
1 hour between each use. You can use up your daily quota all at once and then stop for the rest of the day.
So periodic quota and execution frequency are two different concepts — periodic quota does not mean you
divide the quota by the period length and execute at a uniform rate.
If you had to wait 1 hour between each ChatGPT use, you'd be constantly watching the clock — that's painful.
Being free to use up your 24 quota whenever you want is much more natural.

The periodic quota feature can be used together with the qps parameter: one controls frequency, the other controls periodic quota.

Celery's rate_limit is thoroughly beaten by funboost's periodic quota feature.
Celery's rate_limit = '24/d' forces a 1-hour gap between each execution — that's not what we want.


=== Core Concepts ===

Difference from token bucket:
- Token bucket: tokens are continuously replenished at rate = quota/period
- Periodic quota: quota resets at the start of each period; pauses when quota is exhausted within the period

=== Two Window Modes ===

1. Sliding window (sliding_window=True, default):
   - Period starts from the program start time
   - Example: started at 19:33:55, 6 times per minute -> period is 19:33:55 ~ 19:34:55

2. Fixed window (sliding_window=False):
   - Period starts from the aligned boundary (e.g., top of the minute/hour/day)
   - Example: 6 times per minute -> period is 19:33:00 ~ 19:34:00

=== Use Cases ===

Typical scenario: automatically comment on a blog 30 times per day, once every 10 minutes,
stopping when the daily quota is exhausted.
Configuration:
    quota_limit = 30        # at most 30 executions per period
    quota_period = 'd'      # period is "day"
    qps = 1/600             # execute once every 10 minutes
    sliding_window = False  # use fixed window, counting from midnight

Effect:
    - Because qps=0.00167, only executes once every 10 minutes (uniform interval)
    - Because quota_limit=30, quota_period='d', at most 30 executions per day
    - Pauses when quota is exhausted; quota automatically resets to 30 at midnight the next day

=== Usage Examples ===

    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.contrib.override_publisher_consumer_cls.periodic_quota_mixin import PeriodicQuotaConsumerMixin

    # Sliding window mode (default): 1 per second, at most 6 per minute
    @boost(BoosterParams(
        queue_name='minute_quota_queue',
        broker_kind=BrokerEnum.REDIS,
        consumer_override_cls=PeriodicQuotaConsumerMixin,
        user_options={
            'quota_limit': 6,           # at most 6 executions per period
            'quota_period': 'm',        # period is minutes (s/m/h/d)
            'sliding_window': True,     # sliding window (default, can be omitted)
        },
        qps=1,  # execute once per second (interval control) # periodic quota can be used with qps
    ))
    def my_task(x):
        print(f'Processing {x}')
"""

import threading
import time
import datetime
import typing
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.constant import BrokerEnum
from funboost.core.func_params_model import BoosterParams


class PeriodicQuota:
    """
    Periodic quota implementation

    Parameters:
    - quota_limit: Maximum number of executions per period
    - period_type: Period type ('s', 'm', 'h', 'd')
    - sliding_window: Whether to use sliding window mode
        - True (default): Sliding window, counting from program start time (e.g. at most N times in the first hour after start)
        - False: Fixed window, counting from aligned boundary (e.g. each hour starts at XX:00:00)
        Example: ChatGPT allows 24 uses from 00:00 to 24:00 (fixed), or 24 uses in any rolling 24-hour window (sliding).
        Fixed window (False): You used 24 times during Jan 1 23:50-23:59; you can use 24 more times after Jan 2 00:01 (new day boundary).
        Sliding window (True): You used 24 times during Jan 1 23:50-23:59; you cannot use it at Jan 2 00:01 — must wait until Jan 2 23:50.
    """
    
    PERIOD_SECONDS = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
    }
    
    def __init__(self, quota_limit: int, period_type: str = 'm', sliding_window: bool = False):
        self.quota_limit = quota_limit
        self.period_type = period_type
        self.period_seconds = self.PERIOD_SECONDS.get(period_type, 60)
        self.sliding_window = sliding_window
        
        self._used_count = 0
        self._lock = threading.Lock()
        
        # Set period start based on window mode
        if sliding_window:
            # Sliding window: start from the current time
            self._current_period_start = time.time()
        else:
            # Fixed window: start from the aligned boundary
            self._current_period_start = self._get_fixed_period_start(time.time())

    def _get_fixed_period_start(self, timestamp: float) -> float:
        """Calculate the start time of the period that the current timestamp belongs to (aligned boundary) in fixed window mode"""
        dt = datetime.datetime.fromtimestamp(timestamp)
        
        if self.period_type == 's':
            return datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second).timestamp()
        elif self.period_type == 'm':
            return datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0).timestamp()
        elif self.period_type == 'h':
            return datetime.datetime(dt.year, dt.month, dt.day, dt.hour, 0, 0).timestamp()
        elif self.period_type == 'd':
            return datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0).timestamp()
        else:
            return datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0).timestamp()
    
    def _check_and_reset_period(self):
        """Check if a new period has started; if so, reset the quota"""
        now = time.time()

        if self.sliding_window:
            # Sliding window: check if the period length has elapsed
            if now - self._current_period_start >= self.period_seconds:
                self._current_period_start = now
                self._used_count = 0
                return True
        else:
            # Fixed window: check if a new aligned-boundary period has started
            current_period_start = self._get_fixed_period_start(now)
            if current_period_start > self._current_period_start:
                self._current_period_start = current_period_start
                self._used_count = 0
                return True

        return False

    def acquire(self, timeout: float = None) -> bool:
        """
        Attempt to acquire one quota unit

        :param timeout: Maximum wait time in seconds; None means wait indefinitely
        :return: Whether the quota was successfully acquired
        """
        start_time = time.time()

        while True:
            with self._lock:
                self._check_and_reset_period()

                if self._used_count < self.quota_limit:
                    self._used_count += 1
                    return True

            # Calculate time remaining until the next period
            now = time.time()
            next_period_start = self._current_period_start + self.period_seconds
            wait_time = next_period_start - now

            if wait_time <= 0:
                # New period has already started, continue the loop to check again
                continue

            # Check if timed out
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
                wait_time = min(wait_time, timeout - elapsed)

            # Wait, but at most 1 second before rechecking
            time.sleep(min(wait_time, 1.0))

    def get_remaining_quota(self) -> int:
        """Get the remaining quota for the current period"""
        with self._lock:
            self._check_and_reset_period()
            return self.quota_limit - self._used_count

    def get_seconds_until_reset(self) -> float:
        """Get the number of seconds until the next quota reset"""
        now = time.time()
        next_period_start = self._current_period_start + self.period_seconds
        return max(0, next_period_start - now)


class PeriodicQuotaConsumerMixin(AbstractConsumer):
    """
    Periodic Quota Rate Limiter Consumer Mixin

    Core principle:
    1. At the start of each period, the quota resets to quota_limit
    2. Each execution consumes 1 quota unit
    3. When the quota is exhausted, waits until the next period begins
    4. Combined with qps to control execution interval

    Configuration parameters (passed via user_options):
    - quota_limit: Maximum executions per period
    - quota_period: Period type ('s'=second, 'm'=minute, 'h'=hour, 'd'=day)
    - sliding_window: Window mode (True=sliding window [default], False=fixed window)
    """

    def custom_init(self):
        """Initialize periodic quota"""
        super().custom_init()

        user_options = self.consumer_params.user_options
        quota_limit = user_options.get('quota_limit', 10)
        quota_period = user_options.get('quota_period', 'm')
        sliding_window = user_options.get('sliding_window', True)  # Default: use sliding window

        # Create periodic quota object
        self._periodic_quota = PeriodicQuota(
            quota_limit=quota_limit,
            period_type=quota_period,
            sliding_window=sliding_window
        )
        
        period_names = {'s': 'second', 'm': 'minute', 'h': 'hour', 'd': 'day'}
        if quota_period not in period_names:
            raise ValueError(f'quota_period is error,must in {period_names}')
        period_name = period_names.get(quota_period, quota_period)
        window_mode = "sliding" if sliding_window else "fixed"
        
        self.logger.info(
            f"PeriodicQuota rate limiter initialized: "
            f"quota_limit={quota_limit}/{period_name}, mode={window_mode}, qps={self.consumer_params.qps}"
        )
    
    def _check_quota_before_execute(self):
        """
        Check quota before task execution

        If the quota is exhausted, blocks until the next period begins
        """
        remaining = self._periodic_quota.get_remaining_quota()
        if remaining <= 0:
            wait_seconds = self._periodic_quota.get_seconds_until_reset()
            self.logger.warning(
                f"Quota exhausted ({self._periodic_quota.quota_limit}/{self._periodic_quota.period_type}), "
                f"waiting {wait_seconds:.1f}s for next period reset"
            )
        
        # Block until a quota unit is acquired
        self._periodic_quota.acquire(timeout=86400)

    def _submit_task(self, kw):
        """
        Override _submit_task method to check quota before task execution
        """
        # Step 1: Check quota first (block until a quota unit is available)
        self._check_quota_before_execute()

        # Step 2: Call parent class's _submit_task to execute the task
        super()._submit_task(kw)


class PeriodicQuotaBoosterParams(BoosterParams):
    """
    Pre-configured periodic quota BoosterParams

    Usage examples:

        # 1 per second, at most 6 per minute
        @boost(PeriodicQuotaBoosterParams(
            queue_name='minute_quota_queue',
            user_options={'quota_limit': 6, 'quota_period': 'm'},
            qps=1,
        ))
        def my_task(x):
            ...
    """
    broker_kind: str = BrokerEnum.REDIS
    consumer_override_cls: typing.Optional[typing.Type] = PeriodicQuotaConsumerMixin
    qps: typing.Union[float, int, None] = 1
    user_options: dict = {
        'quota_limit': 10,
        'quota_period': 'm',  # s=second, m=minute, h=hour, d=day
        'sliding_window': True,  # sliding window (default, can be omitted)
    }
