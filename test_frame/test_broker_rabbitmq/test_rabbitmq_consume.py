import time
import random
from funboost import boost, BrokerEnum,BoosterParams,ctrl_c_recv
from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble

pool = ThreadPoolExecutorShrinkAble(200)


@BoosterParams(queue_name='test_rabbit_queue71', broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM, is_show_message_get_from_broker=True, specify_concurrent_pool=pool)
def test_fun(x):
    # time.sleep(2.9)
    # Sleep time randomly ranges from 0.1ms to 5s; the ratio between min and max is 50,000x.
    # A traditional fixed-size thread pool is powerless for unknown-duration tasks with 50,000x variance at 100 qps.
    # But this framework achieves precise rate control with just a simple qps setting.
    # random_sleep = random.randrange(1,50000) / 10000
    # time.sleep(random_sleep)
    # print(x,random_sleep)
    # time.sleep(20000)
    print(f'start {x}')
    rd= random.random()
    time_sleep = 0
    if 0 < rd < 0.3:
        time_sleep = 500
    if 0.3 < rd < 0.6 :
        time_sleep = 1700
    if 0.6 < rd < 1 :
        time_sleep = 1900
    time_sleep=1900
    time.sleep(time_sleep)
    print(time_sleep)
    print(x * 2)
    return x * 2


@BoosterParams(queue_name='test_rabbit_queue8g21', broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM, is_show_message_get_from_broker=True, qps=400, specify_concurrent_pool=pool,
       broker_exclusive_config={'x-max-priority':4,'no_ack':True})
def test_fun2(x):
    # time.sleep(2.9)
    # Sleep time randomly ranges from 0.1ms to 5s; the ratio between min and max is 50,000x.
    # A traditional fixed-size thread pool is powerless for unknown-duration tasks with 50,000x variance at 100 qps.
    # But this framework achieves precise rate control with just a simple qps setting.
    # random_sleep = random.randrange(1,50000) / 10000
    # time.sleep(random_sleep)
    # print(x,random_sleep)
    print(f'Ready to run {x}')
    time.sleep(30)
    print(f'Finished running {x}')

    return x


if __name__ == '__main__':
    test_fun.push(666)
    test_fun.consume()
    test_fun2.push(1)
    test_fun2.consume()
    ctrl_c_recv()
