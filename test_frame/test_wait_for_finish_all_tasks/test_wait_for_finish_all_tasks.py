import time
import os

from funboost import boost


@boost('test_f1_queue', qps=0.5)
def f1(x):
    time.sleep(3)
    print(f'x: {x}')
    for j in range(1, 5):
        f2.push(x * j)


@boost('test_f2_queue', qps=2)
def f2(y):
    time.sleep(5)
    print(f'y: {y}')


if __name__ == '__main__':
    f1.clear()
    f2.clear()
    for i in range(30):
        f1.push(i)
    f1.consume()
    f2.consume()
    f1.wait_for_possible_has_finish_all_tasks(4)
    print('No tasks to execute in the f1 queue within 4 minutes')
    f2.wait_for_possible_has_finish_all_tasks(3)
    print('No tasks to execute in the f2 queue within 3 minutes')
    print('Both f1 and f2 tasks have finished...')
    print('Immediately calling os._exit(444) to end the script')
    os._exit(444)  # End the script
