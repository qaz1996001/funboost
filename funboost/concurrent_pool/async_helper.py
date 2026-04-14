from functools import partial
import asyncio
from concurrent.futures import Executor
from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble
# from funboost.concurrent_pool.flexible_thread_pool import FlexibleThreadPool

# Instead of using the built-in concurrent.futures.ThreadPoolExecutor, we use the smart auto-scaling thread pool.
async_executor_default = ThreadPoolExecutorShrinkAble(500)
# async_executor_default = FlexibleThreadPool(50)  # This one does not support the future feature


def get_or_create_event_loop():
    """
    Python 3.7 style get_event_loop.
    Behavior:
    - If there is a running loop -> return the current loop
    - If there is no loop -> automatically create a new loop and set it
    The behavior of get_event_loop changed significantly after Python 3.10 compared to Python 3.7
    """
    try:
        # Python 3.7+
        return asyncio.get_running_loop()
    except RuntimeError:
        # No running loop
        try:
            # Python 3.6~3.9: get_event_loop automatically creates a loop
            return asyncio.get_event_loop()
        except RuntimeError:
            # Python 3.10+: get_event_loop no longer automatically creates a loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
        
async def simple_run_in_executor(f, *args, async_executor: Executor = None, async_loop=None, **kwargs):
    """
    A powerful function that converts any synchronous blocking function f into asyncio async API syntax.
    For example: r = await simple_run_in_executor(block_fun, 20), which does not block the event loop.

    asyncio.run_coroutine_threadsafe and run_in_executor are opposites of each other.

    asyncio.run_coroutine_threadsafe is used to call async function objects (coroutines) from a non-async context
    (i.e., inside a normal synchronous function). Since the current function is not decorated with async,
    you cannot use await inside it, so you must use this. It converts an asyncio Future object into a
    concurrent.futures Future object.

    run_in_executor is used inside an async context (async-decorated functions) to call synchronous functions,
    running them in a thread pool to prevent blocking other tasks in the event loop.
    It converts a concurrent.futures Future object into an asyncio Future object.
    An asyncio Future object is an awaitable object, so it can be awaited,
    while concurrent.futures.Future objects cannot be awaited.

    :param f: f is a synchronous blocking function, it must not be defined with async.
    :param args: positional arguments for function f
    :async_executor: thread pool
    :param async_loop: async loop object
    :param kwargs: keyword arguments for function f
    :return:
    """
    loopx = async_loop or get_or_create_event_loop()
    async_executorx = async_executor or async_executor_default
    # print(id(loopx))
    result = await loopx.run_in_executor(async_executorx, partial(f, *args, **kwargs))
    return result






if __name__ == '__main__':
    import time
    import requests


    def block_fun(x):
        print(x)
        time.sleep(5)
        return x * 10


    async def enter_fun(xx):  # Entry function, simulating "once async, always async". Cannot call block_fun directly, otherwise it blocks other tasks.
        await asyncio.sleep(1)
        # r = block_fun(xx)  # Using it this way would be disastrous, blocking the event loop, and it would take much longer to finish all tasks.
        r = await  simple_run_in_executor(block_fun, xx)
        print(r)


    loopy = asyncio.get_event_loop()
    print(id(loopy))
    tasks = []
    tasks.append(simple_run_in_executor(requests.get, url='http://www.baidu.com', timeout=10))  # Sync-to-async usage.

    tasks.append(simple_run_in_executor(block_fun, 1))
    tasks.append(simple_run_in_executor(block_fun, 2))
    tasks.append(simple_run_in_executor(block_fun, 3))
    tasks.append(simple_run_in_executor(time.sleep, 8))

    tasks.append(enter_fun(4))
    tasks.append(enter_fun(5))
    tasks.append(enter_fun(6))

    print('start')
    loopy.run_until_complete(asyncio.wait(tasks))
    print('end')

    time.sleep(200)
