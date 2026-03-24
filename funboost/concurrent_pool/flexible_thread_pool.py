"""
A simpler flexible thread pool than ThreadPoolExecutorShrinkAble. Completely built from scratch.

This thread pool's submit has no return value, does not return a future object, and does not support the map method.

This thread pool's performance is 200% better than concurrent.futures.ThreadPoolExecutor.

Also supports concurrent execution of async def functions.
"""

import asyncio
import inspect
import os
import queue
import threading
from functools import wraps

from funboost.concurrent_pool import FunboostBaseConcurrentPool
from funboost.core.loggers import FunboostFileLoggerMixin, LoggerLevelSetterMixin, FunboostMetaTypeFileLogger


class FlexibleThreadPool(FunboostFileLoggerMixin, LoggerLevelSetterMixin, FunboostBaseConcurrentPool):
    KEEP_ALIVE_TIME = 10
    MIN_WORKERS = 1

    def __init__(self, max_workers: int = None,work_queue_maxsize=10):
        self.work_queue = queue.Queue(work_queue_maxsize)
        self.max_workers = max_workers
        self._threads_num = 0
        self.threads_free_count = 0
        self._lock_compute_start_thread = threading.Lock()
        self._lock_compute_threads_free_count = threading.Lock()
        self._lock_for_adjust_thread = threading.Lock()
        self._lock_for_judge_threads_free_count = threading.Lock()
        self.pool_ident = id(self)
        # self.asyncio_loop = asyncio.new_event_loop()

    def _change_threads_free_count(self, change_num):
        with self._lock_compute_threads_free_count:
            self.threads_free_count += change_num

    def _change_threads_start_count(self, change_num):
        with self._lock_compute_start_thread:
            self._threads_num += change_num

    def submit(self, func, *args, **kwargs):
        self.work_queue.put([func, args, kwargs])
        with self._lock_for_adjust_thread:
            if self.threads_free_count <= self.MIN_WORKERS and self._threads_num < self.max_workers:
                _KeepAliveTimeThread(self).start()


class FlexibleThreadPoolMinWorkers0(FlexibleThreadPool):
    MIN_WORKERS = 0


def run_sync_or_async_fun000(func, *args, **kwargs):
    """This approach makes the computer very laggy, not viable"""
    fun_is_asyncio = inspect.iscoroutinefunction(func)
    if fun_is_asyncio:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            loop.close()
    else:
        return func(*args, **kwargs)


tl = threading.local()


def _get_thread_local_loop() -> asyncio.AbstractEventLoop:
    if not hasattr(tl, 'asyncio_loop'):
        tl.asyncio_loop = asyncio.new_event_loop()
    return tl.asyncio_loop


def run_sync_or_async_fun(func, *args, **kwargs):
    fun_is_asyncio = inspect.iscoroutinefunction(func)
    if fun_is_asyncio:
        loop = _get_thread_local_loop()
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            pass
            # loop.close()
    else:
        return func(*args, **kwargs)


def sync_or_async_fun_deco(func):
    @wraps(func)
    def _inner(*args, **kwargs):
        return run_sync_or_async_fun(func, *args, **kwargs)

    return _inner


# noinspection PyProtectedMember
class _KeepAliveTimeThread(threading.Thread, metaclass=FunboostMetaTypeFileLogger):
    def __init__(self, thread_pool: FlexibleThreadPool):
        super().__init__()
        self.pool = thread_pool

    def run(self) -> None:
        # You can set LogManager('_KeepAliveTimeThread').preset_log_level(logging.INFO) to suppress the messages below, see docs section 6.17.b
        self.logger.debug(f'New thread started {self.ident} ')
        self.pool._change_threads_free_count(1)
        self.pool._change_threads_start_count(1)
        while 1:
            try:
                func, args, kwargs = self.pool.work_queue.get(block=True, timeout=self.pool.KEEP_ALIVE_TIME)
            except queue.Empty:
                with self.pool._lock_for_judge_threads_free_count:
                    # print(self.pool.threads_free_count)
                    if self.pool.threads_free_count > self.pool.MIN_WORKERS:
                  
                        # If you don't want this log message and are not interested in funboost's adaptive thread pool, set FUNBOOST_PROMPT_LOG_LEVEL = logging.INFO in FunboostCommonConfig in your funboost_config.py
                        self.logger.debug(f'Stopping thread {self._ident}, trigger: thread {self.ident} in pool {self.pool.pool_ident} has had no tasks for {self.pool.KEEP_ALIVE_TIME} seconds. Idle thread count: {self.pool.threads_free_count}, exceeds minimum core count {self.pool.MIN_WORKERS}')  # noqa
                        self.pool._change_threads_free_count(-1)
                        self.pool._change_threads_start_count(-1)
                        break  # Exit while loop, i.e., terminate.
                    else:
                        continue
            self.pool._change_threads_free_count(-1)
            try:
                fun = sync_or_async_fun_deco(func)
                fun(*args, **kwargs)
            except BaseException as exc:
                self.logger.exception(f'Error occurred in function {func}, reason: {type(exc)} {exc} ')
            self.pool._change_threads_free_count(1)





if __name__ == '__main__':
    import time
    from concurrent.futures import ThreadPoolExecutor
    from custom_threadpool_executor import ThreadPoolExecutorShrinkAble


    def testf(x):
        # time.sleep(10)
        if x % 10000 == 0:
            print(x)


    async def aiotestf(x):
        # await asyncio.sleep(1)
        if x % 10 == 0 or 1:
            print(x)
        return x * 2


    pool = FlexibleThreadPool(100)
    # pool = ThreadPoolExecutor(100)
    # pool = ThreadPoolExecutorShrinkAble(100)

    for i in range(20000):
        # time.sleep(2)
        pool.submit(aiotestf, i)

    # for i in range(100000):
    #     pool.submit(testf, i)

    # while 1:
    #     time.sleep(1000)
    # loop.run_forever()
