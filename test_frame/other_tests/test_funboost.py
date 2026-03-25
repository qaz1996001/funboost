

# from funboost import boost,BoosterParams

# @boost('test_queue')
# def add_numbers(x: int, y: int) -> int:
#     return x + y

# if __name__ == '__main__':
#     # Start the consumer
#     add_numbers.consume()

#     result = add_numbers.push(3, 4)
#     print(f"The sum is: {result.result()}")

import sys
print(sys.executable)

from funboost import boost, BoosterParams,ctrl_c_recv,run_forever
from funboost.timing_job.apscheduler_use_redis_store import funboost_background_scheduler_redis_store
from funboost.timing_job.timing_push import ApsJobAdder


class MyBoosterParams(BoosterParams):
    max_retry_times: int = 3  # Set maximum retry times to 3
    function_timeout: int = 10  # Set timeout to 10 seconds


@boost(MyBoosterParams(queue_name='add_numbers_queue'))
def add_numbers(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

if __name__ == '__main__':
    # Define scheduled task
    # Start the scheduler



    ApsJobAdder(add_numbers,job_store_kind='redis').add_push_job(
        args=(1, 2),
        trigger='date',  # Use date trigger
        run_date='2025-01-16 19:15:40',  # Set run time
        # id='add_numbers_job'  # Task ID
    )

    ApsJobAdder(add_numbers,job_store_kind='memory').add_push_job(
        args=(1, 2),
        trigger='date',  # Use date trigger
        run_date='2025-01-16 19:15:50',  # Set run time
        # id='add_numbers_job'  # Task ID
    )

    # Start consumer
    add_numbers.consume()
    ctrl_c_recv()
    # run_forever()


   
 

    
    