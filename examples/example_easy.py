"""
The most basic Funboost example.
Demonstrates how to use the @boost decorator to create a distributed task queue.
"""
import time
from funboost import boost, BrokerEnum, BoosterParams,ctrl_c_recv


# Example 1: The simplest task function
@boost(BoosterParams(
    queue_name="demo_queue_1",
    broker_kind=BrokerEnum.SQLITE_QUEUE,  # Use SQLite as the message queue; no extra middleware needed
    qps=5,  # Execute 5 times per second
    concurrent_num=10,  # Concurrency of 10
))
def add_task(x, y):
    """Simple addition task"""
    print(f'Calculating: {x} + {y} = {x + y}')
    time.sleep(1)  # Simulate a time-consuming operation
    return x + y


if __name__ == '__main__':
    for i in range(10):
        add_task.push(i, i * 2)
    add_task.consume()
    ctrl_c_recv()
