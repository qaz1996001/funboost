# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/3/16
"""
MongoDB-polling-based Distributed Alert Monitor (Mongo Alert Monitor)

Principle: Users configure is_save_status=True in BoosterParams to save function execution status to MongoDB.
This module periodically polls MongoDB for execution records within the last N seconds, tallies success/failure,
sends an alert when the alert condition is met, and sends a recovery notification when it recovers.

Advantages:
- Naturally distributed aggregation: all process/machine consumers write their status to the same MongoDB collection,
  and a single monitoring instance can aggregate global execution status.
- Zero intrusion: no need to modify consumer code, no mixin needed, just enable is_save_status.
- Supports monitoring multiple queues simultaneously.

=== Prerequisites ===

Consumers must enable status persistence:

    @boost(BoosterParams(
        queue_name='my_task',
        broker_kind=BrokerEnum.REDIS,
        function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
            is_save_status=True,
        ),
    ))
    def my_task(x):
        ...

=== Two Alert Strategies ===

1. count (error count):
   Alert when errors >= failure_count within window_seconds seconds.

2. rate (error rate):
   Alert when total calls >= min_calls and failure rate >= errors_rate within window_seconds seconds.

Both strategies can be set simultaneously; either condition being met triggers an alert.

=== MongoAlertMonitor Parameter Description ===

    boosters:           Functions decorated with @boost (Booster objects), supports single or list, auto-extracts queue_name and table_name
    alert_app:          Alert channel: 'dingtalk', 'wechat', 'feishu', 'webhook', 'custom', default 'wechat'
                        When set to 'custom', inherit MongoAlertMonitor and override the custom_send_notification method.
    webhook_url:        Webhook URL for the alert channel (used when alert_app is 'webhook')

    window_seconds:     Statistics window in seconds, queries execution records within the last N seconds, default 60

    failure_count:      Error count threshold within the window; alert when reached. None means no count-based alert. Default None. When alerting by count, min_calls is ignored.
    errors_rate:        Failure rate threshold within the window, 0.0~1.0. None means no rate-based alert. Default None.
    min_calls:          Minimum call count in the window before rate-based evaluation, default 5

    poll_interval:      Polling interval in seconds, default 10
    alert_interval:     Alert deduplication interval in seconds, default 300

=== Usage Examples ===

    from funboost.core.mongo_alert_monitor import MongoAlertMonitor

    # Example 1: Monitor a single queue, alert when errors >= 10 in the window
    MongoAlertMonitor(
        boosters=my_task,
        alert_app='wechat',
        webhook_url='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx',
        window_seconds=60,
        failure_count=10,
    ).start()

    # Example 2: Monitor multiple queues at once, alert when failure rate >= 50%
    MongoAlertMonitor(
        boosters=[task_a, task_b, task_c],
        alert_app='dingtalk',
        webhook_url='https://oapi.dingtalk.com/robot/send?access_token=xxx',
        window_seconds=60,
        errors_rate=0.5,
        min_calls=10,
    ).start()

    # Example 3: Both strategies active at once (either condition triggers alert)
    MongoAlertMonitor(
        boosters=[my_task, other_task], #  To monitor all boosters, use boosters=BoostersManager.get_all_boosters()
        alert_app='feishu',
        webhook_url='https://open.feishu.cn/open-apis/bot/v2/hook/xxx',
        window_seconds=60,
        failure_count=10,     # errors >= 10
        errors_rate=0.3,      # or failure rate >= 30%
        min_calls=5,
    ).start()

    # Example 4: Custom alert channel (e.g. email), inherit and override custom_send_notification
    class EmailAlertMonitor(MongoAlertMonitor):
        def custom_send_notification(self, message: str):
            import smtplib
            from email.mime.text import MIMEText
            msg = MIMEText(message)
            msg['Subject'] = 'Task Alert'
            msg['From'] = 'bot@example.com'
            msg['To'] = 'ops@example.com'
            with smtplib.SMTP('smtp.example.com') as s:
                s.send_message(msg)

    EmailAlertMonitor(
        boosters=my_task,
        alert_app='custom',
        window_seconds=60,
        failure_count=10,
    ).start()


"""

import datetime
import time
import typing

from funboost.constant import MongoDbName
from funboost.utils.mongo_util import MongoMixin
from funboost.utils.notify_util import Notifier
from funboost.core.loggers import logger_notify
from  funboost.core.funboost_time import FunboostTime
logger = logger_notify


class _QueueAlertState:
    """Alert state tracking for a single queue."""

    def __init__(self, queue_name: str, table_name: str):
        self.queue_name = queue_name
        self.table_name = table_name
        self.is_alerting = False
        self.last_alert_time = 0.0
        self.last_recovery_time = 0.0


class MongoAlertMonitor(MongoMixin):
    """
    MongoDB-polling-based distributed alert monitor.

    Periodically queries MongoDB for function execution records within the last window_seconds seconds,
    determines whether to alert based on error count or error rate, and sends a recovery notification when recovered.
    Supports monitoring multiple booster queues simultaneously, with independent alert state per queue.
    """

    def __init__(self,
                 boosters,
                 alert_app: str = 'wechat',
                 webhook_url: str = None,
                 window_seconds: float = 60,
                 failure_count: int = None,
                 errors_rate: float = None,
                 min_calls: int = 5,
                 poll_interval: float = 10,
                 alert_interval: float = 300,
                 ):
        if failure_count is None and errors_rate is None:
            raise ValueError("At least one of failure_count or errors_rate must be set, otherwise alerts cannot be triggered.")

        # Support a single booster or a list
        if not isinstance(boosters, (list, tuple)):
            boosters = [boosters]

        self._queue_states: typing.List[_QueueAlertState] = []
        for booster in boosters:
            bp = booster.boost_params
            queue_name = bp.queue_name
            table_name = bp.function_result_status_persistance_conf.table_name or queue_name
            self._queue_states.append(_QueueAlertState(queue_name, table_name))

        self.window_seconds = window_seconds
        self.failure_count = failure_count
        self.errors_rate = errors_rate
        self.min_calls = min_calls
        self.poll_interval = poll_interval
        self.alert_interval = alert_interval

        self._alert_app = alert_app
        self._webhook_url = webhook_url
        notifier_kwargs = {}
        if alert_app == 'dingtalk':
            notifier_kwargs['dingtalk_webhook'] = webhook_url
        elif alert_app == 'wechat':
            notifier_kwargs['wechat_webhook'] = webhook_url
        elif alert_app == 'feishu':
            notifier_kwargs['feishu_webhook'] = webhook_url
        self._notifier = Notifier(**notifier_kwargs)

    def _query_stats(self, queue_state: _QueueAlertState) -> dict:
        """Query execution statistics for the specified queue_name within the last window_seconds seconds."""
        col = self.get_mongo_collection(MongoDbName.TASK_STATUS_DB, queue_state.table_name)
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=self.window_seconds)

        pipeline = [
            {'$match': {'queue_name': queue_state.queue_name, 'utime': {'$gte': cutoff}}},
            {'$group': {
                '_id': None,
                'total': {'$sum': 1},
                'failures': {'$sum': {'$cond': [{'$eq': ['$success', False]}, 1, 0]}},
                'successes': {'$sum': {'$cond': [{'$eq': ['$success', True]}, 1, 0]}},
            }},
        ]
        results = list(col.aggregate(pipeline))
        if not results:
            return {'total': 0, 'failures': 0, 'successes': 0, 'rate': 0.0}
        r = results[0]
        total = r['total']
        failures = r['failures']
        return {
            'total': total,
            'failures': failures,
            'successes': r['successes'],
            'rate': failures / total if total > 0 else 0.0,
        }

    def _is_alert_condition_met(self, stats: dict) -> bool:
        """Determine whether the alert condition is met (triggered if either strategy is satisfied)."""
        if self.failure_count is not None:
            if stats['failures'] >= self.failure_count:
                return True
        if self.errors_rate is not None:
            if stats['total'] >= self.min_calls and stats['rate'] >= self.errors_rate:
                return True
        return False

    def _should_send_alert(self, queue_state: _QueueAlertState) -> bool:
        now = time.time()
        if now - queue_state.last_alert_time < self.alert_interval:
            return False
        queue_state.last_alert_time = now
        return True

    def _should_send_recovery(self, queue_state: _QueueAlertState) -> bool:
        now = time.time()
        if now - queue_state.last_recovery_time < self.alert_interval:
            return False
        queue_state.last_recovery_time = now
        return True

    def _format_alert_message(self, queue_name: str, stats: dict) -> str:
        now_str = FunboostTime().get_str()
        lines = [
            "🚨 [ALERT] Queue task abnormality",
            f"Queue name: {queue_name}",
            f"Statistics window: last {self.window_seconds} seconds",
            f"Failures: {stats['failures']}/{stats['total']}",
            f"Failure rate: {stats['rate']:.2%}",
        ]
        triggers = []
        if self.failure_count is not None and stats['failures'] >= self.failure_count:
            triggers.append(f"Error count {stats['failures']} >= {self.failure_count}")
        if self.errors_rate is not None and stats['total'] >= self.min_calls and stats['rate'] >= self.errors_rate:
            triggers.append(f"Failure rate {stats['rate']:.2%} >= {self.errors_rate:.0%}")
        lines.append(f"Trigger condition: {'; '.join(triggers)}")
        lines.append(f"Alert time: {now_str}")
        return '\n'.join(lines)

    def _format_recovery_message(self, queue_name: str, stats: dict) -> str:
        now_str = FunboostTime().get_str()
        return '\n'.join([
            "✅ [RECOVERED] Queue task has returned to normal",
            f"Queue name: {queue_name}",
            f"Statistics window: last {self.window_seconds} seconds",
            f"Current failures: {stats['failures']}/{stats['total']} ({stats['rate']:.2%})",
            f"Recovery time: {now_str}",
        ])

    def custom_send_notification(self, message: str):
        """
        User-defined alert sending hook, automatically called when alert_app='custom'.
        Subclass MongoAlertMonitor and override this method to implement any alert method (email, SMS, internal systems, etc.).

        Example:
            class MyMonitor(MongoAlertMonitor):
                def custom_send_notification(self, message: str):
                    send_email(to='ops@example.com', subject='Task Alert', body=message)
        """
        raise NotImplementedError(
            "When alert_app='custom', you must subclass MongoAlertMonitor and override the custom_send_notification method."
        )

    def _send_notification(self, message: str):
        try:
            if self._alert_app == 'dingtalk':
                self._notifier.send_dingtalk(message, add_caller_info=False)
            elif self._alert_app == 'wechat':
                self._notifier.send_wechat(message, add_caller_info=False)
            elif self._alert_app == 'feishu':
                self._notifier.send_feishu(message, add_caller_info=False)
            elif self._alert_app == 'webhook':
                if self._webhook_url:
                    import requests
                    import json
                    requests.post(
                        self._webhook_url,
                        headers={'Content-Type': 'application/json'},
                        data=json.dumps({'content': message}),
                        timeout=10,
                    )
            elif self._alert_app == 'custom':
                self.custom_send_notification(message)
        except Exception as e:
            logger.error(f"Failed to send alert via {self._alert_app}: {type(e).__name__} {e}")

    def _check_queue(self, queue_state: _QueueAlertState):
        """Check a single queue and update its alert state."""
        stats = self._query_stats(queue_state)
        alert_triggered = self._is_alert_condition_met(stats)

        if alert_triggered:
            if not queue_state.is_alerting:
                queue_state.is_alerting = True
                logger.warning(
                    f"[{queue_state.queue_name}] ALERTING: "
                    f"failures={stats['failures']}/{stats['total']}, rate={stats['rate']:.2%}"
                )
            if self._should_send_alert(queue_state):
                self._send_notification(self._format_alert_message(queue_state.queue_name, stats))
        else:
            if queue_state.is_alerting:
                queue_state.is_alerting = False
                logger.info(
                    f"[{queue_state.queue_name}] RECOVERED: "
                    f"failures={stats['failures']}/{stats['total']}, rate={stats['rate']:.2%}"
                )
                if self._should_send_recovery(queue_state):
                    self._send_notification(self._format_recovery_message(queue_state.queue_name, stats))

        return stats

    def check_once_all(self):
        """Run one check for each monitored queue, called periodically by the scheduler."""
        for queue_state in self._queue_states:
            try:
                self._check_queue(queue_state)
            except Exception as e:
                logger.error(f"[{queue_state.queue_name}] check error: {type(e).__name__} {e}")

    def start(self):
        """
        Register an interval scheduled task with funboost_aps_scheduler to check all queues every poll_interval seconds.
        If the scheduler has not been started, it will be auto-started. Calling start() multiple times on the same MongoAlertMonitor instance only registers the job once.
        """
        from funboost.timing_job.timing_job_base import funboost_aps_scheduler

        queue_names = [qs.queue_name for qs in self._queue_states]
        strategy_desc = []
        if self.failure_count is not None:
            strategy_desc.append(f"failure_count>={self.failure_count}")
        if self.errors_rate is not None:
            strategy_desc.append(f"errors_rate>={self.errors_rate} (min_calls={self.min_calls})")
        logger.info(
            f"MongoAlertMonitor starting: queues={queue_names}, "
            f"window={self.window_seconds}s, strategy=[{', '.join(strategy_desc)}], "
            f"poll_interval={self.poll_interval}s, alert_app={self._alert_app}, "
            f"alert_interval={self.alert_interval}s"
        )

        job_id = f'mongo_alert_monitor__{id(self)}'
        funboost_aps_scheduler.add_job(
            self.check_once_all,
            trigger='interval',
            seconds=self.poll_interval,
            id=job_id,
            replace_existing=True,
            max_instances=1,
        )
        logger.info(f"MongoAlertMonitor job registered: id={job_id}, queues={queue_names}, interval={self.poll_interval}s")

        if not funboost_aps_scheduler.running:
            funboost_aps_scheduler.start()
