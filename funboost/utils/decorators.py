# coding=utf-8
import base64
import copy
import abc
import logging
import random
import uuid
from typing import TypeVar
# noinspection PyUnresolvedReferences
from contextlib import contextmanager
import functools
import json
import os
import sys
import threading
import time
import traceback
import unittest
from functools import wraps
# noinspection PyUnresolvedReferences
import pysnooper
from tomorrow3 import threads as tomorrow_threads

from funboost.utils import LogManager, nb_print, LoggerMixin
# noinspection PyUnresolvedReferences
# from funboost.utils.custom_pysnooper import _snoop_can_click, snoop_deco, patch_snooper_max_variable_length
from nb_log import LoggerLevelSetterMixin

os_name = os.name
# nb_print(f' OS type is {os_name}')
handle_exception_log = LogManager('function_error').get_logger_and_add_handlers()
run_times_log = LogManager('run_many_times').get_logger_and_add_handlers(20)


class CustomException(Exception):
    def __init__(self, err=''):
        err0 = 'fatal exception\n'
        Exception.__init__(self, err0 + err)


def run_many_times(times=1):
    """Decorator to run a function multiple times.
    :param times: number of times to run
    Does not catch errors; errors will interrupt execution. Can be combined with handle_exception decorator to run n times regardless of errors.
    """

    def _run_many_times(func):
        @wraps(func)
        def __run_many_times(*args, **kwargs):
            for i in range(times):
                run_times_log.debug('* ' * 50 + 'Currently running function [ {} ] for the {} time'.format(func.__name__, i + 1))
                func(*args, **kwargs)

        return __run_many_times

    return _run_many_times


# noinspection PyIncorrectDocstring
def handle_exception(retry_times=0, error_detail_level=0, is_throw_error=False, time_sleep=0):
    """Decorator to catch function errors, retry and log.
    :param retry_times : number of retries
    :param error_detail_level : 0 prints exception message, 1 prints 3-level deep stack trace, 2 prints full stack trace
    :param is_throw_error : whether to re-raise the error after max retries
    :type error_detail_level: int
    """

    if error_detail_level not in [0, 1, 2]:
        raise Exception('error_detail_level parameter must be set to 0, 1, or 2')

    def _handle_exception(func):
        @wraps(func)
        def __handle_exception(*args, **keyargs):
            for i in range(0, retry_times + 1):
                try:
                    result = func(*args, **keyargs)
                    if i:
                        handle_exception_log.debug(
                            u'%s\nCall succeeded, method --> [  %s  ] retry #%s succeeded' % ('# ' * 40, func.__name__, i))
                    return result

                except BaseException as e:
                    error_info = ''
                    if error_detail_level == 0:
                        error_info = 'Error type: ' + str(e.__class__) + '  ' + str(e)
                    elif error_detail_level == 1:
                        error_info = 'Error type: ' + str(e.__class__) + '  ' + traceback.format_exc(limit=3)
                    elif error_detail_level == 2:
                        error_info = 'Error type: ' + str(e.__class__) + '  ' + traceback.format_exc()

                    handle_exception_log.exception(
                        u'%s\nError log recorded, method --> [  %s  ] error retry #%s, %s\n' % ('- ' * 40, func.__name__, i, error_info))
                    if i == retry_times and is_throw_error:  # Re-raise error after reaching max retry count
                        raise e
                time.sleep(time_sleep)

        return __handle_exception

    return _handle_exception


def keep_circulating(time_sleep=0.001, exit_if_function_run_sucsess=False, is_display_detail_exception=True, block=True, daemon=False):
    """Decorator to keep running a method in a loop at regular intervals.
    :param time_sleep : interval time between loops
    :param exit_if_function_run_sucsess : exit the loop if the function succeeds
    :param is_display_detail_exception
    :param block : whether to block the main thread. When False, starts a new thread to run the while loop.
    """
    if not hasattr(keep_circulating, 'keep_circulating_log'):
        keep_circulating.log = LogManager('keep_circulating').get_logger_and_add_handlers()

    def _keep_circulating(func):
        @wraps(func)
        def __keep_circulating(*args, **kwargs):

            # noinspection PyBroadException
            def ___keep_circulating():
                while 1:
                    try:
                        result = func(*args, **kwargs)
                        if exit_if_function_run_sucsess:
                            return result
                    except BaseException as e:
                        msg = func.__name__ + '   execution error\n ' + traceback.format_exc(limit=10) if is_display_detail_exception else str(e)
                        keep_circulating.log.error(msg)
                    finally:
                        time.sleep(time_sleep)

            if block:
                return ___keep_circulating()
            else:
                threading.Thread(target=___keep_circulating, daemon=daemon).start()

        return __keep_circulating

    return _keep_circulating


def synchronized(func):
    """Thread lock decorator, can be applied to singleton patterns"""
    func.__lock__ = threading.Lock()

    @wraps(func)
    def lock_func(*args, **kwargs):
        with func.__lock__:
            return func(*args, **kwargs)

    return lock_func

ClSX = TypeVar('CLSX')
def singleton(cls:ClSX)  -> ClSX:
    """
    Singleton pattern decorator with thread lock for a more robust singleton. Mainly solves the issue where multiple threads (e.g. 100 threads) instantiating simultaneously could create 3 or 4 instances.
    """
    _instance = {}
    singleton.__lock = threading.Lock()

    @wraps(cls)
    def _singleton(*args, **kwargs):
        with singleton.__lock:
            if cls not in _instance:
                _instance[cls] = cls(*args, **kwargs)
            return _instance[cls]

    return _singleton

def singleton_no_lock(cls:ClSX)  -> ClSX:
    """
    Singleton pattern decorator without thread lock. May produce multiple instances under heavy concurrent instantiation.
    """
    _instance = {}


    @wraps(cls)
    def _singleton(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return _singleton

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class SingletonBaseCall(metaclass=SingletonMeta):
    """
    Singleton base class. Any subclass inheriting from this base class will automatically become a singleton.

    Example:
    class MyClass(SingletonBase):
        pass

    instance1 = MyClass()
    instance2 = MyClass()

    assert instance1 is instance2  # instance1 and instance2 are actually the same object
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Additional subclass processing can be added here, e.g. checking singleton requirements


class SingletonBaseNew:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Additional subclass processing can be added here, e.g. checking singleton requirements


class SingletonBaseCustomInit(metaclass=abc.ABCMeta):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._custom_init(*args, **kwargs)
        return cls._instance

    def _custom_init(self, *args, **kwargs):
        raise NotImplemented



def flyweight(cls):
    """
    Flyweight pattern decorator, a limited multi-instance pattern that returns the same instance for identical parameters.

    Improvement: Compatible with both positional and keyword arguments. The following two calls return the same instance:
        cls('value')           # positional argument
        cls(param='value')     # keyword argument
    """
    import inspect
    
    # 1. Storage within closure, each class independently owns its own instance cache without interference
    _instances = {}
    
    # 2. Create an independent lock for each class to avoid global lock contention
    _class_lock = threading.Lock()
    
    # 3. Get the signature of the class's __init__ method for parameter normalization
    try:
        _sig = inspect.signature(cls.__init__)
    except (ValueError, TypeError):
        _sig = None

    def _make_hashable(value):
        if isinstance(value, dict):
            return tuple(sorted((k, _make_hashable(v)) for k, v in value.items()))
        elif isinstance(value, (list, tuple)):
            return tuple(_make_hashable(v) for v in value)
        elif isinstance(value, set):
            return frozenset(_make_hashable(v) for v in value)
        return value

    def _make_key(args, kwds):
        """
        Generate a unique key, compatible with both positional and keyword arguments.
        Uses inspect.signature.bind to normalize all arguments into a unified form.
        """
        if _sig is not None:
            try:
                # Bind arguments to the signature, normalizing positional and keyword args uniformly
                # Pass None as a placeholder for the self parameter
                bound = _sig.bind(None, *args, **kwds)
                bound.apply_defaults()  # Apply defaults to ensure calls with same semantics generate same key

                # Get the bound arguments dict, remove self parameter
                arguments = dict(bound.arguments)
                arguments.pop('self', None)

                # Convert to hashable sorted tuple, ensuring consistent order
                return tuple(sorted((k, _make_hashable(v)) for k, v in arguments.items()))
            except TypeError:
                # If binding fails (argument mismatch, etc.), fall back to the original approach
                pass
        
        # Fallback: use the original approach
        key_args = _make_hashable(args)
        if not kwds:
            return key_args
        key_kwargs = frozenset((k, _make_hashable(v)) for k, v in kwds.items())
        return (key_args, key_kwargs)

    @wraps(cls)
    def _flyweight(*args, **kwargs):
        # 1. Generate Key
        cache_key = _make_key(args, kwargs)
        
        # 2. First check (no lock, high performance)
        if cache_key not in _instances:
            # 3. Acquire lock (only for the current class)
            with _class_lock:
                # 4. Second check (Double-Checked Locking)
                if cache_key not in _instances:
                    _instances[cache_key] = cls(*args, **kwargs)
        
        return _instances[cache_key]

    return _flyweight


def timer(func):
    """Timer decorator, only used to measure function execution time"""
    if not hasattr(timer, 'log'):
        timer.log = LogManager(f'timer_{func.__name__}').get_logger_and_add_handlers(log_filename=f'timer_{func.__name__}.log')

    @wraps(func)
    def _timer(*args, **kwargs):
        t1 = time.time()
        result = func(*args, **kwargs)
        t2 = time.time()
        t_spend = round(t2 - t1, 2)
        timer.log.debug('Executing method [ {} ] took {} seconds'.format(func.__name__, t_spend))
        return result

    return _timer


# noinspection PyProtectedMember
class TimerContextManager(LoggerMixin):
    """
    Timer using context manager, can time code snippets.
    """

    def __init__(self, is_print_log=True):
        self._is_print_log = is_print_log
        self.t_spend = None
        self._line = None
        self._file_name = None
        self.time_start = None

    def __enter__(self):
        self._line = sys._getframe().f_back.f_lineno  # Line number of the code calling this method
        self._file_name = sys._getframe(1).f_code.co_filename  # Which file called this method
        self.time_start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.t_spend = time.time() - self.time_start
        if self._is_print_log:
            self.logger.debug(f'Timing code snippet:  \nExecuting "{self._file_name}:{self._line}" took {round(self.t_spend, 2)} seconds')


class RedisDistributedLockContextManager(LoggerMixin, LoggerLevelSetterMixin):
    """
    Distributed Redis lock context manager.
    """
    '''
    redis 官方推荐的 redlock-py
    https://github.com/SPSCommerce/redlock-py/blob/master/redlock/__init__.py
    '''
    unlock_script = """
       if redis.call("get",KEYS[1]) == ARGV[1] then
           return redis.call("del",KEYS[1])
       else
           return 0
       end"""

    def __init__(self, redis_client, redis_lock_key, expire_seconds=30, ):
        self.redis_client = redis_client
        self.redis_lock_key = redis_lock_key
        self._expire_seconds = expire_seconds
        self.identifier = str(uuid.uuid4())
        self.has_aquire_lock = False
        self.logger.setLevel(logging.INFO)

    def __enter__(self):
        self._line = sys._getframe().f_back.f_lineno  # Line number of the code calling this method
        self._file_name = sys._getframe(1).f_code.co_filename  # Which file called this method
        ret = self.redis_client.set(self.redis_lock_key, value=self.identifier, ex=self._expire_seconds, nx=True)

        self.has_aquire_lock = False if ret is None else True
        if self.has_aquire_lock:
            log_msg = f'\n"{self._file_name}:{self._line}" this line acquired redis lock {self.redis_lock_key}'
        else:
            log_msg = f'\n"{self._file_name}:{self._line}" this line did not acquire redis lock {self.redis_lock_key}'
        # print(self.logger.level,log_msg)
        self.logger.debug(log_msg)
        return self

    def __bool__(self):
        return self.has_aquire_lock

    def __exit__(self, exc_type, exc_val, exc_tb):
        # self.redis_client.delete(self.redis_lock_key)
        unlock = self.redis_client.register_script(self.unlock_script)
        result = unlock(keys=[self.redis_lock_key], args=[self.identifier])
        if result:
            return True
        else:
            return False


class RedisDistributedBlockLockContextManager(RedisDistributedLockContextManager):
    def __init__(self, redis_client, redis_lock_key, expire_seconds=30, check_interval=0.1):
        super().__init__(redis_client,redis_lock_key,expire_seconds)
        self.check_interval = check_interval
        # self.logger.setLevel(logging.DEBUG)

    def __enter__(self):
        while True:
            self._line = sys._getframe().f_back.f_lineno  # Line number of the code calling this method
            self._file_name = sys._getframe(1).f_code.co_filename  # Which file called this method
            ret = self.redis_client.set(self.redis_lock_key, value=self.identifier, ex=self._expire_seconds, nx=True)
            has_aquire_lock = False if ret is None else True
            if has_aquire_lock:
                log_msg = f'\n"{self._file_name}:{self._line}" this line acquired redis lock {self.redis_lock_key}'
            else:
                log_msg = f'\n"{self._file_name}:{self._line}" this line did not acquire redis lock {self.redis_lock_key}'
            # print(self.logger.level,log_msg)
            self.logger.debug(log_msg)
            if has_aquire_lock:
                break
            else:
                time.sleep(self.check_interval)


"""
@contextmanager
        def some_generator(<arguments>):
            <setup>
            try:
                yield <value>
            finally:
                <cleanup>
"""





class ExceptionContextManager:
    """
    Exception catching using context manager, can catch errors in code snippets, more granular than decorators.
    """

    def __init__(self, logger_name='ExceptionContextManager', verbose=100, donot_raise__exception=True, ):
        """
        :param verbose: Depth of error printing, corresponds to traceback's limit parameter, must be a positive integer
        :param donot_raise__exception: Whether to suppress the exception. False re-raises, True suppresses.
        """
        self.logger = LogManager(logger_name).get_logger_and_add_handlers()
        self._verbose = verbose
        self._donot_raise__exception = donot_raise__exception

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # print(exc_val)
        # print(traceback.format_exc())
        exc_str = str(exc_type) + '  :  ' + str(exc_val)
        exc_str_color = '\033[0;30;45m%s\033[0m' % exc_str
        if self._donot_raise__exception:
            if exc_tb is not None:
                self.logger.error('\n'.join(traceback.format_tb(exc_tb)[:self._verbose]) + exc_str_color)
        return self._donot_raise__exception  # __exit__ method must return True to suppress the exception


def where_is_it_called(func):
    """A decorator that logs which file and line number called the decorated function"""
    if not hasattr(where_is_it_called, 'log'):
        where_is_it_called.log = LogManager('where_is_it_called').get_logger_and_add_handlers()

    # noinspection PyProtectedMember
    @wraps(func)
    def _where_is_it_called(*args, **kwargs):
        # Get the called function name
        # func_name = sys._getframe().f_code.co_name
        func_name = func.__name__
        # Which function called this function
        which_fun_call_this = sys._getframe(1).f_code.co_name  # NOQA

        # Get the line number where the called function was invoked
        line = sys._getframe().f_back.f_lineno

        # Get the module file name of the called function
        file_name = sys._getframe(1).f_code.co_filename

        # noinspection PyPep8
        where_is_it_called.log.debug(
            f'Method [{func_name}] at line [{func.__code__.co_firstlineno}] of file [{func.__code__.co_filename}] in module [{func.__module__}] is being called from '
            f'method [{which_fun_call_this}] at line [{line}] in file [{file_name}], with arguments [{args},{kwargs}]')
        try:
            t0 = time.time()
            result = func(*args, **kwargs)
            result_raw = result
            t_spend = round(time.time() - t0, 2)
            if isinstance(result, dict):
                result = json.dumps(result)
            if len(str(result)) > 200:
                result = str(result)[0:200] + '  ......  '
            where_is_it_called.log.debug('Executing function [{}] took {} seconds, returned result --> '.format(func_name, t_spend) + str(result))
            return result_raw
        except BaseException as e:
            where_is_it_called.log.debug('Executing function {}, an error occurred'.format(func_name))
            where_is_it_called.log.exception(e)
            raise e

    return _where_is_it_called


# noinspection PyPep8Naming
class cached_class_property(object):
    """Class property cache decorator"""

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = self.func(obj)
        setattr(cls, self.func.__name__, value)
        return value


# noinspection PyPep8Naming
class cached_property(object):
    """Instance property cache decorator"""

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        print(obj, cls)
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def cached_method_result(fun):
    """Method result caching decorator. Does not accept parameters other than self. Mainly used on property-like methods, combined with @property. Better PyCharm auto-completion than the decorators above."""

    @wraps(fun)
    def inner(self):
        if not hasattr(fun, 'result'):
            result = fun(self)
            fun.result = result
            fun_name = fun.__name__
            setattr(self.__class__, fun_name, result)
            setattr(self, fun_name, result)
            return result
        else:
            return fun.result

    return inner


def cached_method_result_for_instance(fun):
    """Method result caching decorator for instances. Does not accept parameters other than self. Mainly used on property-like methods."""

    @wraps(fun)
    def inner(self):
        if not hasattr(fun, 'result'):
            result = fun(self)
            fun.result = result
            fun_name = fun.__name__
            setattr(self, fun_name, result)
            return result
        else:
            return fun.result

    return inner


class FunctionResultCacher:
    logger = LogManager('FunctionResultChche').get_logger_and_add_handlers(log_level_int=20)
    func_result_dict = {}
    """
    {
        (f1,(1,2,3,4)):(10,1532066199.739),
        (f2,(5,6,7,8)):(26,1532066211.645),
    }
    """

    @classmethod
    def cached_function_result_for_a_time(cls, cache_time: float):
        """
        Decorator to cache function results for a period of time. Do not use on functions that return very large strings or memory-intensive data structures.
        :param cache_time : cache duration in seconds
        :type cache_time : float
        """

        def _cached_function_result_for_a_time(fun):

            @wraps(fun)
            def __cached_function_result_for_a_time(*args, **kwargs):
                # print(cls.func_result_dict)
                # if len(cls.func_result_dict) > 1024:
                if sys.getsizeof(cls.func_result_dict) > 100 * 1000 * 1000:
                    cls.func_result_dict.clear()

                key = cls._make_arguments_to_key(args, kwargs)
                if (fun, key) in cls.func_result_dict and time.time() - cls.func_result_dict[(fun, key)][1] < cache_time:
                    return cls.func_result_dict[(fun, key)][0]
                else:
                    cls.logger.debug('Function [{}] cannot use cache this time'.format(fun.__name__))
                    result = fun(*args, **kwargs)
                    cls.func_result_dict[(fun, key)] = (result, time.time())
                    return result

            return __cached_function_result_for_a_time

        return _cached_function_result_for_a_time

    @staticmethod
    def _make_arguments_to_key(args, kwds):
        key = args
        if kwds:
            sorted_items = sorted(kwds.items())
            for item in sorted_items:
                key += item
        return key  # Tuples can be concatenated.


# noinspection PyUnusedLocal
class __KThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.killed = False
        self.__run_backup = None

    # noinspection PyAttributeOutsideInit
    def start(self):
        """Start the thread."""
        self.__run_backup = self.run
        self.run = self.__run  # Force the Thread to install our trace.
        threading.Thread.start(self)

    def __run(self):
        """Hacked run function, which installs the trace."""
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, why, arg):
        if why == 'call':
            return self.localtrace
        return None

    def localtrace(self, frame, why, arg):
        if self.killed:
            if why == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True


# noinspection PyPep8Naming
class TIMEOUT_EXCEPTION(Exception):
    """function run timeout"""
    pass


def timeout(seconds):
    """Timeout decorator, specifies a timeout duration.

    If the decorated method does not return within the specified time, a Timeout exception is raised."""

    def timeout_decorator(func):

        def _(*args, **kwargs):
            def _new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
                result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))

            result = []
            new_kwargs = {
                'oldfunc': func,
                'result': result,
                'oldfunc_args': args,
                'oldfunc_kwargs': kwargs
            }

            thd = __KThread(target=_new_func, args=(), kwargs=new_kwargs)
            thd.start()
            thd.join(seconds)
            alive = thd.is_alive()
            thd.kill()  # kill the child thread

            if alive:
                # raise TIMEOUT_EXCEPTION('function run too long, timeout %d seconds.' % seconds)
                raise TIMEOUT_EXCEPTION(f'{func.__name__} execution time exceeded {seconds} seconds')
            else:
                if result:
                    return result[0]
                return result

        _.__name__ = func.__name__
        _.__doc__ = func.__doc__
        return _

    return timeout_decorator


# noinspection PyMethodMayBeStatic
class _Test(unittest.TestCase):
    @unittest.skip
    def test_superposition(self):
        """Test multiple runs and exception retry, test decorator stacking"""

        @run_many_times(3)
        @handle_exception(2, 1)
        def f():
            import json
            json.loads('a', ac='ds')

        f()

    @unittest.skip
    def test_run_many_times(self):
        """Test running 5 times"""

        @run_many_times(5)
        def f1():
            print('hello')
            time.sleep(1)

        f1()

    @unittest.skip
    def test_tomorrow_threads(self):
        """Test multi-thread decorator, print 5 times every 2 seconds"""

        @tomorrow_threads(5)
        def f2():
            print(time.strftime('%H:%M:%S'))
            time.sleep(2)

        [f2() for _ in range(9)]

    @unittest.skip
    def test_singleton(self):
        """Test singleton pattern decorator"""

        @singleton
        class A(object):
            def __init__(self, x):
                self.x = x

        a1 = A(3)
        a2 = A(4)
        self.assertEqual(id(a1), id(a2))
        print(a1.x, a2.x)

    @unittest.skip
    def test_flyweight(self):
        @flyweight
        class A:
            def __init__(self, x, y, z, q=4):
                in_param = copy.deepcopy(locals())
                nb_print(f'Initialization executed, {in_param}')

        @flyweight
        class B:
            def __init__(self, x, y, z):
                in_param = copy.deepcopy(locals())
                nb_print(f'Initialization executed, {in_param}')

        A(1, 2, 3)
        A(1, 2, 3)
        A(1, 2, 4)
        B(1, 2, 3)

    @unittest.skip
    def test_keep_circulating(self):
        """Test interval time, looping execution"""

        @keep_circulating(3)
        def f6():
            print("Printing every 3 seconds   " + time.strftime('%H:%M:%S'))

        f6()

    @unittest.skip
    def test_timer(self):
        """Test timer decorator"""

        @timer
        def f7():
            time.sleep(2)

        f7()

    @unittest.skip
    def test_timer_context(self):
        """
        Test context manager for timing code snippets
        """
        with TimerContextManager(is_print_log=False) as tc:
            time.sleep(2)
        print(tc.t_spend)

    @unittest.skip
    def test_where_is_it_called(self):
        """测试函数被调用的装饰器，被调用2次将会记录2次被调用的日志"""

        @where_is_it_called
        def f9(a, b):
            result = a + b
            print(result)
            time.sleep(0.1)
            return result

        f9(1, 2)

        f9(3, 4)

    # noinspection PyArgumentEqualDefault
    # @unittest.skip
    def test_cached_function_result(self):
        @FunctionResultCacher.cached_function_result_for_a_time(3)
        def f10(a, b, c=3, d=4):
            print('计算中。。。')
            return a + b + c + d

        print(f10(1, 2, 3, d=6))
        print(f10(1, 2, 3, d=4))
        print(f10(1, 2, 3, 4))
        print(f10(1, 2, 3, 4))
        time.sleep(4)
        print(f10(1, 2, 3, 4))

    @unittest.skip
    def test_exception_context_manager(self):
        def f1():
            # noinspection PyStatementEffect,PyTypeChecker
            1 + '2'

        def f2():
            f1()

        def f3():
            f2()

        def f4():
            f3()

        def run():
            f4()

        # noinspection PyUnusedLocal
        with ExceptionContextManager() as ec:
            run()

        print('finish')

    @unittest.skip
    def test_timeout(self):
        """
        测试超时装饰器
        :return:
        """

        @timeout(3)
        def f(time_to_be_sleep):
            time.sleep(time_to_be_sleep)
            print('hello wprld')

        f(5)


if __name__ == '__main__':
    pass
    unittest.main()
