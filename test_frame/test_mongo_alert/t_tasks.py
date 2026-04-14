# -*- coding: utf-8 -*-
"""
Test task definitions: intentionally cause some tasks to fail, to observe alert effects with MongoAlertMonitor.

Steps:
  1. Run this file first to start consumers and continuously publish tasks
  2. Then run t_monitor.py to start alert monitoring (or start monitoring first, then publish)

Prerequisites:
  - Configure Redis (broker) and MongoDB (status persistence) connection info in funboost_config.py
"""
import random
import time

from funboost import boost, BrokerEnum
from funboost.core.func_params_model import BoosterParams, FunctionResultStatusPersistanceConfig


# -- Task A: High-failure-rate queue, ~60% of tasks will raise an exception --
@boost(BoosterParams(
    queue_name='test_alert__high_failure_rate',
    broker_kind=BrokerEnum.REDIS,
    concurrent_num=5,
    function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
        is_save_status=True,
    ),
))
def task_high_failure(x: int):
    if random.random() < 0.6:
        raise ValueError(f"task_high_failure intentional failure: x={x}")
    return f"ok: {x}"


# -- Task B: Low-failure-rate queue, ~10% of tasks will raise an exception --
@boost(BoosterParams(
    queue_name='test_alert__low_failure_rate',
    broker_kind=BrokerEnum.REDIS,
    concurrent_num=5,
    function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
        is_save_status=True,
    ),
))
def task_low_failure(x: int):
    if random.random() < 0.1:
        raise ValueError(f"task_low_failure intentional failure: x={x}")
    return f"ok: {x}"


if __name__ == '__main__':
    # Start consumers (background consuming)
    task_high_failure.consume()
    task_low_failure.consume()

    # Continuously publish tasks, one batch every 0.5 seconds
    i = 0
    while True:
        task_high_failure.push(x=i)
        task_low_failure.push(x=i)
        i += 1
        time.sleep(0.5)
