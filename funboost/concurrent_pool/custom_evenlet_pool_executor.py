# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/7/3 10:35
import atexit
import time
import warnings
# from eventlet import greenpool, monkey_patch, patcher, Timeout

from funboost.concurrent_pool import FunboostBaseConcurrentPool
from funboost.core.loggers import get_funboost_file_logger
# print('eventlet imported')
from funboost.core.lazy_impoter import EventletImporter


def check_evenlet_monkey_patch(raise_exc=True):
    try:
        if not EventletImporter().patcher.is_monkey_patched('socket'):  # Pick any flag to check
            if raise_exc:
                warnings.warn(f'Detected that eventlet monkey patch is not applied. Please add "import eventlet;eventlet.monkey_patch(all=True)" at the first line of your entry script.')
                raise Exception('Detected that eventlet monkey patch is not applied. Please add "import eventlet;eventlet.monkey_patch(all=True)" at the first line of your entry script.')
        else:
            return 1
    except ModuleNotFoundError:
        if raise_exc:
            warnings.warn(f'Detected that eventlet monkey patch is not applied. Please add "import eventlet;eventlet.monkey_patch(all=True)" at the first line of your entry script.')
            raise Exception('Detected that eventlet monkey patch is not applied. Please add "import eventlet;eventlet.monkey_patch(all=True)" at the first line of your entry script.')


logger_evenlet_timeout_deco = get_funboost_file_logger('evenlet_timeout_deco')


def evenlet_timeout_deco(timeout_t):
    def _evenlet_timeout_deco(f):
        def __evenlet_timeout_deco(*args, **kwargs):
            timeout = EventletImporter().Timeout(timeout_t, )
            # timeout.start()  # Unlike gevent, it starts directly.
            result = None
            try:
                result = f(*args, **kwargs)
            except EventletImporter().Timeout as t:
                logger_evenlet_timeout_deco.error(f'Function {f} exceeded {timeout_t} seconds')
                if t is not timeout:
                    print(t)
                    # raise  # not my timeout
            finally:
                timeout.cancel()
                return result

        return __evenlet_timeout_deco

    return _evenlet_timeout_deco


def get_eventlet_pool_executor(*args2, **kwargs2):
    class CustomEventletPoolExecutor(EventletImporter().greenpool.GreenPool, FunboostBaseConcurrentPool):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            check_evenlet_monkey_patch()  # Checked in basecomer.py.
            atexit.register(self.shutdown)

        def submit(self, *args, **kwargs):  # Maintain a consistent public interface.
            # nb_print(args)
            self.spawn_n(*args, **kwargs)
            # self.spawn_n(*args, **kwargs)

        def shutdown(self):
            self.waitall()

    return CustomEventletPoolExecutor(*args2, **kwargs2)


if __name__ == '__main__':
    # greenpool.GreenPool.waitall()
    EventletImporter().monkey_patch(all=True)


    def f2(x):

        time.sleep(2)
        print(x)


    pool = get_eventlet_pool_executor(4)

    for i in range(15):
        print(f'submitting {i}')
        pool.submit(evenlet_timeout_deco(8)(f2), i)
