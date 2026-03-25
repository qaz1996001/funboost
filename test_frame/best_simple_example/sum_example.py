
import logging
import time
from nb_log import LogManager



from funboost import boost, BrokerEnum, BoosterParams,ctrl_c_recv

from test_frame.my_config import BoosterParamsMy


@boost( boost_params=BoosterParamsMy(queue_name='task_queue_name1c', max_retry_times=4, qps=3,
                                     log_level=10,log_filename='custom.log'))
def task_fun(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3)  # The framework will automatically use concurrency to bypass this blocking. No matter how long the function takes, it will automatically adjust concurrency to run task_fun the target number of times per second.
    return x + y


if __name__ == "__main__":
    pass
    task_fun.consume()  # Consumer starts the loop scheduling concurrent consumption of tasks
    for i in range(10):
        task_fun.push(i, y=i * 2)  # Publisher publishes tasks
    # ctrl_c_recv()
    # Or:
    while 1:
        time.sleep(100)
      


