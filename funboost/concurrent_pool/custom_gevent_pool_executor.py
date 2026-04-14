# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/7/2 14:11
import atexit
import time
import warnings
# from collections import Callable
from typing import Callable
import threading
from funboost.core.lazy_impoter import GeventImporter

# from nb_log import LoggerMixin, nb_print, LogManager
from funboost.concurrent_pool import FunboostBaseConcurrentPool
from funboost.core.loggers import get_funboost_file_logger, FunboostFileLoggerMixin


# print('gevent imported')

def check_gevent_monkey_patch(raise_exc=True):
    try:
        if not GeventImporter().monkey.is_module_patched('socket'):  # Pick any flag to check
            if raise_exc:
                warnings.warn(f'Detected that gevent monkey patch is not applied. Please add "import gevent.monkey;gevent.monkey.patch_all()" at the first line of your entry script.')
                raise Exception(f'Detected that gevent monkey patch is not applied. Please add "import gevent.monkey;gevent.monkey.patch_all()" at the first line of your entry script.')
        else:
            return 1
    except ModuleNotFoundError:
        if raise_exc:
            warnings.warn(f'Detected that gevent monkey patch is not applied. Please add "import gevent.monkey;gevent.monkey.patch_all()" at the first line of your entry script.')
            raise Exception(f'Detected that gevent monkey patch is not applied. Please add "import gevent.monkey;gevent.monkey.patch_all()" at the first line of your entry script.')


logger_gevent_timeout_deco = get_funboost_file_logger('gevent_timeout_deco')


def gevent_timeout_deco(timeout_t):
    def _gevent_timeout_deco(f):
        def __gevent_timeout_deceo(*args, **kwargs):
            timeout = GeventImporter().gevent.Timeout(timeout_t, )
            timeout.start()
            result = None
            try:
                result = f(*args, **kwargs)
            except GeventImporter().gevent.Timeout as t:
                logger_gevent_timeout_deco.error(f'Function {f} exceeded {timeout_t} seconds')
                if t is not timeout:
                    print(t)
                    # raise  # not my timeout
            finally:
                timeout.close()
                return result

        return __gevent_timeout_deceo

    return _gevent_timeout_deco


def get_gevent_pool_executor(size=None, greenlet_class=None):
    class GeventPoolExecutor(GeventImporter().gevent_pool.Pool, FunboostBaseConcurrentPool):
        def __init__(self, size2=None, greenlet_class2=None):
            check_gevent_monkey_patch()  # Checked in basecomer.py.
            super().__init__(size2, greenlet_class2)
            atexit.register(self.shutdown)

        def submit(self, *args, **kwargs):
            self.spawn(*args, **kwargs)

        def shutdown(self):
            self.join()

    return GeventPoolExecutor(size, greenlet_class)


class GeventPoolExecutor2(FunboostFileLoggerMixin, FunboostBaseConcurrentPool):
    def __init__(self, max_works, ):
        self._q = GeventImporter().JoinableQueue(maxsize=max_works)
        # self._q = Queue(maxsize=max_works)
        for _ in range(max_works):
            GeventImporter().gevent.spawn(self.__worker)
        # atexit.register(self.__atexit)
        self._q.join(timeout=100)

    def __worker(self):
        while True:
            fn, args, kwargs = self._q.get()
            try:
                fn(*args, **kwargs)
            except BaseException as exc:
                self.logger.exception(f'Error occurred in function {fn.__name__}, reason: {type(exc)} {exc} ')
            finally:
                pass
                self._q.task_done()

    def submit(self, fn: Callable, *args, **kwargs):
        self._q.put((fn, args, kwargs))

    def __atexit(self):
        self.logger.critical('About to exit the program.')
        self._q.join()


class GeventPoolExecutor3(FunboostFileLoggerMixin, FunboostBaseConcurrentPool):
    def __init__(self, max_works, ):
        self._q = GeventImporter().gevent.queue.Queue(max_works)
        self.g_list = []
        for _ in range(max_works):
            self.g_list.append(GeventImporter().gevent.spawn(self.__worker))
        atexit.register(self.__atexit)

    def __worker(self):
        while True:
            fn, args, kwargs = self._q.get()
            try:
                fn(*args, **kwargs)
            except BaseException as exc:
                self.logger.exception(f'Error occurred in function {fn.__name__}, reason: {type(exc)} {exc} ')

    def submit(self, fn: Callable, *args, **kwargs):
        self._q.put((fn, args, kwargs))

    def joinall(self):
        GeventImporter().gevent.joinall(self.g_list)

    def joinall_in_new_thread(self):
        threading.Thread(target=self.joinall)

    def __atexit(self):
        self.logger.critical('About to exit the program.')
        self.joinall()


if __name__ == '__main__':
    GeventImporter().monkey.patch_all(thread=False)


    def f2(x):

        time.sleep(3)
        print(x * 10)


    pool = GeventPoolExecutor3(40)

    for i in range(20):
        time.sleep(0.1)
        print(f'submitting {i}')
        pool.submit(gevent_timeout_deco(8)(f2), i)
    # pool.joinall_in_new_thread()
    print(66666666)
