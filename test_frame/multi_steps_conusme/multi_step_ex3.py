
"""
This code:
1. Demonstrates non-blocking startup of multiple function consumer queues (consume does not block the main thread)
2. Demonstrates support for publishing new tasks to any queue from within a consumer function, implementing multi-level task chains
The code structure is clear and highly extensible
"""
from funboost import boost, BrokerEnum,BoosterParams,ctrl_c_recv,ConcurrentModeEnum
import time

class MyBoosterParams(BoosterParams):  # Custom parameter class, inheriting BoosterParams, used to reduce repeated parameters in each consumer function decorator
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    max_retry_times: int = 3
    concurrent_mode: str = ConcurrentModeEnum.THREADING 

    
@boost(MyBoosterParams(queue_name='s1_queue', qps=1, ))
def step1(a:int,b:int):
    print(f'a={a},b={b}')
    time.sleep(0.7)
    for j in range(10):
        step2.push(c=a+b +j,d=a*b +j,e=a-b +j ) # Inside step1's consumer function, you can also publish messages to any other queue.
    return a+b


@boost(MyBoosterParams(queue_name='s2_queue', qps=3, ))
def step2(c:int,d:int,e:int):
    time.sleep(3)
    print(f'c={c},d={d},e={e}')
    return c* d * e


if __name__ == '__main__':
    for i in range(100):
        step1.push(i,i*2) # Send a message to step1 function's queue.
    step1.consume() # Calling .consume is non-blocking; it loops pulling messages in a separate child thread. Some people worry about blocking and manually use threading.Thread(target=step1.consume) to start consuming — this is completely redundant and wrong.
    step2.consume() # So you can smoothly start multiple consumer functions in sequence without blocking.
    ctrl_c_recv()

