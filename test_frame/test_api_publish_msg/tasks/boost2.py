import time
from funboost import boost, BrokerEnum


@boost("task_api_push_queue2", qps=50, broker_kind=BrokerEnum.REDIS)  # Parameters include 20 types with many execution control options for any control you can think of.
def task_fun2(a, b):
    print(f'{a} + {b} = {a + b}')
    time.sleep(3)  # The framework will automatically use concurrency to bypass this blocking. No matter how long the function takes internally, it will automatically adjust concurrency to achieve the target runs per second.
    return a + b


if __name__ == "__main__":
    for i in range(100):
        task_fun2.push(i, b=i * 2)  # Publisher publishes tasks
    task_fun2.consume()  # Consumer starts the loop scheduling concurrent consumption of tasks
