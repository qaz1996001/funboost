import time
from funboost import boost, BrokerEnum


@boost("task_api_push_queue1", qps=500, broker_kind=BrokerEnum.REDIS, is_using_rpc_mode=True)  # Parameters include 20 types with many execution control options for any control you can think of.
def task_fun1(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3)  # The framework will automatically use concurrency to bypass this blocking. No matter how long the function takes internally, it will automatically adjust concurrency to achieve the target runs per second.
    return x + y


if __name__ == "__main__":
    # for i in range(100):
    #     task_fun1.push(i, y=i * 2)  # Publisher publishes tasks
    task_fun1.consume()  # Start consumer
