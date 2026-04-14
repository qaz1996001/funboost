"""

This is a wrong way to call async coroutines. The coroutine becomes useless. Including celery — if you call async def functions this way, async becomes useless.
"""
import asyncio
from funboost import boost,BrokerEnum,ConcurrentModeEnum

async def f(x,):
    print(id(asyncio.get_event_loop()))   # From here you can see that the printed loop is different each time, not the same event loop
    await  asyncio.sleep(4)
    return x + 5

# For compatibility with asyncio, an extra function is needed — completely redundant. The correct approach is to add the decorator directly on the async def f above and set concurrent_mode=ConcurrentModeEnum.ASYNC
@boost('test_asyncio_error_queue', broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE, )
def my_task(x):
    print(asyncio.new_event_loop().run_until_complete(f(x,)))


if __name__ == '__main__':
    for i in range(5):
        my_task.push(i)
    my_task.consume()
