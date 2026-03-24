"""
Integrated scheduled task support.
"""
import atexit

import time
from apscheduler.executors.pool import BasePoolExecutor

from typing import Union
import threading

from apscheduler.schedulers.background import BackgroundScheduler
# noinspection PyProtectedMember
from apscheduler.schedulers.base import STATE_STOPPED, STATE_RUNNING
from apscheduler.util import undefined
from threading import TIMEOUT_MAX
import deprecated
from funboost.utils.redis_manager import RedisMixin

from funboost.funboost_config_deafult import FunboostCommonConfig

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.booster import BoostersManager, Booster

from funboost.core.func_params_model import BoosterParams
from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble,ThreadPoolExecutorShrinkAbleNonDaemon


@deprecated.deprecated(reason='Do not use this approach anymore. It has serialization issues when job_store is a database. Use add_push_job which is compatible with both memory and database: add_push_job')
def timing_publish_deco(consuming_func_decorated_or_consumer: Union[callable, AbstractConsumer]):
    def _deco(*args, **kwargs):
        if getattr(consuming_func_decorated_or_consumer, 'is_decorated_as_consume_function', False) is True:
            consuming_func_decorated_or_consumer.push(*args, **kwargs)
        elif isinstance(consuming_func_decorated_or_consumer, AbstractConsumer):
            consuming_func_decorated_or_consumer.publisher_of_same_queue.push(*args, **kwargs)
        else:
            raise TypeError('consuming_func_decorated_or_consumer must be a function decorated with @boost or a consumer type')

    return _deco


def push_fun_params_to_broker(queue_name: str, *args, **kwargs):
    """
    queue_name: queue name
    *args **kwargs are the input parameters of the consumer function
    """
    try:
        booster = BoostersManager.get_or_create_booster_by_queue_name(queue_name)
        return booster.push(*args, **kwargs)
    except KeyError as e:
        from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter
        publisher = SingleQueueConusmerParamsGetter(queue_name).gen_publisher_for_faas()
        return publisher.push(*args, **kwargs)
        


class ThreadPoolExecutorForAps(BasePoolExecutor):
    """
    An executor that runs jobs in a concurrent.futures thread pool.

    Plugin alias: ``threadpool``

    :param max_workers: the maximum number of spawned threads.
    :param pool_kwargs: dict of keyword arguments to pass to the underlying
        ThreadPoolExecutor constructor
    """

    def __init__(self, max_workers=100, pool_kwargs=None):

        # pool = ThreadPoolExecutorShrinkAble(int(max_workers), )
        pool = ThreadPoolExecutorShrinkAbleNonDaemon(int(max_workers), )

        """
        raise RuntimeError('cannot schedule new futures after ' RuntimeError: cannot schedule new futures after interpreter shutdown

        ThreadPoolExecutorShrinkAbleNonDaemon is better - it prevents the error caused by the main thread exiting
        while apscheduler uses a daemon-threaded thread pool.
        ThreadPoolExecutorShrinkAbleNonDaemon's threads are non-daemon threads.
        """

        super().__init__(pool)


class FunboostBackgroundScheduler(BackgroundScheduler):
    """
    Custom class, inherits from the official BackgroundScheduler.
    By overriding _main_loop, it provides better support for dynamically modifying, adding, and deleting scheduled task configurations.
    """

    _last_wait_seconds = None
    _last_has_task = False

    @deprecated.deprecated(reason='Do not use this approach anymore. It has serialization issues when job_store is a database. Use add_push_job which is compatible with both memory and database: add_push_job')
    def add_timing_publish_job(self, func, trigger=None, args=None, kwargs=None, id=None, name=None,
                               misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                               next_run_time=undefined, jobstore='default', executor='default',
                               replace_existing=False, **trigger_args):
        return self.add_job(timing_publish_deco(func), trigger, args, kwargs, id, name,
                            misfire_grace_time, coalesce, max_instances,
                            next_run_time, jobstore, executor,
                            replace_existing, **trigger_args)

    def add_push_job(self, func: Booster, trigger=None, args=None, kwargs=None, 
                     id=None, name=None,
                     misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                     next_run_time=undefined, jobstore='default', executor='default',
                     replace_existing=False, **trigger_args, ):
        """
        :param func: Function decorated with @boost decorator
        :param trigger:
        :param args:
        :param kwargs:
        :param id:
        :param name:
        :param misfire_grace_time:
        :param coalesce:
        :param max_instances:
        :param next_run_time:
        :param jobstore:
        :param executor:
        :param replace_existing:
        :param trigger_args:
        :return:
        """
        # args = args or {}
        # kwargs['queue_name'] = func.queue_name

        """
        If users don't use funboost's FunboostBackgroundScheduler but instead use the native apscheduler object,
        they can use scheduler.add_job(push_fun_params_to_broker, args=(,), kwargs={}).
        push_fun_params_to_broker's input parameters are the consumer function queue's queue_name plus
        the original consumer function's input parameters.
        """
        if args is None:
            args = tuple()
        
        args_list = list(args)
        args_list.insert(0, func.queue_name)
        args = tuple(args_list)
        if name is None:
            name = f'push_fun_params_to_broker_for_queue_{func.queue_name}'
        func.publisher.check_func_input_params(*args[1:], **(kwargs or {})) # This line validates input parameters, preventing invalid scheduled parameters from being added and only discovered at execution time. This is more reliable than the official apscheduler.
        return self.add_job(push_fun_params_to_broker, trigger, args, kwargs, id, name,
                            misfire_grace_time, coalesce, max_instances,
                            next_run_time, jobstore, executor,
                            replace_existing, **trigger_args, )

    def start(self, paused=False, block_exit=True):
        # def _block_exit():
        #     while True:
        #         time.sleep(3600)
        #
        # threading.Thread(target=_block_exit,).start()  # 既不希望用BlockingScheduler阻塞主进程也不希望定时退出。
        # self._daemon = False
        # def _when_exit():
        #     while 1:
        #         # print('prevent exit')
        #         time.sleep(100)

        # if block_exit:
        #     atexit.register(_when_exit)
        self._daemon = False   # Here we override BackgroundScheduler's _daemon attribute, forcing it to non-daemon thread by default. The default is daemon thread, which causes RuntimeError: cannot schedule new futures after interpreter shutdown when the main thread exits.
        super().start(paused=paused, )
        # _block_exit() 
    def _main_loop00000(self):
        """
        The original code was this, not friendly for dynamically adding tasks.
        :return:
        """
        wait_seconds = threading.TIMEOUT_MAX
        while self.state != STATE_STOPPED:
            print(6666, self._event.is_set(), wait_seconds)
            self._event.wait(wait_seconds)
            print(7777, self._event.is_set(), wait_seconds)
            self._event.clear()
            wait_seconds = self._process_jobs()

    def _main_loop(self):
        """The original _main_loop would set wait_seconds to None after all tasks are deleted, causing infinite waiting.
        Or if the next task to run has a wait_seconds of 3600 seconds, and a new dynamic task is added during that time,
        now it takes at most 1 second to detect newly added dynamic scheduled tasks.
        """
        MAX_WAIT_SECONDS_FOR_NEX_PROCESS_JOBS = 0.5
        wait_seconds = None
        while self.state != STATE_STOPPED:
            if wait_seconds is None:
                wait_seconds = MAX_WAIT_SECONDS_FOR_NEX_PROCESS_JOBS
            self._last_wait_seconds = min(wait_seconds, MAX_WAIT_SECONDS_FOR_NEX_PROCESS_JOBS)
            if wait_seconds in (None, TIMEOUT_MAX):
                self._last_has_task = False
            else:
                self._last_has_task = True
            time.sleep(self._last_wait_seconds)  # Must take the minimum value, otherwise e.g. with a 0.1 second interval, without taking the minimum it won't run every 0.1 seconds.
            wait_seconds = self._process_jobs()

    def _create_default_executor(self):
        return ThreadPoolExecutorForAps()  # Must be a subclass of apscheduler pool


FsdfBackgroundScheduler = FunboostBackgroundScheduler  # Backward compatibility for the name, fsdf is the abbreviation of function-scheduling-distributed-framework (the old framework name)
# funboost_aps_scheduler's scheduled configuration is memory-based, cannot remotely add/modify/delete scheduled task configurations across machines. For dynamic CRUD of scheduled tasks, use funboost_background_scheduler_redis_store

"""
It is recommended not to use this funboost_aps_scheduler object directly, but instead use ApsJobAdder
to add scheduled tasks, which automatically creates multiple apscheduler object instances.
Especially when using Redis as jobstores, it uses different jobstores with separate jobs_key and run_times_key
for each consumer function.
"""
# funboost_aps_scheduler uses memory as job_store
funboost_aps_scheduler = FunboostBackgroundScheduler(timezone=FunboostCommonConfig.TIMEZONE, daemon=False, )
fsdf_background_scheduler = funboost_aps_scheduler  # Backward compatibility for the old name.



if __name__ == '__main__':

    """
    The examples below are outdated. They still work but are not recommended.
    It is recommended to use ApsJobAdder uniformly to add scheduled tasks.
    """

    # Scheduled consumption demo
    import datetime
    from funboost import boost, BrokerEnum, fsdf_background_scheduler, timing_publish_deco, run_forever


    @Booster(boost_params=BoosterParams(queue_name='queue_test_666', broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE))
    def consume_func(x, y):
        print(f'{x} + {y} = {x + y}')


    print(consume_func, type(consume_func))

    # Schedule to run every 3 seconds.
    funboost_aps_scheduler.add_push_job(consume_func,
                                        'interval', id='3_second_job', seconds=3, kwargs={"x": 5, "y": 6})

    # Schedule to run only once
    funboost_aps_scheduler.add_push_job(consume_func,
                                        'date', run_date=datetime.datetime(2020, 7, 24, 13, 53, 6), args=(5, 6,))

    # Schedule to run every day at 11:32:20.
    funboost_aps_scheduler.add_push_job(consume_func,
                                        'cron', day_of_week='*', hour=18, minute=22, second=20, args=(5, 6,))

    # Start scheduler
    funboost_aps_scheduler.start()

    # Start consuming
    consume_func.consume()
    run_forever()
