import time
from funboost.utils.ctrl_c_end import ctrl_c_recv

from funboost.core.func_params_model import TaskOptions
from funboost import boost, BrokerEnum,ConcurrentModeEnum,BoosterParams,Booster,ctrl_c_recv

from logging_tree import printout

@BoosterParams(queue_name='queue_test_step1b', qps=0.5, broker_kind=BrokerEnum.REDIS_ACK_ABLE, 
               concurrent_mode=ConcurrentModeEnum.THREADING)
def step1(x):
    print(f'x value is {x}')
    time.sleep(10)
    step2.publish({'y':x*10},task_options=TaskOptions(countdown=5))


@Booster(BoosterParams(queue_name='queue_test_step2b', qps=3, broker_kind=BrokerEnum.REDIS_ACK_ABLE))
def step2(y):
    print(f'y value is {y}')
    time.sleep(20)



if __name__ == '__main__':

    step1.push(2)
    printout()

    # step1.consume()
    # step2.consume()



    """
    step1.consume()
    step2.consume()
    All consume() calls run in child threads.
    The main thread will finish quickly, with only the child threads running. Need to prevent RuntimeError: cannot schedule new futures after interpreter shutdown.

    Since the user's main thread finishes quickly, the scheduled tasks use apscheduler's BackgroundScheduler type.
    If users use scheduling, just add a statement at the end of the code to prevent the main thread from exiting.
    """
    # while 1: # This line prevents the main thread from exiting, solving RuntimeError: cannot schedule new futures after interpreter shutdown
    #     time.sleep(100)
    ctrl_c_recv()

