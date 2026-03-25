# -*- coding: utf-8 -*-
"""
AlertNotifierConsumerMixin usage examples

Demonstrates three scenarios:
1. Consecutive failure strategy + WeCom alert
2. Error rate strategy + DingTalk alert
3. Track only specific exception types
"""
import time
import random
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv,ConcurrentModeEnum

from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import (
    AlertNotifierConsumerMixin,
    AlertNotifierBoosterParams,
)

# ================================================================
# Example 1: Consecutive failure strategy + WeCom alert (most common use case)
#
# Send a WeCom alert after 3 consecutive failures; also notify on recovery,
# with no repeated alerts within 60 seconds.
# ================================================================

@boost(AlertNotifierBoosterParams(
    queue_name='alert_demo_consecutive',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
    qps=5,
    max_retry_times=0,
    user_options={
        'alert_options': {
            'strategy': 'consecutive',
            'failure_threshold': 3,
            'alert_app': 'wechat',
            'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your_key_here',
            'alert_interval': 60,
        },
    },
))
def task_consecutive(x: int):
    """Simulate an unstable task: fails for the first 6 times, then recovers"""
    time.sleep(1)
    if x < 6:
        raise ConnectionError(f"Simulated connection failure x={x}")
    return f"success x={x}"


# ================================================================
# Example 2: Error rate strategy + DingTalk alert
#
# Alert when at least 5 calls occur within a 60-second sliding window
# and the error rate >= 50%.
# ================================================================

@boost(BoosterParams(
    queue_name='alert_demo_rate',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=5,
    max_retry_times=0,
    concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
    consumer_override_cls=AlertNotifierConsumerMixin,
    user_options={
        'alert_options': {
            'strategy': 'rate',
            'errors_rate': 0.5,
            'period': 60,
            'min_calls': 5,
            'alert_app': 'dingtalk',
            'webhook_url': 'https://oapi.dingtalk.com/robot/send?access_token=your_token_here',
            'alert_interval': 120,
        },
    },
))
def task_rate(x: int):
    """Simulate a probabilistically failing task: fails 50% of the time"""
    time.sleep(1)
    if random.random() < 0.5:
        raise TimeoutError(f"Simulated timeout x={x}")
    return f"success x={x}"


# ================================================================
# Example 3: Track only specific exception types
#
# Only ConnectionError and TimeoutError trigger alerts;
# other exception types (e.g., ValueError) are not counted.
# ================================================================

@boost(AlertNotifierBoosterParams(
    queue_name='alert_demo_filtered',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=5,
    max_retry_times=0,
    user_options={
        'alert_options': {
            'failure_threshold': 3,
            'alert_app': 'webhook',
            'webhook_url': 'https://your-custom-webhook.example.com/alert',
            'alert_interval': 60,
            'exceptions': (ConnectionError, TimeoutError),
        },
    },
))
def task_filtered(x: int):
    """ValueError will not trigger an alert; only ConnectionError will"""
    if x % 3 == 0:
        raise ValueError(f"Parameter validation failed x={x} (no alert)")
    if x % 3 == 1:
        raise ConnectionError(f"Connection failed x={x} (triggers alert)")
    return f"success x={x}"


if __name__ == '__main__':
    # Publish test messages
    for i in range(15):
        task_consecutive.push(x=i)

    for i in range(200):
        task_rate.push(x=i)

    for i in range(15):
        task_filtered.push(x=i)

    # Start consuming (all memory queues, no external dependencies)
    # task_consecutive.consume()
    task_rate.consume()
    # task_filtered.consume()

    ctrl_c_recv()
