from eventlet import monkey_patch

monkey_patch()

from funboost.consumers.nameko_consumer import batch_start_nameko_consumers


import time

from funboost import boost, ConcurrentModeEnum, BrokerEnum



@boost('test_nameko_queue', broker_kind=BrokerEnum.NAMEKO, concurrent_mode=ConcurrentModeEnum.EVENTLET)
def f(a, b):
    print(a, b)
    time.sleep(1)
    return 'hi'


@boost('test_nameko_queue2', broker_kind=BrokerEnum.NAMEKO, concurrent_mode=ConcurrentModeEnum.EVENTLET)
def f2(x, y):
    print(f'x: {x}   y:{y}')
    time.sleep(2)
    return 'heelo'


if __name__ == '__main__':
    # Users can use nameko's ServiceContainer to directly start each nameko service class; syntax is the same as using other middleware in funboost.
    f.consume()
    f2.consume()

    # Can also start in bulk using nameko's ServiceRunner to start multiple nameko service classes. This function is specifically written for nameko middleware.
    batch_start_nameko_consumers([f, f2])
