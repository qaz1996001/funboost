"""
A thread pool that can automatically adjust thread count in real-time.
Improvements over the official ThreadPoolExecutor:
1. Bounded queue
2. Real-time thread count adjustment - threads are closed when there are few tasks. The official ThreadPoolExecutor
   can only scale up when busy but doesn't close threads when idle. This pool implements the keepAliveTime parameter
   functionality from Java's ThreadPoolExecutor. Linux systems can only handle a limited total number of threads,
   typically under 20,000.
3. Very intelligent and conservative thread creation. For example, with a pool size of 500, if the function takes
   only 0.1 seconds and a task arrives every 2 seconds, 1 thread is sufficient. The official pool would keep growing
   to 500, which is not intelligent.

This thread pool is the framework's default threading pool. If no concurrency mode is set, this one is used.

This implements submit but does not implement future-related functionality.
"""

import atexit
import queue
import sys
import threading
import time
import weakref

from nb_log import LoggerMixin, nb_print, LoggerLevelSetterMixin, LogManager
from funboost.concurrent_pool.custom_evenlet_pool_executor import check_evenlet_monkey_patch
from funboost.concurrent_pool.custom_gevent_pool_executor import check_gevent_monkey_patch

_shutdown = False
_threads_queues = weakref.WeakKeyDictionary()


def _python_exit():
    global _shutdown
    _shutdown = True
    items = list(_threads_queues.items())
    for t, q in items:
        q.put(None)
    for t, q in items:
        t.join()


atexit.register(_python_exit)


class _WorkItem(LoggerMixin):
    def __init__(self, fn, args, kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        # noinspection PyBroadException
        try:
            self.fn(*self.args, **self.kwargs)
        except BaseException as exc:
            self.logger.exception(f'Error occurred in function {self.fn.__name__}, reason: {type(exc)} {exc} ')

    def __str__(self):
        return f'{(self.fn.__name__, self.args, self.kwargs)}'


def check_not_monkey():
    if check_gevent_monkey_patch(raise_exc=False):
        raise Exception('Please do not apply gevent monkey patch')
    if check_evenlet_monkey_patch(raise_exc=False):
        raise Exception('Please do not apply eventlet monkey patch')


class CustomThreadPoolExecutor(LoggerMixin, LoggerLevelSetterMixin):
    def __init__(self, max_workers=None, thread_name_prefix=''):
        """
        Maintains compatibility with the official concurrent.futures.ThreadPoolExecutor and the modified
        BoundedThreadPoolExecutor, keeping parameter names and count consistent.
        :param max_workers:
        :param thread_name_prefix:
        """
        self._max_workers = max_workers or 4
        self._min_workers = 5  # This corresponds to Java's ThreadPoolExecutor corePoolSize. To keep the pool's public methods consistent with Python's built-in concurrent.futures.ThreadPoolExecutor, no additional init params are added; hardcoded to 5.
        self._thread_name_prefix = thread_name_prefix
        self.work_queue = queue.Queue(max_workers)
        # self._threads = set()
        self._threads = weakref.WeakSet()
        self._lock_compute_threads_free_count = threading.Lock()
        self.threads_free_count = 0
        self._shutdown = False
        self._shutdown_lock = threading.Lock()
        # self.logger.setLevel(20)

    def set_min_workers(self, min_workers=10):
        self._min_workers = min_workers
        return self

    def change_threads_free_count(self, change_num):
        with self._lock_compute_threads_free_count:
            self.threads_free_count += change_num

    def submit(self, func, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('Cannot add new tasks to the thread pool')
        self.work_queue.put(_WorkItem(func, args, kwargs))
        self._adjust_thread_count()

    def _adjust_thread_count(self):
        # if len(self._threads) < self._threads_num:
        # self.logger.debug((self.threads_free_count, len(self._threads), len(_threads_queues), get_current_threads_num()))
        if self.threads_free_count < self._min_workers and len(self._threads) < self._max_workers:
            # t = threading.Thread(target=_work,
            #                      args=(self._work_queue,self))
            t = _CustomThread(self).set_log_level(self.logger.level)
            t.setDaemon(True)
            t.start()
            self._threads.add(t)
            _threads_queues[t] = self.work_queue

    def shutdown(self, wait=True):
        with self._shutdown_lock:
            self._shutdown = True
            self.work_queue.put(None)
        if wait:
            for t in self._threads:
                t.join()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown(wait=True)
        return False


class _CustomThread(threading.Thread, LoggerMixin, LoggerLevelSetterMixin):
    _lock_for_judge_threads_free_count = threading.Lock()

    def __init__(self, executorx: CustomThreadPoolExecutor):
        super().__init__()
        self._executorx = executorx
        self._run_times = 0

    # noinspection PyProtectedMember
    def _remove_thread(self, stop_resson=''):
        # noinspection PyUnresolvedReferences
        self.logger.debug(f'Stopping thread {self._ident}, trigger condition: {stop_resson} ')
        self._executorx.change_threads_free_count(-1)
        self._executorx._threads.remove(self)
        _threads_queues.pop(self)

    # noinspection PyProtectedMember
    def run(self):
        # noinspection PyUnresolvedReferences
        self.logger.debug(f'New thread started {self._ident} ')
        self._executorx.change_threads_free_count(1)
        while True:
            try:
                work_item = self._executorx.work_queue.get(block=True, timeout=60)
            except queue.Empty:
                with self._lock_for_judge_threads_free_count:
                    if self._executorx.threads_free_count > self._executorx._min_workers:
                        self._remove_thread(f'Current thread has had no tasks for 60 seconds. Number of idle threads in pool: {self._executorx.threads_free_count}, exceeds the specified count {self._executorx._min_workers}')
                        break  # Exit while loop, i.e., terminate. This is where the thread actually ends; _remove_thread is just a name, it doesn't destroy the thread.
                    else:
                        continue

            # nb_print(work_item)
            if work_item is not None:
                self._executorx.change_threads_free_count(-1)
                work_item.run()
                del work_item
                self._executorx.change_threads_free_count(1)
                continue
            if _shutdown or self._executorx._shutdown:
                self._executorx.work_queue.put(None)
                break


process_name_set = set()
logger_show_current_threads_num = LogManager('show_current_threads_num').get_logger_and_add_handlers(
    formatter_template=5, log_filename='show_current_threads_num.log', do_not_use_color_handler=True)


def show_current_threads_num(sleep_time=60, process_name='', block=False):
    process_name = sys.argv[0] if process_name == '' else process_name

    def _show_current_threads_num():
        while True:
            # logger_show_current_threads_num.info(f'{process_name} process concurrency count -->  {threading.active_count()}')
            nb_print(f'{process_name} process thread count -->  {threading.active_count()}')
            time.sleep(sleep_time)

    if process_name not in process_name_set:
        if block:
            _show_current_threads_num()
        else:
            t = threading.Thread(target=_show_current_threads_num, daemon=True)
            t.start()
        process_name_set.add(process_name)


def get_current_threads_num():
    return threading.active_count()


if __name__ == '__main__':
    from funboost.utils import decorators
    from funboost.concurrent_pool.bounded_threadpoolexcutor import BoundedThreadPoolExecutor


    # @decorators.keep_circulating(1)
    def f1(a):
        time.sleep(0.2)
        nb_print(f'{a} .......')
        # raise Exception('Throw an error for testing')


    # show_current_threads_num()
    pool = CustomThreadPoolExecutor(200).set_log_level(10).set_min_workers()
    # pool = BoundedThreadPoolExecutor(200)   # For comparison testing with the original BoundedThreadPoolExecutor
    show_current_threads_num(sleep_time=5)
    for i in range(300):
        time.sleep(0.3)  # This interval simulates infrequent task arrival; only a few threads are needed since f1 runs quickly. No need for so many threads - one advantage of CustomThreadPoolExecutor over BoundedThreadPoolExecutor.
        pool.submit(f1, str(i))

    nb_print(6666)
    # pool.shutdown(wait=True)
    pool.submit(f1, 'yyyy')

    # Below tests blocking the main thread from exiting. Comment out to test main thread exit behavior.
    while True:
        time.sleep(10)
