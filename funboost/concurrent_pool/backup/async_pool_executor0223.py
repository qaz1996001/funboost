import atexit
import asyncio
import threading
import time
import traceback
from threading import Thread
import nb_log  # noqa

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


class AsyncPoolExecutor2:
    def __init__(self, size, loop=None):
        self._size = size
        self.loop = loop or asyncio.new_event_loop()
        self._sem = asyncio.Semaphore(self._size, loop=self.loop)
        # atexit.register(self.shutdown)
        Thread(target=self._start_loop_in_new_thread).start()

    def submit(self, func, *args, **kwargs):
        while self._sem.locked():
            time.sleep(0.001)
        asyncio.run_coroutine_threadsafe(self._run_func(func, *args, **kwargs), self.loop)

    async def _run_func(self, func, *args, **kwargs):
        async with self._sem:
            result = await func(*args, **kwargs)
            return result

    def _start_loop_in_new_thread(self, ):
        self.loop.run_forever()

    def shutdown(self):
        self.loop.stop()
        self.loop.close()


class AsyncPoolExecutor(nb_log.LoggerMixin):
    """
    Makes the API similar to a thread pool. The best performance approach would be to make submit an async def too,
    running production and consumption in the same thread and same loop, but this would break call chain compatibility,
    making the calling pattern incompatible with thread pools.
    """

    def __init__(self, size, loop=None):
        """

        :param size: Number of coroutine tasks to run concurrently.
        :param loop:
        """
        self._size = size
        self.loop = loop or asyncio.new_event_loop()
        self._sem = asyncio.Semaphore(self._size, )
        self._queue = asyncio.Queue(maxsize=size, )
        self._lock = threading.Lock()
        t = Thread(target=self._start_loop_in_new_thread,daemon=True)
        # t.setDaemon(True)  # Setting daemon thread allows atexit to trigger, enabling automatic program exit without manually calling shutdown
        t.start()
        self._can_be_closed_flag = False
        atexit.register(self.shutdown)

        self._event = threading.Event()
        # print(self._event.is_set())
        self._event.set()

    def submit000(self, func, *args, **kwargs):
        # This performs 3x faster than the approach below using run_coroutine_threadsafe + result return.
        with self._lock:
            while 1:
                if not self._queue.full():
                    self.loop.call_soon_threadsafe(self._queue.put_nowait, (func, args, kwargs))
                    break
                else:
                    time.sleep(0.01)

    def submit(self, func, *args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(self._produce(func, *args, **kwargs), self.loop)  # The run_coroutine_threadsafe method also has drawbacks, consuming significant performance.
        future.result()  # Prevents submitting too fast; blocks submit when queue is full.

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
                traceback.print_exc()
            # self._queue.task_done()

    async def __run(self):
        for _ in range(self._size):
            asyncio.ensure_future(self._consume())

    def _start_loop_in_new_thread(self, ):
        # self._loop.run_until_complete(self.__run())  # This approach also works.
        # self._loop.run_forever()

        # asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(asyncio.wait([self.loop.create_task(self._consume()) for _ in range(self._size)],))
        self._can_be_closed_flag = True

    def shutdown(self):
        if self.loop.is_running():  # This may be triggered by atexit register or manually called by the user; need to check to avoid closing twice.
            for i in range(self._size):
                self.submit(f'stop{i}', )
            while not self._can_be_closed_flag:
                time.sleep(0.1)
            self.loop.stop()
            self.loop.close()
            print('Closing loop')


class AsyncProducerConsumer:
    """
    Reference: https://asyncio.readthedocs.io/en/latest/producer_consumer.html official documentation.
    A simple producer/consumer example, using an asyncio.Queue:
    """

    """
    Produce and consume simultaneously. This framework doesn't use this class because it requires production and
    consumption to be in the same thread, making it inconvenient to refactor the existing synchronous framework code.
    """

    def __init__(self, items, concurrent_num=200, consume_fun_specify=None):
        """

        :param items: List of parameters to consume
        :param concurrent_num: Concurrency count
        :param consume_fun_specify: Specified async consumer function object. If not specified, inherit and override consume_fun.
        """
        self.queue = asyncio.Queue()
        self.items = items
        self.consumer_params.concurrent_num = concurrent_num
        self.consume_fun_specify = consume_fun_specify

    async def produce(self):
        for item in self.items:
            await self.queue.put(item)

    async def consume(self):
        while True:
            # wait for an item from the producer
            item = await self.queue.get()
            # process the item
            # print('consuming {}...'.format(item))
            # simulate i/o operation using sleep
            try:
                if self.consume_fun_specify:
                    await self.consume_fun_specify(item)
                else:
                    await self.consume_fun(item)
            except BaseException as e:
                print(e)

            # Notify the queue that the item has been processed
            self.queue.task_done()

    @staticmethod
    async def consume_fun(item):
        """
        Either inherit this class and override this method, or specify consume_fun_specify as an async function during initialization.
        :param item:
        :return:
        """
        print(item, 'Please override the consume_fun method')
        await asyncio.sleep(1)

    async def __run(self):
        # schedule the consumer
        tasks = []
        for _ in range(self.consumer_params.concurrent_num):
            task = asyncio.ensure_future(self.consume())
            tasks.append(task)
        # run the producer and wait for completion
        await self.produce()
        # wait until the consumer has processed all items
        await self.queue.join()
        # the consumer is still awaiting for an item, cancel it
        for task in tasks:
            task.cancel()

    def start_run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__run())
        # loop.close()


if __name__ == '__main__':
    def test_async_pool_executor():
        from funboost.concurrent_pool import CustomThreadPoolExecutor as ThreadPoolExecutor
        # from concurrent.futures.thread import ThreadPoolExecutor
        # noinspection PyUnusedLocal
        async def f(x):
            # await asyncio.sleep(0.1)
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


    async def _my_fun(item):
        print('hehe', item)
        # await asyncio.sleep(1)


    def test_async_producer_consumer():
        AsyncProducerConsumer([i for i in range(100000)], concurrent_num=200, consume_fun_specify=_my_fun).start_run()
        print('over')


    test_async_pool_executor()
    # test_async_producer_consumer()
