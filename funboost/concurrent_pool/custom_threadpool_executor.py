"""
The most powerful Python thread pool.

The most intelligent thread pool that can automatically adjust thread count in real-time. This thread pool has a
duck-type relationship with the official concurrent.futures thread pool, so you can replace it by simply changing
the class name or using import-as.
Compared to the official thread pool, it has 4 innovative features or improvements:

1. It can not only scale up but also automatically scale down (the official built-in ThreadPoolExecutor lacks this
   feature. This concept is similar to Java's ThreadPoolExecutor KeepAliveTime parameter).
   For example, with a 1000-thread pool, if you submit tasks at high frequency for one minute, the pool scales up to
   max threads. But if for the next 7-8 hours only 1-2 tasks are submitted per minute, the official pool maintains
   1000 threads, while this pool automatically scales down. It uses KeepAliveTime to determine when to scale down.

2. Very conservative in creating new threads. For example, with a max 100-thread pool, if a task is submitted every
   2 seconds and each function only takes 1 second, only 1 thread is needed. The official pool would keep increasing
   to the max thread count, but this pool does not.

3. The task queue is changed to a bounded queue.

4. When a function error occurs in this pool, it directly displays the error. The official pool would not show errors;
   e.g., writing 1/0 in a function would still not display the error.

This implements submit and also future-related functionality, making it a true drop-in replacement for the built-in
ThreadPoolExecutor.

You can add time.sleep in various places to verify the auto-scaling functionality from points 1 and 2.
"""
import logging

import os
import atexit
import queue
import sys
import threading
import time
import weakref

from funboost.concurrent_pool import FunboostBaseConcurrentPool
from nb_log import LoggerLevelSetterMixin
from funboost.core.loggers import FunboostFileLoggerMixin,get_funboost_file_logger
from concurrent.futures import Executor, Future



_shutdown = False
_threads_queues = weakref.WeakKeyDictionary()


def check_not_monkey():
    from funboost.concurrent_pool.custom_evenlet_pool_executor import check_evenlet_monkey_patch
    from funboost.concurrent_pool.custom_gevent_pool_executor import check_gevent_monkey_patch
    if check_gevent_monkey_patch(raise_exc=False):
        raise Exception('When using multi-thread mode, please do not apply gevent monkey patch')
    if check_evenlet_monkey_patch(raise_exc=False):
        raise Exception('When using multi-thread mode, please do not apply eventlet monkey patch')


def _python_exit():
    global _shutdown
    _shutdown = True
    items = list(_threads_queues.items())
    for t, q in items:
        q.put(None)
    for t, q in items:
        t.join()


atexit.register(_python_exit)


class _WorkItem(FunboostFileLoggerMixin):
    def __init__(self, future, fn, args, kwargs):
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        # noinspection PyBroadException
        if not self.future.set_running_or_notify_cancel():
            return
        try:
            result = self.fn(*self.args, **self.kwargs)
        except BaseException as exc:
            self.logger.exception(f'Error occurred in function {self.fn}, reason: {type(exc)} {exc} ')
            self.future.set_exception(exc)
            # Break a reference cycle with the exception 'exc'
            self = None  # noqa
        else:
            self.future.set_result(result)

    def __str__(self):
        return f'{(self.fn.__name__, self.args, self.kwargs)}'


def set_threadpool_executor_shrinkable(min_works=1, keep_alive_time=5):
    ThreadPoolExecutorShrinkAble.MIN_WORKERS = min_works
    ThreadPoolExecutorShrinkAble.KEEP_ALIVE_TIME = keep_alive_time


class ThreadPoolExecutorShrinkAble(Executor, FunboostFileLoggerMixin, LoggerLevelSetterMixin,FunboostBaseConcurrentPool):
    # To maintain full duck-type compatibility with the official ThreadPoolExecutor, parameters are hardcoded.
    # It's recommended to use monkey patching to modify these two parameters, to keep the API consistent with built-in concurrent.futures.
    # MIN_WORKERS = 5   # Minimum can be set to 0, representing the minimum number of threads to keep on standby regardless of idle time.
    # KEEP_ALIVE_TIME = 60  # This parameter means: how long a thread waits via queue.get(block=True, timeout=KEEP_ALIVE_TIME) before terminating if no task arrives.

    MIN_WORKERS = 1
    KEEP_ALIVE_TIME = 60
    THREAD_USE_DAEMON = True

    def __init__(self, max_workers: int = None, thread_name_prefix='',work_queue_maxsize=10):
        """
        Maintains compatibility with the official concurrent.futures.ThreadPoolExecutor and the modified
        BoundedThreadPoolExecutor, keeping parameter names and count consistent.
        :param max_workers:
        :param thread_name_prefix:
        """
        # print(max_workers)
        self._max_workers = max_workers or (os.cpu_count() or 1) * 5
        self._thread_name_prefix = thread_name_prefix
        # print(self._max_workers)
        # self.work_queue = self._work_queue = queue.Queue(self._max_workers or 10)
        self.work_queue = self._work_queue = queue.Queue(work_queue_maxsize)
        # self._threads = set()
        self._threads = weakref.WeakSet()
        self._lock_compute_threads_free_count = threading.Lock()
        self.threads_free_count = 0
        self._shutdown = False
        self._shutdown_lock = threading.Lock()
        self.pool_ident = id(self)

    def _change_threads_free_count(self, change_num):
        with self._lock_compute_threads_free_count:
            self.threads_free_count += change_num

    def submit(self, func, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('Cannot add new tasks to the thread pool')
            f = Future()
            w = _WorkItem(f, func, args, kwargs)
            self.work_queue.put(w)
            self._adjust_thread_count()
            return f

    def _adjust_thread_count(self):
        # print(self.threads_free_count, self.MIN_WORKERS, len(self._threads), self._max_workers)
        if self.threads_free_count <= self.MIN_WORKERS and len(self._threads) < self._max_workers:
            t = _CustomThread(self).set_log_level(self.logger.level)
            t.daemon = self.THREAD_USE_DAEMON
            t.start()
            self._threads.add(t)
            _threads_queues[t] = self._work_queue

    def shutdown(self, wait=True):  # noqa
        with self._shutdown_lock:
            self._shutdown = True
            self.work_queue.put(None)
        if wait:
            for t in self._threads:
                t.join()




# Both names are valid, maintaining backward compatibility with the old name (CustomThreadpoolExecutor), but the new name (ThreadPoolExecutorShrinkAble) better expresses its meaning.
CustomThreadpoolExecutor = CustomThreadPoolExecutor = ThreadPoolExecutorShrinkAble


class ThreadPoolExecutorShrinkAbleNonDaemon(ThreadPoolExecutorShrinkAble):
    """This is ideal for apscheduler's ThreadPoolExecutorForAps. The threads in this pool are non-daemon threads.

    This prevents the error that occurs when child threads are still running but the main thread exits:
    raise RuntimeError('cannot schedule new futures after ' RuntimeError: cannot schedule new futures after interpreter shutdown

    Previously, background scheduler used daemon threads in the thread pool. To avoid 'cannot schedule new futures after',
    users had to manually add ctrl_c_recv() or while 1: time.sleep(10) in the main thread to prevent it from exiting,
    which was inconvenient for users.
    """
    MIN_WORKERS = 0
    THREAD_USE_DAEMON = False



# noinspection PyProtectedMember
class _CustomThread(threading.Thread, FunboostFileLoggerMixin, LoggerLevelSetterMixin):
    _lock_for_judge_threads_free_count = threading.Lock()

    def __init__(self, executorx: ThreadPoolExecutorShrinkAble):
        super().__init__()
        self._executorx = executorx

    def _remove_thread(self, stop_resson=''):
        # noinspection PyUnresolvedReferences
        self.logger.debug(f'Stopping thread {self._ident}, trigger condition: {stop_resson} ')
        self._executorx._change_threads_free_count(-1)
        self._executorx._threads.remove(self)
        _threads_queues.pop(self)

    # noinspection PyProtectedMember
    def run(self):
        # noinspection PyUnresolvedReferences
        # print(logging.getLogger(None).level,logging.getLogger(None).handlers)
        # print(self.logger.level)
        # print(self.logger.handlers)
        self.logger.debug(f'New thread started {self._ident} ')
        self._executorx._change_threads_free_count(1)
        while True:
            try:
                work_item = self._executorx.work_queue.get(block=True, timeout=self._executorx.KEEP_ALIVE_TIME)
            except queue.Empty:
                # continue
                # self._remove_thread()
                with self._lock_for_judge_threads_free_count:
                    if self._executorx.threads_free_count > self._executorx.MIN_WORKERS:
                        self._remove_thread(
                            f'Thread {self.ident} in pool {self._executorx.pool_ident} has had no tasks for {self._executorx.KEEP_ALIVE_TIME} seconds. '
                            f'Number of idle threads in pool: {self._executorx.threads_free_count}, exceeds minimum core count {self._executorx.MIN_WORKERS}')
                        break  # Exit while loop, i.e., terminate. This is where the thread actually ends; _remove_thread is just a name, it doesn't destroy the thread.
                    else:
                        continue

            if work_item is not None:
                self._executorx._change_threads_free_count(-1)
                work_item.run()
                del work_item
                self._executorx._change_threads_free_count(1)
                continue
            if _shutdown or self._executorx._shutdown:
                self._executorx.work_queue.put(None)
                break


process_name_set = set()
logger_show_current_threads_num = get_funboost_file_logger('show_current_threads_num',formatter_template=5, do_not_use_color_handler=False)


def show_current_threads_num(sleep_time=600, process_name='', block=False, daemon=True):
    """Start a separate thread to print the thread count every N seconds. This is unrelated to the shrinkable thread pool implementation."""
    process_name = sys.argv[0] if process_name == '' else process_name

    def _show_current_threads_num():
        while True:
            # logger_show_current_threads_num.info(f'{process_name} process concurrency count -->  {threading.active_count()}')
            # nb_print(f'  {process_name} {os.getpid()} process thread count -->  {threading.active_count()}')
            logger_show_current_threads_num.info(
                f'  {process_name} {os.getpid()} process total thread count -->  {threading.active_count()}')
            time.sleep(sleep_time)

    if process_name not in process_name_set:
        if block:
            _show_current_threads_num()
        else:
            t = threading.Thread(target=_show_current_threads_num, daemon=daemon)
            t.start()
        process_name_set.add(process_name)


def get_current_threads_num():
    return threading.active_count()


if __name__ == '__main__':
    show_current_threads_num(sleep_time=5)


    def f1(a):
        time.sleep(0.2)  # Modify this number to test the thread count adjustment feature.
        print(f'{a} .......')
        return a * 10
        # raise Exception('Throw an error for testing')  # The official pool won't show function errors, making you think your code is fine.


    pool = ThreadPoolExecutorShrinkAble(1)
    # pool = ThreadPoolExecutor(200)  # For comparison testing with the official built-in pool

    for i in range(30):
        time.sleep(0.1)  # 这里的间隔时间模拟，当任务来临不密集，只需要少量线程就能搞定f1了，因为f1的消耗时间短，
        # 不需要开那么多线程，CustomThreadPoolExecutor比ThreadPoolExecutor 优势之一。
        futurex = pool.submit(f1, i)
        # print(futurex.result())

    # 1/下面测试阻塞主线程退出的情况。注释掉可以测主线程退出的情况。
    # 2/此代码可以证明，在一段时间后，连续长时间没任务，官方线程池的线程数目还是保持在最大数量了。而此线程池会自动缩小，实现了java线程池的keppalivetime功能。
    time.sleep(1000000)
