
"""
A more comprehensive example of funboost usage, including:
1. Inheriting BoosterParams to reduce repeated parameters in each decorator
2. RPC to get results
3. Smoothly starting multiple consumer functions in sequence
4. Scheduled tasks
"""
from funboost import boost, BrokerEnum,BoosterParams,ctrl_c_recv,ConcurrentModeEnum,ApsJobAdder
import time

class MyBoosterParams(BoosterParams):  # Custom parameter class, inheriting BoosterParams, used to reduce repeated parameters in each consumer function decorator
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    max_retry_times: int = 3
    concurrent_mode: str = ConcurrentModeEnum.THREADING 

    
@boost(MyBoosterParams(queue_name='s1_queue', qps=1, 
                    #    do_task_filtering=True, # Can enable task filtering to prevent duplicate parameter consumption.
                       is_using_rpc_mode=True, # Enable rpc mode, supports getting results via rpc
                       ))
def step1(a:int,b:int):
    print(f'a={a},b={b}')
    time.sleep(0.7)
    for j in range(10):
        step2.push(c=a+b +j,d=a*b +j,e=a-b +j ) # Inside step1's consumer function, you can also publish messages to any other queue.
    return a+b


@boost(MyBoosterParams(queue_name='s2_queue', qps=3, ))
def step2(c:int,d:int,e:int=666):
    time.sleep(3)
    print(f'c={c},d={d},e={e}')
    return c* d * e


if __name__ == '__main__':
    step1.clear()  # Clear queue
    step2.clear()  # Clear queue

    step1.consume() # Calling .consume is non-blocking; it starts consuming in a separate child thread with a loop pulling messages.
    # Some people worry about blocking and manually use threading.Thread(target=step1.consume).start(), which is completely redundant and wrong.
    step2.consume() # So you can smoothly start multiple consumer functions in sequence in the main thread without blocking.
    step2.multi_process_consume(3) # This is multi-process stacked with multi-thread consumption, starting 3 processes plus default thread concurrency.

    async_result = step1.push(100,b=200)
    print('step1 rpc result is:',async_result.result)  # rpc blocks and waits for step1 consumption result to return

    for i in range(100):
        step1.push(i,i*2) # Send a message to step1 function's queue; parameters are similar to calling the function directly.
        step1.publish ({'a':i,'b':i*2},task_id=f'task_{i}') # publish takes a dict as the first parameter; can pass more funboost auxiliary parameters than push. Similar to celery's apply_async vs delay relationship — one simple, one complex but powerful.
    
    

    """
    1. funboost uses ApsJobAdder.add_push_job to add scheduled tasks, not add_job.
    2. funboost is a light wrapper around the well-known apscheduler framework, so the scheduled task syntax is the same as apscheduler — no new syntax or parameters invented.
       Users need to study the apscheduler documentation; all scheduling requires apscheduler knowledge, and scheduling has little to do with funboost itself.
    3. funboost's scheduled tasks aim to push messages to the message queue on a schedule, NOT to directly execute a consumer function in the current program on a schedule.

    Below are three ways to add scheduled tasks. These scheduling methods are from the well-known apscheduler package, unrelated to funboost.
    """
    # Method 1: Execute once at a specified date
    ApsJobAdder(step2, 
               job_store_kind='redis', # Use redis as apscheduler's jobstores
               is_auto_start=True,   # Add task and simultaneously start the scheduler by calling apscheduler object .start()
    ).add_push_job(
        trigger='date',
        run_date='2025-06-30 16:25:40',
        args=(7, 8,9),
        id='date_job1',
        replace_existing=True,
    )

    # Method 2: Execute at fixed intervals
    ApsJobAdder(step2, job_store_kind='redis').add_push_job(
        trigger='interval',
        seconds=30,
        args=(4, 6,10),
        id='interval_job1',
        replace_existing=True,
    )

    # Method 3: Use cron expression for scheduled execution
    ApsJobAdder(step2, job_store_kind='redis').add_push_job(
        trigger='cron',
        day_of_week='*',
        hour=23,
        minute=49,
        second=50,
        kwargs={"c": 50, "d": 60,"e":70},
        replace_existing=True,
        id='cron_job1')
    
    ctrl_c_recv()  # Used to block code and prevent the main thread from exiting, keeping the main thread running forever. Equivalent to adding while 1:time.sleep(10) at the end of your code. The apscheduler background scheduler daemon thread needs this to keep the scheduler from exiting.