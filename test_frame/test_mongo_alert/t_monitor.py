# -*- coding: utf-8 -*-
"""
MongoAlertMonitor alert monitoring example

Before running, start t_tasks.py first to let tasks continuously generate success/failure records in MongoDB.

This script demonstrates three usage scenarios:
  Scenario 1: Monitor only the high-failure-rate queue, alert by error count
  Scenario 2: Monitor only the low-failure-rate queue, alert by failure rate
  Scenario 3: Monitor both queues simultaneously, with two strategies combined (alert if either is triggered)

During execution, statistics will be collected within a window_seconds=60 second window,
checked every poll_interval=10 seconds, and alerts will not repeat within alert_interval=60 seconds.

Replace webhook_url with your own WeChat Work / DingTalk / Feishu Webhook URL.
"""
import os
from dotenv import load_dotenv

load_dotenv('/my_dotenv.env')

# Must import task definitions first to get the Booster object
from test_frame.test_mongo_alert.t_tasks import task_high_failure, task_low_failure

from funboost.core.mongo_alert_monitor import MongoAlertMonitor
from funboost import ctrl_c_recv

WECHAT_WEBHOOK = os.getenv('QYWEIXIN_WEBHOOK')

# -- Scenario 1: Alert if error count >= 5 within 60 seconds (high-failure-rate queue) --
MongoAlertMonitor(
    boosters=task_high_failure,
    alert_app='wechat',
    webhook_url=WECHAT_WEBHOOK,
    window_seconds=60,
    failure_count=5,        # Trigger if errors >= 5 within 60 seconds
    poll_interval=10,       # Check every 10 seconds
    alert_interval=60,      # No repeated alerts within 60 seconds (for testing; production recommends 300+)
).start()

# -- Scenario 2: Alert if failure rate >= 50% and total calls >= 10 within 60 seconds (low-failure-rate queue) --
MongoAlertMonitor(
    boosters=task_low_failure,
    alert_app='wechat',
    webhook_url=WECHAT_WEBHOOK,
    window_seconds=60,
    errors_rate=0.5,        # Trigger if failure rate >= 50%
    min_calls=10,           # Evaluate only when at least 10 calls have been made
    poll_interval=10,
    alert_interval=60,
).start()

# -- Scenario 3: Monitor both queues simultaneously, two strategies combined (alert if either is triggered) --
# Note: one MongoAlertMonitor instance monitors multiple queues; alert state is independent per queue
MongoAlertMonitor(
    boosters=[task_high_failure, task_low_failure],
    alert_app='wechat',
    webhook_url=WECHAT_WEBHOOK,
    window_seconds=60,
    failure_count=3,        # Alert if any queue has errors >= 3 within 60 seconds
    errors_rate=0.3,        # Or failure rate >= 30%
    min_calls=5,
    poll_interval=10,
    alert_interval=60,
).start()
