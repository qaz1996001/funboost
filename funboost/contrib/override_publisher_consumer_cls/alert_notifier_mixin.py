# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/3/15
"""
Alert Notifier Consumer Mixin

Functionality: Automatically sends alert notifications when the consuming function fails and reaches
a threshold, and automatically sends recovery notifications when errors are resolved.
Only performs alerting, does not implement circuit breaking (no consumption blocking, no degradation).

=== Two Trigger Strategies ===

1. consecutive (consecutive failure count, default):
   Triggers alert when consecutive failures >= failure_threshold. Any single success resets the count.

2. rate (error rate sliding window):
   Within a sliding window of `period` seconds, triggers alert when call count >= min_calls
   and error rate >= errors_rate.

=== Alert Channels ===

Supports five alert channels (choose one):
- dingtalk:  DingTalk robot
- wechat:    WeChat Work robot
- feishu:    Feishu (Lark) robot
- webhook:   Custom Webhook (POST JSON: {"content": "message content"})
- custom:    User-defined, inherit AlertNotifierConsumerMixin and override custom_send_notification method

=== Deduplication and Recovery ===

- alert_interval:  Alert deduplication window in seconds; the same queue will not trigger repeated alerts within this time
- After error recovery (transitioning from alerting state to normal state), a recovery notification is automatically sent

=== user_options['alert_options'] Parameter Description ===

    strategy:           'consecutive' (consecutive failure count) or 'rate' (error rate sliding window), default 'consecutive'

    failure_threshold:  Consecutive failure count threshold (consecutive strategy), default 5
    errors_rate:        Error rate threshold 0.0~1.0 (rate strategy), default 0.5
    period:             Statistics window in seconds (rate strategy), default 60.0
    min_calls:          Minimum call count in window before evaluation (rate strategy), default 5

    alert_app:          Alert channel, options: 'dingtalk', 'wechat', 'feishu', 'webhook', 'custom', default 'wechat'
                        When set to 'custom', inherit AlertNotifierConsumerMixin and override custom_send_notification method
    webhook_url:        Webhook URL for the corresponding alert channel (required)

    alert_interval:     Alert deduplication interval in seconds; the same queue won't send repeated alerts within this time, default 300 (5 minutes)
    exceptions:         Tuple of exception types to track (None tracks all), default None

=== Usage Examples ===

    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import (
        AlertNotifierConsumerMixin,
        AlertNotifierBoosterParams,
    )

    # Method 1: Consecutive failure strategy + WeChat Work alert (simplest usage)
    @boost(AlertNotifierBoosterParams(
        queue_name='my_task',
        broker_kind=BrokerEnum.REDIS,
        user_options={
            'alert_options': {
                'failure_threshold': 5,
                'alert_app': 'wechat',
                'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your_key',
            },
        },
    ))
    def my_task(x):
        return call_external_api(x)

    # Method 2: Error rate strategy + DingTalk alert
    @boost(BoosterParams(
        queue_name='my_task_rate',
        broker_kind=BrokerEnum.REDIS,
        consumer_override_cls=AlertNotifierConsumerMixin,
        user_options={
            'alert_options': {
                'strategy': 'rate',
                'errors_rate': 0.5,
                'period': 60,
                'min_calls': 10,
                'alert_app': 'dingtalk',
                'webhook_url': 'https://oapi.dingtalk.com/robot/send?access_token=your_token',
                'alert_interval': 600,
            },
        },
    ))
    def my_task_rate(x):
        return call_external_api(x)

"""

import collections
import threading
import time
import typing
import datetime

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.func_params_model import BoosterParams
from funboost.core.function_result_status_saver import FunctionResultStatus
from funboost.utils.notify_util import Notifier
from funboost.concurrent_pool.async_helper import simple_run_in_executor

class AlertState:
    NORMAL = 'normal'
    ALERTING = 'alerting'


def _parse_exception_names(exceptions) -> typing.Optional[set]:
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


class AlertTracker:
    """
    Thread-safe alert state tracker (local memory)

    Supports two trigger strategies:
    - consecutive: Triggers alert when consecutive failures >= failure_threshold
    - rate: Triggers alert when error rate >= errors_rate and call count >= min_calls within sliding window

    Resets consecutive failure count on success. Notifies the upper layer when transitioning from ALERTING to NORMAL state.
    """

    def __init__(self,
                 strategy: str = 'consecutive',
                 failure_threshold: int = 5,
                 errors_rate: float = 0.5,
                 period: float = 60.0,
                 min_calls: int = 5,
                 ):
        self.strategy = strategy
        self.failure_threshold = failure_threshold
        self.errors_rate = errors_rate
        self.period = period
        self.min_calls = min_calls

        self._state = AlertState.NORMAL
        self._consecutive_failure_count = 0
        self._total_failure_count = 0
        self._lock = threading.Lock()

        self._call_records: typing.Deque[typing.Tuple[float, bool]] = collections.deque()

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @property
    def consecutive_failure_count(self) -> int:
        with self._lock:
            return self._consecutive_failure_count

    @property
    def total_failure_count(self) -> int:
        with self._lock:
            return self._total_failure_count

    def get_error_rate_info(self) -> dict:
        with self._lock:
            self._cleanup_old_records_unlocked()
            total = len(self._call_records)
            if total == 0:
                return {'total': 0, 'failures': 0, 'rate': 0.0}
            failures = sum(1 for _, success in self._call_records if not success)
            return {'total': total, 'failures': failures, 'rate': failures / total}

    def record_success(self) -> typing.Tuple[str, str]:
        """Record success, returns (old_state, new_state)"""
        with self._lock:
            old_state = self._state
            self._consecutive_failure_count = 0
            if self.strategy == 'rate':
                self._call_records.append((time.time(), True))
                self._cleanup_old_records_unlocked()

            if old_state == AlertState.ALERTING:
                if self.strategy == 'consecutive':
                    self._state = AlertState.NORMAL
                elif self.strategy == 'rate':
                    if not self._should_alert_by_rate_unlocked():
                        self._state = AlertState.NORMAL
            return old_state, self._state

    def record_failure(self) -> typing.Tuple[str, str]:
        """Record failure, returns (old_state, new_state)"""
        with self._lock:
            old_state = self._state
            self._consecutive_failure_count += 1
            self._total_failure_count += 1

            if self.strategy == 'consecutive':
                if self._consecutive_failure_count >= self.failure_threshold:
                    self._state = AlertState.ALERTING
            elif self.strategy == 'rate':
                self._call_records.append((time.time(), False))
                self._cleanup_old_records_unlocked()
                if self._should_alert_by_rate_unlocked():
                    self._state = AlertState.ALERTING
            return old_state, self._state

    def _should_alert_by_rate_unlocked(self) -> bool:
        total = len(self._call_records)
        if total < self.min_calls:
            return False
        failures = sum(1 for _, success in self._call_records if not success)
        return (failures / total) >= self.errors_rate

    def _cleanup_old_records_unlocked(self):
        cutoff = time.time() - self.period
        while self._call_records and self._call_records[0][0] < cutoff:
            self._call_records.popleft()


class AlertNotifierConsumerMixin(AbstractConsumer):
    """
    Alert Notifier Consumer Mixin

    All parameters are configured via user_options['alert_options']. See module docstring for details.
    Only monitors and alerts; does not implement circuit breaking logic.
    """

    def custom_init(self):
        super().custom_init()

        user_options = self.consumer_params.user_options
        alert_options = user_options.get('alert_options', {})
        strategy = alert_options.get('strategy', 'consecutive')

        self._alert_tracker = AlertTracker(
            strategy=strategy,
            failure_threshold=alert_options.get('failure_threshold', 5),
            errors_rate=alert_options.get('errors_rate', 0.5),
            period=alert_options.get('period', 60.0),
            min_calls=alert_options.get('min_calls', 5),
        )

        self._alert_app: str = alert_options.get('alert_app', 'wechat')
        self._alert_webhook_url = alert_options.get('webhook_url', None)

        notifier_kwargs = {}
        if self._alert_app == 'dingtalk':
            notifier_kwargs['dingtalk_webhook'] = self._alert_webhook_url
        elif self._alert_app == 'wechat':
            notifier_kwargs['wechat_webhook'] = self._alert_webhook_url
        elif self._alert_app == 'feishu':
            notifier_kwargs['feishu_webhook'] = self._alert_webhook_url
        self._alert_notifier = Notifier(**notifier_kwargs)

        self._alert_interval = alert_options.get('alert_interval', 300)
        self._last_alert_time = 0.0
        self._last_recovery_time = 0.0
        self._alert_time_lock = threading.Lock()

        self._alert_tracked_exception_names = _parse_exception_names(
            alert_options.get('exceptions', None)
        )

        self.logger.info(
            f"AlertNotifier initialized: strategy={strategy}, "
            f"{'failure_threshold=' + str(alert_options.get('failure_threshold', 5)) if strategy == 'consecutive' else 'errors_rate=' + str(alert_options.get('errors_rate', 0.5)) + ', period=' + str(alert_options.get('period', 60.0)) + 's, min_calls=' + str(alert_options.get('min_calls', 5))}, "
            f"alert_app={self._alert_app}, alert_interval={self._alert_interval}s, "
            f"exceptions={self._alert_tracked_exception_names or 'all'}"
        )

    def _is_alert_tracked_exception(self, function_result_status: FunctionResultStatus) -> bool:
        if self._alert_tracked_exception_names is None:
            return True
        if not function_result_status.exception_type:
            return True
        return function_result_status.exception_type in self._alert_tracked_exception_names

    def _should_send_alert(self) -> bool:
        """Check if outside the deduplication window and an alert can be sent"""
        with self._alert_time_lock:
            now = time.time()
            if now - self._last_alert_time < self._alert_interval:
                return False
            self._last_alert_time = now
            return True

    def _should_send_recovery(self) -> bool:
        """Check if outside the deduplication window and a recovery notification can be sent"""
        with self._alert_time_lock:
            now = time.time()
            if now - self._last_recovery_time < self._alert_interval:
                return False
            self._last_recovery_time = now
            return True

    def _format_alert_message(self, info_dict: dict) -> str:
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg_lines = [
            "🚨 [ALERT] Queue Task Exception",
            f"Queue name: {info_dict['queue_name']}",
            f"Strategy: {info_dict['strategy']}",
        ]
        if info_dict['strategy'] == 'consecutive':
            msg_lines.append(f"Consecutive failures: {info_dict['consecutive_failure_count']}")
        if 'error_rate_info' in info_dict:
            ri = info_dict['error_rate_info']
            msg_lines.append(f"Error rate: {ri['rate']:.2%} ({ri['failures']}/{ri['total']})")
        msg_lines.append(f"Total failures: {info_dict['total_failure_count']}")
        msg_lines.append(f"Alert time: {now_str}")
        return '\n'.join(msg_lines)

    def _format_recovery_message(self, info_dict: dict) -> str:
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg_lines = [
            "✅ [RECOVERY] Queue Task Has Recovered",
            f"Queue name: {info_dict['queue_name']}",
            f"Strategy: {info_dict['strategy']}",
            f"Recovery time: {now_str}",
        ]
        return '\n'.join(msg_lines)

    def custom_send_notification(self, message: str):
        """
        User-defined alert sending hook, automatically called when alert_app='custom'.
        Inherit AlertNotifierConsumerMixin and override this method to implement any alert method (email, SMS, internal systems, etc.).

        Example:
            class EmailAlertConsumer(AlertNotifierConsumerMixin):
                def custom_send_notification(self, message: str):
                    send_email(to='ops@example.com', subject='Task Alert', body=message)

            @boost(BoosterParams(
                queue_name='my_task',
                consumer_override_cls=EmailAlertConsumer,
                user_options={'alert_options': {'alert_app': 'custom', 'failure_threshold': 5}},
            ))
            def my_task(x):
                ...
        """
        raise NotImplementedError(
            "When alert_app='custom', you need to inherit AlertNotifierConsumerMixin and override the custom_send_notification method"
        )

    def _send_notification(self, message: str):
        """Send notification via the configured alert channel"""
        try:
            if self._alert_app == 'dingtalk':
                self._alert_notifier.send_dingtalk(message, add_caller_info=False)
            elif self._alert_app == 'wechat':
                self._alert_notifier.send_wechat(message, add_caller_info=False)
            elif self._alert_app == 'feishu':
                self._alert_notifier.send_feishu(message, add_caller_info=False)
            elif self._alert_app == 'webhook':
                if self._alert_webhook_url:
                    import requests
                    import json
                    requests.post(
                        self._alert_webhook_url,
                        headers={'Content-Type': 'application/json'},
                        data=json.dumps({'content': message}),
                        timeout=10,
                    )
            elif self._alert_app == 'custom':
                self.custom_send_notification(message)
            else:
                self.logger.warning(f"Unknown alert_app: {self._alert_app}, supported: dingtalk, wechat, feishu, webhook, custom")
        except Exception as e:
            self.logger.error(f"Failed to send alert via {self._alert_app}: {type(e).__name__} {e}")

    def _frame_custom_record_process_info_func(
            self, current_function_result_status: FunctionResultStatus, kw: dict):
        super()._frame_custom_record_process_info_func(
            current_function_result_status, kw)
        
        """
        If a task is requeued, sent to dead letter queue, or remotely killed, these are not real business failures
        and should not be counted toward the alert threshold, otherwise it would cause false alerts.
        """
        if (current_function_result_status._has_requeue
                or current_function_result_status._has_to_dlx_queue
                or current_function_result_status._has_kill_task):
            return

        if current_function_result_status.success:
            old_state, new_state = self._alert_tracker.record_success()
        else:
            if not self._is_alert_tracked_exception(current_function_result_status):
                return
            old_state, new_state = self._alert_tracker.record_failure()

        info_dict = {
            'queue_name': self.queue_name,
            'strategy': self._alert_tracker.strategy,
            'consecutive_failure_count': self._alert_tracker.consecutive_failure_count,
            'total_failure_count': self._alert_tracker.total_failure_count,
        }
        if self._alert_tracker.strategy == 'rate':
            info_dict['error_rate_info'] = self._alert_tracker.get_error_rate_info()

        # Entered alerting state -> send alert
        if new_state == AlertState.ALERTING:
            if self._should_send_alert():
                msg = self._format_alert_message(info_dict)
                self.logger.warning(
                    f"AlertNotifier triggered for queue [{self.queue_name}], "
                    f"consecutive_failures={info_dict['consecutive_failure_count']}, "
                    f"total_failures={info_dict['total_failure_count']}"
                )
                self._send_notification(msg)
            elif old_state != AlertState.ALERTING:
                self.logger.warning(
                    f"AlertNotifier triggered for queue [{self.queue_name}], "
                    f"but suppressed by alert_interval={self._alert_interval}s"
                )

        # Recovered from alerting state -> send recovery notification
        if old_state == AlertState.ALERTING and new_state == AlertState.NORMAL:
            if self._should_send_recovery():
                msg = self._format_recovery_message(info_dict)
                self.logger.info(
                    f"AlertNotifier recovered for queue [{self.queue_name}]"
                )
                self._send_notification(msg)
    
    async def _aio_frame_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus, kw: dict):
        await super()._aio_frame_custom_record_process_info_func(current_function_result_status, kw)
        await simple_run_in_executor(self._frame_custom_record_process_info_func, current_function_result_status, kw)


class AlertNotifierBoosterParams(BoosterParams):
    """
    Pre-configured BoosterParams with alert notification

    Usage examples:

        # Alert after 5 consecutive failures + WeChat Work
        @boost(AlertNotifierBoosterParams(
            queue_name='my_task',
            broker_kind=BrokerEnum.REDIS,
            user_options={
                'alert_options': {
                    'failure_threshold': 5,
                    'alert_app': 'wechat',
                    'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx',
                },
            },
        ))
        def my_task(x):
            return call_external_api(x)

        # Error rate strategy + DingTalk
        @boost(AlertNotifierBoosterParams(
            queue_name='my_task_rate',
            broker_kind=BrokerEnum.REDIS,
            user_options={
                'alert_options': {
                    'strategy': 'rate',
                    'errors_rate': 0.5,
                    'period': 60,
                    'min_calls': 10,
                    'alert_app': 'dingtalk',
                    'webhook_url': 'https://oapi.dingtalk.com/robot/send?access_token=xxx',
                    'alert_interval': 600,
                },
            },
        ))
        def my_task_rate(x):
            return call_external_api(x)
    """
    consumer_override_cls: typing.Optional[typing.Type] = AlertNotifierConsumerMixin
    user_options: dict = {
        'alert_options': {
            'strategy': 'consecutive',
            'failure_threshold': 5,
            'alert_app': 'wechat',
            'alert_interval': 300,
        },
    }


__all__ = [
    'AlertState',
    'AlertTracker',
    'AlertNotifierConsumerMixin',
    'AlertNotifierBoosterParams',
]
