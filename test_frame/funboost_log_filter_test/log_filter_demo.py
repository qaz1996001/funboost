

import logging
import time
from nb_log import LogManager
from funboost import boost, BrokerEnum, BoosterParams
# # Lock the log level for the relevant namespace before importing funboost to suppress so-called annoying log messages
# # The funboost framework's funboost_config.py configuration, logo printing, etc. can be suppressed by setting the log level for the funboost.prompt namespace
# LogManager('funboost.prompt').preset_log_level(logging.INFO)
# # The python thread pool developed by the funboost author (which auto-expands on demand and can auto-shrink) prints debug logs for thread creation and destruction to give a more intuitive understanding of when threads are created and destroyed. Those who are not interested in the thread pool's uniqueness can set a higher log level for _KeepAliveTimeThread.
# LogManager('_KeepAliveTimeThread').preset_log_level(logging.INFO)



@boost( boost_params=BoosterParams(queue_name='task_queue_n10', max_retry_times=4, qps=3,
                                     log_level=10,log_filename='custom.log'))
def task_fun(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3)  # The framework will automatically use concurrency to bypass this blocking. No matter how long the function takes internally, it will automatically adjust concurrency to achieve the target runs per second.


if __name__ == "__main__":
    pass
    task_fun.consume()  # Consumer starts the loop scheduling concurrent consumption of tasks
    for i in range(10):
        task_fun.push(i, y=i * 2)  # Publisher publishes tasks



