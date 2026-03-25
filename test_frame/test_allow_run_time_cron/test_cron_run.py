
import time
import datetime
from funboost import boost, BoosterParams, BrokerEnum,ctrl_c_recv

# Scenario 1: Only run during working hours on weekdays (prerequisite for test pass: must currently be a weekday between 9-18, otherwise this will also be paused)
# * 9-18 * * 1-5 means allow running from Monday to Friday during 9:00-18:59
# qps=1 to control speed for easier observation
@boost(BoosterParams(
    queue_name='test_cron_allow_queue',
    # allow_run_time_cron='* 9-18 * * 1-5',
    allow_run_time_cron='* 9-19 * * 1-5',
    qps=1,
    broker_kind=BrokerEnum.MEMORY_QUEUE
))
def task_allow(x):
    print(f'✅ [Allowed task] Running normally... parameter: {x}, current time: {datetime.datetime.now()}')

# Scenario 2: Current time does not allow running
# 0 0 1 1 * means run at 0:00 on January 1st each year. Will not run unless it's exactly that moment.
@boost(BoosterParams(
    queue_name='test_cron_deny_queue',
    allow_run_time_cron='0 0 1 1 *',
    qps=1,
    broker_kind=BrokerEnum.MEMORY_QUEUE
))
def task_deny(x):
    print(f'❌ [Denied task] Somehow executed! BUG! parameter: {x}')

if __name__ == '__main__':
    # 1. First publish some tasks
    for i in range(2):
        task_allow.push(i)
        task_deny.push(i)

    print(f"Tasks published. Current time: {datetime.datetime.now()}")
    print("-" * 50)
    print("Expected results:")
    print("1. task_allow should print logs normally")
    print("2. task_deny should not execute any function logic, no task_deny print output in console,")
    print("   but you should see funboost's warning log: 'not within allow_run_time_cron ... pausing'")
    print("-" * 50)

    # 2. Start consuming
    task_allow.consume()
    task_deny.consume()
    ctrl_c_recv()


