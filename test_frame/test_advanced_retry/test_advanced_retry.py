# -*- coding: utf-8 -*-

import datetime
import time
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv



fail_count_sleep = 0
fail_count_requeue = 0

# ========== Test 1: sleep mode + exponential backoff ==========
@boost(BoosterParams(
    queue_name='test_adv_retry_sleep_queue',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_show_message_get_from_broker=True,

    max_retry_times=30,
    is_using_advanced_retry=True,
    advanced_retry_config={
        'retry_mode': 'sleep',           # Sleep in the current thread
        'retry_base_interval': 1.0,       # Base interval 1 second
        'retry_multiplier': 2.0,          # 1s, 2s, 4s
        'retry_max_interval': 60.0,
        'retry_jitter': False,
    },

))
def task_sleep_retry(x):
    global fail_count_sleep
    fail_count_sleep += 1
    now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f'❌ [sleep mode] Execution #{fail_count_sleep} x={x}, time: {now}, about to raise exception')
    raise ValueError(f'Simulated error x={x}')


# ========== Test 2: requeue mode + exponential backoff ==========
# Note: requeue mode requires delayed task support. MEMORY_QUEUE with memory jobstore is sufficient
@boost(BoosterParams(
    queue_name='test_adv_retry_requeue_queue',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_show_message_get_from_broker=True,
    delay_task_apscheduler_jobstores_kind='memory',  # Use memory for testing, no redis dependency

    max_retry_times=100,
    is_using_advanced_retry=True,
    advanced_retry_config={
        'retry_mode': 'requeue',          # Send back to queue to wait
        'retry_base_interval': 10.0,       # Base interval 10 seconds
        'retry_multiplier': 2.0,          # 10s, 20s, 40s, 80s, 160s, 300s, 300s, 300s ...
        'retry_max_interval': 300.0,
        'retry_jitter': False,
    },
))
def task_requeue_retry(x):
    global fail_count_requeue
    fail_count_requeue += 1
    now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f'❌ [requeue mode] Execution #{fail_count_requeue} x={x}, time: {now}, about to raise exception')
    raise ValueError(f'Simulated error x={x}')


if __name__ == '__main__':
    # Publish test tasks
    task_sleep_retry.push(100)
    task_requeue_retry.push(200)

    print(f"Test tasks published, starting consumption... (time: {datetime.datetime.now().strftime('%H:%M:%S')})")
    print()

    # Start consuming
    task_sleep_retry.consume()
    # task_requeue_retry.consume()

    ctrl_c_recv()
