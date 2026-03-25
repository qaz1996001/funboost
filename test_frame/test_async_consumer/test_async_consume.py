import time
import asyncio
from funboost import boost, BrokerEnum, ConcurrentModeEnum
from auto_run_on_remote import run_current_script_on_remote
# import uvloop
# uvloop.install()

# run_current_script_on_remote()
@boost('test_async_queue', concurrent_mode=ConcurrentModeEnum.THREADING, qps=0, broker_kind=BrokerEnum.REDIS, concurrent_num=60,log_level=20)
async def async_f(x):   # Schedule async consumer function
    # return

    # time.sleep(2)   # Cannot use synchronous time.sleep for 2 seconds; otherwise no matter how large the concurrency, actual qps max is only 0.5
    # await asyncio.sleep(2)
    print(x)
    return x * 3


@boost('test_f_queue', concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD, qps=0, broker_kind=BrokerEnum.MEMORY_QUEUE,log_level=20)
def f(y):  # Schedule synchronous consumer function
    if y % 1000 == 0:
        print(y)
    # time.sleep(7)


if __name__ == '__main__':
    async_f.clear()
    f.clear()

    for i in range(800000):
        # async_f.push(i)
        f.push(i * 1)

    # async_f.consume()
    f.consume()
