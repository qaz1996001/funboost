

import time
from funboost import boost, BrokerEnum, BoosterParams,fct


@boost(boost_params=BoosterParams(queue_name="task_queue_name2b", qps=5, broker_kind=BrokerEnum.REDIS, log_level=10,should_check_publish_func_params=False))  # Parameters include 20+ options; virtually every control scenario is supported.
def task_fun(x, y,**kwargs):
    print(kwargs)

    print(fct.full_msg)
    print(f'{x} + {y} = {x + y}')
    time.sleep(3)  # The framework automatically manages concurrency around this blocking call;
                   # no matter how long the function takes, it will automatically adjust to run task_fun 5 times per second.
    return x + y


if __name__ == "__main__":
    for i in range(10):
        task_fun.push(i, i * 2,x3=6,x4=8)  # Publisher publishes tasks
        # task_fun.publisher.send_msg({'x':i*10,'y':i*20})
    task_fun.consume()  # Consumer starts loop scheduling for concurrent task consumption
    # task_fun.multi_process_consume(2)  # Consumer starts loop scheduling for concurrent task consumption
