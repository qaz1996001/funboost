"""
fixed_thread_pool.py - A fixed-size non-intelligent thread pool, the simplest brute-force implementation that anyone can write.
The downside is that the code won't exit automatically because each thread in the pool runs a while-loop as a non-daemon thread
and cannot automatically determine when the code should exit.
If your code is long-running and doesn't need to exit, this type of thread pool works well.
"""

import threading
import traceback
from queue import Queue
# import nb_log
from funboost.concurrent_pool import FunboostBaseConcurrentPool
from funboost.core.loggers import FunboostFileLoggerMixin


class FixedThreadPool(FunboostFileLoggerMixin,FunboostBaseConcurrentPool):
    def __init__(self, max_workers: int = 8):
        self._max_workers = max_workers
        self._work_queue = Queue(maxsize=10)
        self._start_thrads()

    def submit(self, func, *args, **kwargs):
        self._work_queue.put([func, args, kwargs])

    def _forever_fun(self):
        while True:
            func, args, kwargs = self._work_queue.get()
            try:
                func(*args, **kwargs)
            except BaseException as e:
                self.logger.error(f'func:{func}, args:{args}, kwargs:{kwargs} exc_type:{type(e)}  traceback_exc:{traceback.format_exc()}')

    def _start_thrads(self):
        for i in range(self._max_workers):
            threading.Thread(target=self._forever_fun).start()


if __name__ == '__main__':
    def f3(x):
        # time.sleep(1)
        # 1 / 0
        if x % 10000 == 0:
            print(x)


    pool = FixedThreadPool(100)
    for j in range(10):
        pool.submit(f3, j)
