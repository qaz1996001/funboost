
"""
Funboost most basic example
Demonstrates how to use the @boost decorator to create a distributed task queue
"""
import time
from funboost import boost, BrokerEnum, BoosterParams,ctrl_c_recv
import random
import nb_log
import threading



# Example 1: Simplest task function
@boost(BoosterParams(
    queue_name="demo_queue_2b4",
    broker_kind=BrokerEnum.REDIS,  # Use Redis as the message queue
    qps=5,  # Execute 5 times per second
    concurrent_num=1,  # Concurrency count of 1
    project_name="test_project1",
))
def add_task(x, y):
    """Simple addition task"""

    time.sleep(1)  # Simulate a time-consuming operation
    # if random.random() < 0.1:
    #     raise Exception('random exception')
    print(f'Calculating: {x} + {y} = {x + y}')
    return x + y


def test_thread():
    while True:
        time.sleep(30)
        print('test_thread')
        nb_log.debug('debug')
        nb_log.info('info')
        nb_log.warning('''warning
        warning line 1
        warning line 2
        warning line 3

        ''')
        nb_log.error('''error
        error line 1
        error line 2
        error line 3
        ''')
        nb_log.critical('''critical
        critical line 1
        critical line 2
        critical line 3
        ''')


if __name__ == '__main__':
    threading.Thread(target=test_thread).start()

    add_task.consume()

    for i in range(1000,2000000):
        time.sleep(1)
        add_task.push(i, i * 2)

    ctrl_c_recv()
