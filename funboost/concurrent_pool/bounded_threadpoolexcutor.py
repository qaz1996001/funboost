# coding=utf-8
"""
A ThreadPoolExecutor with a bounded task queue
that directly captures and logs errors.
"""
from functools import wraps
import queue
from concurrent.futures import ThreadPoolExecutor, Future
# noinspection PyProtectedMember
from concurrent.futures.thread import _WorkItem  # noqa

from funboost.concurrent_pool import FunboostBaseConcurrentPool
from funboost.core.loggers import get_funboost_file_logger

logger = get_funboost_file_logger('BoundedThreadPoolExecutor')


def _deco(f):
    @wraps(f)
    def __deco(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BaseException as e:
            logger.exception(e)

    return __deco if f is not None else f


class BoundedThreadPoolExecutor(ThreadPoolExecutor,FunboostBaseConcurrentPool ):
    def __init__(self, max_workers=None, thread_name_prefix=''):
        ThreadPoolExecutor.__init__(self, max_workers, thread_name_prefix)
        self._work_queue = queue.Queue(max_workers * 2)

    def submit(self, fn, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')
            f = Future()
            fn_deco = _deco(fn)
            w = _WorkItem(f, fn_deco, args, kwargs)
            self._work_queue.put(w)
            self._adjust_thread_count()
            return f


if __name__ == '__main__':
    def fun():
        print(1 / 0.2)

    # With the official thread pool, no error would be shown, making you think the code has no issues.
    with BoundedThreadPoolExecutor(10) as pool:
        for i in range(20):
            pool.submit(fun)
