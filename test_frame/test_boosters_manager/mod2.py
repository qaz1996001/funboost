import time

from funboost import boost, BoosterParams
import queue_names


@boost(BoosterParams(queue_name=queue_names.Q_TEST_QUEUE_MANAGER2A, qps=0.5, ))
def fun2a(x):
    print(f'fun2a x value is {x}')


@boost(BoosterParams(queue_name=queue_names.Q_TEST_QUEUE_MANAGER2B, qps=0.5, ))
def fun2b(x):
    print(f'fun2b x value is {x}')
