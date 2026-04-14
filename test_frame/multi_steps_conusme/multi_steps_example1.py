import time

from funboost import boost, BrokerEnum,ConcurrentModeEnum,BoostersManager,BoosterParams


@boost(BoosterParams(queue_name='queue_test_step1', qps=0.5, broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_mode=ConcurrentModeEnum.THREADING))
def step1(x):
    print(f'x value is {x}')
    if x == 0:
        for i in range(1, 3):
            step1.pub(dict(x=x + i))
    for j in range(10):
        step2.push(y=x * 100 + j)  # push sends multiple parameters directly, pub publishes a dictionary
    time.sleep(10)


@boost(BoosterParams(queue_name='queue_test_step2', qps=3, broker_kind=BrokerEnum.REDIS_ACK_ABLE))
def step2(y):
    print(f'y value is {y}')
    time.sleep(10)


if __name__ == '__main__':
    # step1.clear()
    step1.push(0)

    # step1.consume()  # Can start two consumers in sequence. consume starts a while-1 loop scheduling inside an independent thread, so multiple consumers can be started in sequence.
    # step2.consume()
    # BoostersManager.consume_all() # This approach saves total memory but cannot utilize multi-core cpu
    # BoostersManager.mp_consume_all(2)  # This approach uses more total memory but fully utilizes multi-core cpu
