

"""
This script demonstrates that funboost's Redis jobstore-backed apscheduler is not afraid of
repeated deployments, because it uses a Redis distributed lock to prevent scanning and
picking up the same scheduled task multiple times.
"""

from funboost import boost, BrokerEnum,ctrl_c_recv,BoosterParams,ApsJobAdder



# Define the task handler function
@boost(BoosterParams(queue_name='sum_queue550', broker_kind=BrokerEnum.REDIS))
def sum_two_numbers(x, y):  
    result = x + y 
    print(f'The sum of {x} and {y} is {result}')  

if __name__ == '__main__':
    ApsJobAdder(sum_two_numbers, job_store_kind='redis').add_push_job(
        trigger='interval',
        seconds=5,
        args=(4, 6),
        replace_existing=True,
        id='interval_job501',
    )
    ctrl_c_recv()
