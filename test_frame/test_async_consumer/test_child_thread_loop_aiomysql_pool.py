"""
This script demonstrates how to use aiomysql connection pools in funboost's child thread loops.

Demonstrates 2 ways to use aiomysql connection pools:
Method 1:
async_aiomysql_f1 uses the main thread's connection pool.
The core soul of the code is that async_aiomysql_f1's decorator must pass specify_async_loop=main_thread_loop.
If async_aiomysql_f1 doesn't specify specify_async_loop, the classic error "attached to a different loop" will occur,
where the child thread's loop tries to operate the main thread loop's connection pool — this is completely wrong.

Some people don't understand main thread loops and child thread loops at all, yet insist on using the asyncio ecosystem.
People who are not proficient with the asyncio programming ecosystem should honestly use synchronous multi-threaded programming — it's much simpler.
Because funboost's thread pool FlexibleThreadPool can auto scale up and down,
auto scale-down completely demolishes the built-in concurrent.futures.ThreadPoolExecutor — it's a god-tier operation.
FlexibleThreadPool removes the futures feature implementation, simplifies the code, and improves performance by 250% over the official built-in thread pool.


Method 2:
async_aiomysql_f2_use_thread_local_aio_mysql_pool uses thread-local level global variable connection pools.
This way the child thread's loop avoids operating the main thread loop's aiomysql connection pool, preventing the "attached to a different loop" error.
"""
import threading

from funboost import boost, BrokerEnum, ConcurrentModeEnum, ctrl_c_recv, BoosterParams
import asyncio
import  time
import aiomysql


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop) # This is the key point

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'db': 'testdb',
    'charset': 'utf8mb4',
    'autocommit': True
}

g_aiomysql_pool : aiomysql.Pool
async def create_pool():
    pool = await aiomysql.create_pool(**DB_CONFIG, minsize=1, maxsize=10,) # These are key points.
    global g_aiomysql_pool
    g_aiomysql_pool = pool
    return pool



# If async_aiomysql_f1 does not specify specify_async_loop, the classic error "attached to a different loop" will occur, where the child thread's loop tries to use the main thread loop's connection pool
r"""
Traceback (most recent call last):
  File "D:\codes\funboost\test_frame\test_async_consumer\test_child_thread_loop_aiomysql_pool.py", line 46, in async_aiomysql_f1
    await cur.execute("SELECT now()")
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\cursors.py", line 239, in execute
    await self._query(query)
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\cursors.py", line 457, in _query
    await conn.query(q)
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\connection.py", line 469, in query
    await self._read_query_result(unbuffered=unbuffered)
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\connection.py", line 683, in _read_query_result
    await result.read()
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\connection.py", line 1164, in read
    first_packet = await self.connection._read_packet()
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\connection.py", line 609, in _read_packet
    packet_header = await self._read_bytes(4)
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\connection.py", line 657, in _read_bytes
    data = await self._reader.readexactly(num_bytes)
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\asyncio\streams.py", line 723, in readexactly
    await self._wait_for_data('readexactly')
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\asyncio\streams.py", line 517, in _wait_for_data
    await self._waiter
RuntimeError: Task <Task pending name='Task-2' coro=<AsyncPoolExecutor._consume() running at D:\codes\funboost\funboost\concurrent_pool\async_pool_executor.py:110>> got Future <Future pending> attached to a different loop

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "D:\codes\funboost\funboost\consumers\base_consumer.py", line 929, in _async_run_consuming_function_with_confirm_and_retry
    rs = await corotinue_obj
  File "D:\codes\funboost\test_frame\test_async_consumer\test_child_thread_loop_aiomysql_pool.py", line 48, in async_aiomysql_f1
    print(res)
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\utils.py", line 139, in __aexit__
    await self._pool.release(self._conn)
RuntimeError: Task <Task pending name='Task-2' coro=<AsyncPoolExecutor._consume() running at D:\codes\funboost\funboost\concurrent_pool\async_pool_executor.py:110>> got Future <Task pending name='Task-22' coro=<Pool._wakeup() running at D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\pool.py:203>> attached to a different loop
"""

"""
Method 1:
Consumer function uses the global g_aiomysql connection pool. Each thread uses the main thread's loop to query via the connection pool,
so @boost needs to specify specify_async_loop as the main thread's loop.
"""
@boost(BoosterParams(queue_name='async_aiomysql_f1_queue', concurrent_mode=ConcurrentModeEnum.ASYNC, broker_kind=BrokerEnum.REDIS,
        log_level=10,concurrent_num=3,
       specify_async_loop=loop, # specify_async_loop parameter is the core soul; not passing it when using the main loop's connection pool will cause an error.
       is_auto_start_specify_async_loop_in_child_thread=True,
       ))
async def async_aiomysql_f1(x):
    await asyncio.sleep(5)
    async with g_aiomysql_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT now()")
            res = await cur.fetchall()
            print(res)


thread_local = threading.local()

async def create_pool_thread_local():
    if hasattr(thread_local, 'aiomysql_pool'):
        return thread_local.aiomysql_pool
    pool = await aiomysql.create_pool(**DB_CONFIG, minsize=1, maxsize=5, )  # These are key points.
    setattr(thread_local, 'aiomysql_pool', pool)
    print('Created thread-local level aiomysql connection pool')
    return pool


"""
Method 2:
Consumer function uses thread_local thread-level global variables. Each consumer function's child thread loop uses
its own thread-level connection pool. This avoids the child thread's loop using the main thread's bound aiomysql pool
to query the database, which would cause errors.

"""
@boost(BoosterParams(queue_name='async_aiomysql_f2_queue', concurrent_mode=ConcurrentModeEnum.ASYNC, broker_kind=BrokerEnum.REDIS,
        log_level=10,concurrent_num=3,
       # specify_async_loop=loop, # specify_async_loop does not need to be passed, because the child thread's loop has its own pool and doesn't use the main thread's pool for database queries
       is_auto_start_specify_async_loop_in_child_thread=True,
       ))
async def async_aiomysql_f2_use_thread_local_aio_mysql_pool(x):
    await asyncio.sleep(5)
    aiomysql_pool_thread_local = await create_pool_thread_local()
    async with aiomysql_pool_thread_local.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT now()")
            res = await cur.fetchall()
            print(res)




if __name__ == '__main__':
    loop.run_until_complete(create_pool()) # Create pool first; aiomysql pool cannot be created directly as a module-level global variable.

    async_aiomysql_f1.clear()
    async_aiomysql_f2_use_thread_local_aio_mysql_pool.clear()

    for i in range(10):
        async_aiomysql_f1.push(i)
        async_aiomysql_f2_use_thread_local_aio_mysql_pool.push(i*10)

    async_aiomysql_f1.consume()
    async_aiomysql_f2_use_thread_local_aio_mysql_pool.consume()
    ctrl_c_recv()
