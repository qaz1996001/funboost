# -*- coding: utf-8 -*-
"""
Test periodic quota rate limiting (PeriodicQuotaConsumerMixin)

Scenario: Execute once per second, but at most 6 times per minute;
after the quota is exhausted, wait 60 seconds for the quota to reset.

Usage:
    python test_periodic_quota.py

Expected behavior (sliding window mode, default):
1. Execute once per second (controlled by qps=1)
2. After 6 executions in the first 6 seconds, the quota is exhausted
3. Wait 60 seconds (until the 1-minute period from the start time ends)
4. Quota resets; continue executing once per second...
"""

import datetime
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv
from funboost.contrib.override_publisher_consumer_cls.periodic_quota_mixin import (
    PeriodicQuotaConsumerMixin,
)


# 1 per second, at most 6 per minute
@boost(BoosterParams(
    queue_name='test_periodic_quota_queue',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    consumer_override_cls=PeriodicQuotaConsumerMixin,
    is_show_message_get_from_broker = True,
    user_options={
        'quota_limit': 6,        # At most 6 times per minute
        'quota_period': 'm',     # Period is one minute
        'sliding_window': False, # Fixed window (counting from 0 seconds/minutes/hours/days)
    },
    qps=1,  # Execute once per second; periodic quota can be used together with qps
))
def task_periodic_quota(x):
    print(f'[Periodic Quota] Executing task x={x}, time: {datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]}')


if __name__ == '__main__':
    print("=" * 70)
    print("Periodic Quota Rate Limiting Test")
    print("=" * 70)
    print()
    print("Configuration:")
    print("  - quota_limit=6, quota_period='m' (at most 6 times per minute)")
    print("  - qps=1 (execute once per second)")
    print("  - sliding_window=True (default, sliding window mode)")
    print()
    print("Expected behavior (sliding window mode):")
    print("  First 6 seconds: execute once per second")
    print("  From second 7 onward: quota exhausted; wait until 60 seconds after start (end of sliding period)")
    print("  After quota reset: resume executing once per second")
    print()
    print("=" * 70)
    print()

    # Publish 100 tasks
    for i in range(100):
        task_periodic_quota.push(i)

    print(f"Published 100 tasks, starting consumption... (time: {datetime.datetime.now().strftime('%H:%M:%S')})")
    print()

    # Start consuming
    task_periodic_quota.consume()

    ctrl_c_recv()
