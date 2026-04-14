
"""
After 2025, scheduled tasks are now recommended to use the ApsJobAdder style;
users no longer need to manually choose an apscheduler object to add scheduled tasks.

Benefits of using ApsJobAdder (a wrapper around apscheduler) versus using apscheduler directly:

1. ApsJobAdder.add_push_job adds tasks that are published to the message queue on schedule.
   Users can avoid writing a separate push_xx_fun_to_broker function;
   instead of apscheduler.add_job(push_xx_fun_to_broker, args=(1,)),
   just use ApsJobAdder.add_push_job(xx_fun, args=(1,)).

2. When using Redis as the job_store, ApsJobAdder uses a separate jobs_key for each consumer
   function, with an independent apscheduler object per consumer, avoiding interference
   between scheduled task scans.
   For example, you can start the scheduled task for fun1 without starting fun2's.

3. When using Redis as the job_store, _process_jobs uses a Redis distributed lock, solving the
   classic headache of apscheduler recommending only one process start.
   Now you can start multiple apscheduler objects across multiple machines and processes
   without causing duplicate scheduled task executions.
"""

from funboost import boost, BrokerEnum,ctrl_c_recv,BoosterParams,ApsJobAdder



# Define the task handler function
@boost(BoosterParams(queue_name='sum_queue5', broker_kind=BrokerEnum.REDIS))
def sum_two_numbers(x, y):
    result = x + y
    print(f'The sum of {x} and {y} is {result}')


@boost(BoosterParams(queue_name='data_queue5', broker_kind=BrokerEnum.REDIS))
def show_msg(data):
    print(f'data: {data}')

if __name__ == '__main__':

    # Start consumers
    sum_two_numbers.consume()
    show_msg.consume()

    # Publish tasks
    sum_two_numbers.push(3, 5)
    sum_two_numbers.push(10, 20)

    show_msg.push('hello world')

    # Use ApsJobAdder to add scheduled tasks; the scheduling syntax inside is the same as apscheduler.
    # Users should be familiar with the add_job timing parameters of the well-known apscheduler framework.

    # Method 1: Execute once at a specified date
    # ApsJobAdder(sum_two_numbers, job_store_kind='redis').aps_obj.start(paused=False)
    ApsJobAdder(sum_two_numbers, job_store_kind='redis').add_push_job(
        trigger='date',
        run_date='2025-01-17 23:25:40',
        args=(7, 8),
        replace_existing=True,  # If an id is specified, the same id cannot be added twice; use replace_existing to replace the previous scheduled task
        id='date_job1'
    )

    # Method 2: Execute at a fixed interval, using memory as the apscheduler job_store
    ApsJobAdder(sum_two_numbers, job_store_kind='redis').add_push_job(
        trigger='interval',
        seconds=5,
        args=(4, 6),
        replace_existing=True,
        id='interval_job1',
    )

    # Method 3: Execute on a cron schedule
    ApsJobAdder(sum_two_numbers, job_store_kind='redis').add_push_job(
        trigger='cron',
        day_of_week='*',
        hour=23,
        minute=49,
        second=50,
        kwargs={"x":50,"y":60},
        replace_existing=True,
        id='cron_job1')

    # Use memory as the apscheduler job_store for delayed tasks; since it uses memory, this schedule cannot be persisted.
    ApsJobAdder(show_msg, job_store_kind='memory').add_push_job(
        trigger='interval',
        seconds=20,
        args=('hi python',)
    )

    ctrl_c_recv()  # Prevent the main thread from ending; this is important for background-type apscheduler to avoid errors about the main thread having exited. You can also add time.sleep at the end.
