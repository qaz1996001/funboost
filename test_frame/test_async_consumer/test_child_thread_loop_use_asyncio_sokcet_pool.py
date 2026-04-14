"""
This script mainly demonstrates how to use asyncio async socket pools to send async requests
in funboost's automatically created separate child thread loops.
The core is to pass the main thread's loop to the child thread so both use the same loop to run async functions.
In funboost, this is done via specify_async_loop=main_thread_loop.


Using an async connection pool created in the main thread's loop to send requests from a different cross-thread loop is not possible.
Regardless of which third-party package's socket pool (e.g., aiomysql, aioredis, aiohttp, httpx), connection pools
created in the main thread cannot directly be used in child thread loop async functions to send requests via their connections.
Some async third-party packages' connection pools can be used in child thread loops without errors because they use lazy initialization.
"""

"""
Users must understand the binding relationship between threads and loops.
Must understand why different loops cannot operate on the same async connection pool for requests or database queries.

Users should write more test demos of child thread loops calling connection pools to send requests.
This has nothing to do with funboost itself.
Users' asyncio knowledge is too weak; they only know how to use loops in the main thread,
leading to misunderstanding of loop-thread binding and not knowing how different loops can operate a single connection pool.
Running async functions in child thread loops is much harder than in main thread loops, with more pitfalls.
Users need to write more demo examples, test, practice, and ask AI models.
"""

# For example, a child thread's loop trying to use the main thread loop's bound http connection pool to send requests will cause the following error. Database connection pools have the same issue.
"""
Traceback (most recent call last):
  File "D:\codes\funboost\funboost\consumers\base_consumer.py", line 929, in _async_run_consuming_function_with_confirm_and_retry
    rs = await corotinue_obj
  File "D:\codes\funboost\test_frame\test_async_consumer\test_child_thread_loop_use_asyncio_sokcet_pool.py", line 64, in async_f2
    async with ss.request('get', url=url) as resp:  # If making requests this way, boost decorator must specify specify_async_loop,
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiohttp\client.py", line 1425, in __aenter__
    self._resp: _RetType = await self._coro
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiohttp\client.py", line 607, in _request
    with timer:
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiohttp\helpers.py", line 636, in __enter__
    raise RuntimeError("Timeout context manager should be used inside a task")
RuntimeError: Timeout context manager should be used inside a task

"""

from funboost import boost, BrokerEnum, ConcurrentModeEnum, ctrl_c_recv, BoosterParams
import asyncio
import aiohttp
import time

url = 'http://mini.eastday.com/assets/v1/js/search_word.js'

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop) # This is the key point
ss = aiohttp.ClientSession(loop=loop) # This is the key point: ss is bound to the main thread's loop.


@boost(BoosterParams(queue_name='test_async_queue1', concurrent_mode=ConcurrentModeEnum.ASYNC, broker_kind=BrokerEnum.REDIS,
        log_level=10,concurrent_num=3,
       specify_async_loop=loop, # specify_async_loop parameter is the core soul; not passing it when using the main loop's connection pool will cause an error.
       is_auto_start_specify_async_loop_in_child_thread=False,
       ))
async def async_f1(x):
    """
    This function is automatically run by funboost in a loop within a separate child thread.
    The loop runs many coroutines concurrently to execute async_f1's logic.
    The most important thing users need to understand is that when using funboost's ConcurrentModeEnum.ASYNC,
    you are NOT operating async functions in the main thread; they run in a child thread's loop.
    If it were running in the main thread, how could you smoothly start multiple function consumers in sequence:
    f1.consume() f2.consume() f3.consume()? Just think about it and you'll know it's not the main thread calling async functions.
    """

    # If using async with ss.request('get', url=url) to send requests via the main thread loop's connection pool,
    # the boost decorator must specify specify_async_loop.
    # If you don't use the ss connection pool but instead use async with aiohttp.request('GET', ...) as resp:, specify_async_loop is not needed.
    async with ss.request('get', url=url) as resp:
        text = await resp.text()
        print('async_f1', x, resp.url, text[:10])
    await asyncio.sleep(5)
    return x


@boost(BoosterParams(queue_name='test_async_queue2', concurrent_mode=ConcurrentModeEnum.ASYNC, broker_kind=BrokerEnum.REDIS,
        log_level=10,concurrent_num=3,
       # specify_async_loop=loop, # specify_async_loop is the core soul parameter; not passing it when using the main loop's connection pool will cause an error.
       is_auto_start_specify_async_loop_in_child_thread=False,
       ))
async def async_f2(x):
    # If using async with ss.request('get', url=url) to send requests via the main thread loop's connection pool,
    # the boost decorator must specify specify_async_loop.
    # If you don't use the ss connection pool but instead use async with aiohttp.request('GET', ...) as resp:, specify_async_loop is not needed.
    async with aiohttp.request('get', url=url) as resp:
        text = await resp.text()
        print('async_f2', x, resp.url, text[:10])
    await asyncio.sleep(5)
    return x



async def do_req(i):
    async with ss.request('get', url=url) as resp:  # If making requests this way, boost decorator must specify specify_async_loop,
        text = await resp.text()
        print(f'Main thread loop running {i}:',text[:10])
    await asyncio.sleep(3)

if __name__ == '__main__':

    async_f1.clear()
    async_f2.clear()

    for i in range(10):
        async_f1.push(i)
        async_f2.push(i*10)

    async_f1.consume()
    async_f2.consume()

    # time.sleep(5) # Adding this tests which starts first: main thread loop or child thread loop. If child thread's specify_async_loop starts first, the main thread's loop.run_forever() below will error: RuntimeError: This event loop is already running
    main_tasks = [loop.create_task(do_req(i)) for i in range(20)]
    loop.run_forever()  # If you want to run async functions both in funboost and in your own script, configure decorator with is_auto_start_specify_async_loop_in_child_thread=False, and manually start loop.run_forever()

    ctrl_c_recv()
