import time
from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name="task_queue_1",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=2,
    concurrent_num=10
))
def task1(x, y):
    print(f'[Task1] Computing: {x} + {y} = {x + y}')
    time.sleep(1)
    return x + y


@boost(BoosterParams(
    queue_name="task_queue_2",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=3,
    concurrent_num=10
))
def task2(a, b):
    print(f'[Task2] Computing: {a} * {b} = {a * b}')
    time.sleep(1)
    return a * b


if __name__ == '__main__':
    print('--- Starting consumers for two functions ---')
    task1.consume()
    task2.consume()

    print('\n--- Publishing task1 ---')
    for i in range(3):
        task1.push(i, i * 2)

    print('\n--- Publishing task2 ---')
    for i in range(3):
        task2.push(i, i * 2)

    print('\n--- Demo complete ---')
    time.sleep(5)
