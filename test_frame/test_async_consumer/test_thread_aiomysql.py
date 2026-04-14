


"""
Demonstrates how child thread loops correctly operate async aio connection pools.

The correct approach: child thread should use asyncio.run_coroutine_threadsafe(aio_do_select(1), main_thread_loop)

The wrong approach: child thread creates its own loop but uses the main thread's aio connection pool to query the database,
causing the classic error RuntimeError: attached to a different loop.

funboost's AsyncPoolExecutor runs a loop in a child thread. Understanding this example explains why,
when operating aio connection pools, the funboost decorator needs to pass the main loop to specify_async_loop.
"""

import threading

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
    print(f'Main thread threading id: {threading.get_ident()}')
    pool = await aiomysql.create_pool(**DB_CONFIG, minsize=1, maxsize=10,) # These are key points.
    global g_aiomysql_pool
    g_aiomysql_pool = pool
    return pool


async def aio_do_select(i):
    async with g_aiomysql_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT now()")
            res = await cur.fetchall()
            print(res)

def run_do_select_in_child_thread(loopx:asyncio.AbstractEventLoop):
    """ Correct way to query database from child thread"""
    print(f'Child thread threading id: {threading.get_ident()}')
    asyncio.run_coroutine_threadsafe(aio_do_select(1), loopx)  # This is the correct solution


def run_do_select_in_child_thread_error():
    """Wrong way to query database: child thread uses its own loop to call the main thread loop's bound g_aiomysql_pool,
     causing the classic error RuntimeError: attached to a different loop
     """
    print(f'Child thread threading id: {threading.get_ident()}')
    loop = asyncio.new_event_loop()
    loop.run_until_complete(aio_do_select(1))

if __name__ == '__main__':
    loop.run_until_complete(create_pool())
    threading.Thread(target=run_do_select_in_child_thread, args=(loop,)).start()
    threading.Thread(target=run_do_select_in_child_thread_error, ).start()
    loop.run_forever()
