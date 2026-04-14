import logging
import time
from funboost import boost, BrokerEnum, BoosterParams,BoostersManager


class BoosterParamsMy(BoosterParams):  # Pass this class to avoid specifying rabbitmq as the message queue and using rpc mode every time.
    """
    When defining a subclass, fields must also include type annotations.
    """
    broker_kind: str = BrokerEnum.RABBITMQ
    max_retry_times: int = 4
    log_level: int = logging.DEBUG
    log_filename :str= 'custom.log'


@boost(boost_params=BoosterParamsMy(queue_name='task_queue_name1f', qps=3,))
def task_fun(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3)  # The framework will automatically use concurrency to bypass this blocking. No matter how long the function takes internally, it will automatically adjust concurrency to run task_fun 3 times per second.


@boost(boost_params=BoosterParamsMy(queue_name='task_queue_name2f', qps=10,))
def task_fun2(x, y):
    print(f'{x} - {y} = {x - y}')
    time.sleep(3)  # The framework will automatically use concurrency to bypass this blocking. No matter how long the function takes internally, it will automatically adjust concurrency to run task_fun 10 times per second.
    task_fun.push(x*10,y*10)
    # 1/0
    # BoostersManager.get_or_create_booster_by_queue_name(task_fun.queue_name).push(x*10,y*10)



if __name__ == "__main__":
    task_fun.multi_process_consume(2)  # Consumer starts the loop scheduling concurrent consumption of tasks
    task_fun2.multi_process_consume(2)
    for i in range(10):
        # task_fun.push(i, y=i * 2)  # Publisher publishes task
        task_fun2.push(i, i * 10)