import sys

import atexit
import asyncio
import threading
import time
import traceback
from threading import Thread
import traceback

from funboost.concurrent_pool.base_pool_type import FunboostBaseConcurrentPool
from funboost.core.loggers import FunboostFileLoggerMixin

# if os.name == 'posix':
#     import uvloop
#
#     asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())  # Monkey patching is best placed at the top of the code, otherwise there's a high chance of issues.

"""
# An alternative approach using janus thread-safe queue to implement async pool.
# However, the queue performance is not better than the producer-consumer implementation in this module,
# so we don't reimplement it using this package.
import janus
import asyncio
import time
import threading
import nb_log
queue = janus.Queue(maxsize=6000)

async def consume():
    while 1:
        # time.sleep(1)
        val = await queue.async_q.get() # This is async, don't confuse it
        print(val)

def push():
    for i in range(50000):
        # time.sleep(0.2)
        # print(i)
        queue.sync_q.put(i)  # This is sync, don't confuse it.


if __name__ == '__main__':
    threading.Thread(target=push).start()
    loop = asyncio.get_event_loop()
    loop.create_task(consume())
    loop.run_forever()
"""

if sys.platform == "darwin":  # May cause errors on Mac
      import selectors
      selectors.DefaultSelector = selectors.PollSelector

class AsyncPoolExecutor(FunboostFileLoggerMixin,FunboostBaseConcurrentPool):
    """
    Makes the API similar to a thread pool. The best performance approach would be to make submit an async def too,
    running production and consumption in the same thread and same loop, but this would break call chain compatibility,
    making the calling pattern incompatible with thread pools.
    """

    def __init__(self, size, specify_async_loop=None,
                 is_auto_start_specify_async_loop_in_child_thread=True):
        """

        :param size: Number of coroutine tasks to run concurrently.
        :param specify_loop: Optional loop specification. Async third-party package connection pools cannot use different loops.
        """
        self._size = size
        self._specify_async_loop = specify_async_loop
        self._is_auto_start_specify_async_loop_in_child_thread = is_auto_start_specify_async_loop_in_child_thread
        self.loop = specify_async_loop or asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._diff_init()
        # self._lock = threading.Lock()
        t = Thread(target=self._start_loop_in_new_thread, daemon=False)
        # t.setDaemon(True)  # Setting daemon thread allows atexit to trigger, enabling automatic program exit without manually calling shutdown
        t.start()
     

    # def submit000(self, func, *args, **kwargs):
    #     # This performs 3x faster than the approach below using run_coroutine_threadsafe + result return.
    #     with self._lock:
    #         while 1:
    #             if not self._queue.full():
    #                 self.loop.call_soon_threadsafe(self._queue.put_nowait, (func, args, kwargs))
    #                 break
    #             else:
    #                 time.sleep(0.01)

    def _diff_init(self):
        if sys.version_info.minor < 10:
            # self._sem = asyncio.Semaphore(self._size, loop=self.loop)
            self._queue = asyncio.Queue(maxsize=self._size, loop=self.loop)
        else:
            # self._sem = asyncio.Semaphore(self._size) # After Python 3.10, many classes and methods removed the loop parameter
            self._queue = asyncio.Queue(maxsize=self._size)


    def submit(self, func, *args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(self._produce(func, *args, **kwargs), self.loop)  # The run_coroutine_threadsafe method also has drawbacks, consuming significant performance.
        future.result()  # Prevents submitting too fast; blocks submit when queue is full. Backpressure prevents rapidly draining tens of millions of messages from the message queue into memory.

    async def _produce(self, func, *args, **kwargs):
        await self._queue.put((func, args, kwargs))

    async def _consume(self):
        while True:
            func, args, kwargs = await self._queue.get()
            if isinstance(func, str) and func.startswith('stop'):
                # self.logger.debug(func)
                break
            # noinspection PyBroadException,PyUnusedLocal
            try:
                await func(*args, **kwargs)
            except BaseException as e:
                self.logger.exception(f'func:{func}, args:{args}, kwargs:{kwargs} exc_type:{type(e)}  traceback_exc:{traceback.format_exc()}')
            # self._queue.task_done()

    async def __run(self):
        for _ in range(self._size):
            asyncio.ensure_future(self._consume())

    def _start_loop_in_new_thread(self, ):
        # self._loop.run_until_complete(self.__run())  # This approach also works.
        # self._loop.run_forever()

        # asyncio.set_event_loop(self.loop)
        # self.loop.run_until_complete(asyncio.wait([self._consume() for _ in range(self._size)], loop=self.loop))
        # self._can_be_closed_flag = True
        if self._specify_async_loop is None:
            for _ in range(self._size):
                self.loop.create_task(self._consume())
        else:
            for _ in range(self._size):
                asyncio.run_coroutine_threadsafe(self._consume(),self.loop) # This is asyncio's dedicated function for safely submitting tasks to the event loop from other threads.
        if self._specify_async_loop is None:
            self.loop.run_forever()
        else:
            if self._is_auto_start_specify_async_loop_in_child_thread:
                try:
                    self.loop.run_forever() # If using a specified loop, you cannot start one loop multiple times.
                except Exception as e:
                    self.logger.warning(f'{e} {traceback.format_exc()}')   # If multiple threads use one loop, the loop cannot be started repeatedly, otherwise it will raise an error.
            else:
                pass # The user needs to manually start loop.run_forever() in their own business code


    # def shutdown(self):
    #     if self.loop.is_running():  # This may be triggered by atexit register or manually called by the user; need to check to avoid closing twice.
    #         for i in range(self._size):
    #             self.submit(f'stop{i}', )
    #         while not self._can_be_closed_flag:
    #             time.sleep(0.1)
    #         self.loop.stop()
    #         self.loop.close()
    #         print('Closing loop')



if __name__ == '__main__':
    def test_async_pool_executor():
        from funboost.concurrent_pool import CustomThreadPoolExecutor as ThreadPoolExecutor
        # from concurrent.futures.thread import ThreadPoolExecutor
        # noinspection PyUnusedLocal
        async def f(x):
            await asyncio.sleep(1)
            pass
            print('print', x)
            # await asyncio.sleep(1)
            # raise Exception('aaa')

        def f2(x):
            pass
            # time.sleep(0.001)
            print('print', x)

        print(1111)

        t1 = time.time()
        pool = AsyncPoolExecutor(20)
        # pool = ThreadPoolExecutor(200)  # Coroutines cannot be run using a thread pool, otherwise print won't execute at all. For an async function f(x), you get a coroutine, which must be further scheduled as a task in the loop to run.
        for i in range(1, 501):
            print('submitting', i)
            pool.submit(f, i)
        # time.sleep(5)
        # pool.submit(f, 'hi')
        # pool.submit(f, 'hi2')
        # pool.submit(f, 'hi3')
        # print(2222)
        pool.shutdown()
        print(time.time() - t1)


    test_async_pool_executor()
    # test_async_producer_consumer()

    print(sys.version_info)
