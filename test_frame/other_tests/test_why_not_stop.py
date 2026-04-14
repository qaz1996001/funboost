


import time
import typing

from funboost import boost,get_consumer,BoosterParams


# @boost(queue_name='task_queue_name1c', max_retry_times=4, qps=3,
#                                      log_level=10,_log_filename='custom.log')
def task_fun(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3)  # The framework will automatically use concurrency to bypass this blocking. No matter how long the function takes internally, it will automatically adjust concurrency to achieve the target runs per second.

get_consumer(BoosterParams(queue_name='task_queue_name1c', max_retry_times=4, qps=3, log_level=10,log_filename='custom.log',consuming_function=task_fun))
if __name__ == "__main__":
    pass
    print('hi')
    # task_fun.consume()  # Consumer starts the loop scheduling concurrent consumption of tasks
    # for i in range(10):
    #     task_fun.push(i, y=i * 2)  # Publisher publishes tasks
    #
    # task_fun.consume()  # Consumer starts the loop scheduling concurrent consumption of tasks

