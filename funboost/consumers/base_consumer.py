# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:11
"""
Abstract base class for all middleware-type consumers. Minimizes the code needed to implement consumers for different middlewares.
The most complex parts of the entire framework are implemented here, because multiple concurrency models and over 20 function execution control methods need to be supported, resulting in very long code.

The main framework functionality is implemented in this file.
"""
import functools
import random
import sys
import typing
import abc
import copy
from apscheduler.jobstores.memory import MemoryJobStore
from funboost.core.broker_kind__exclusive_config_default_define import generate_broker_exclusive_config
from funboost.core.funboost_time import FunboostTime
from pathlib import Path
# from multiprocessing import Process
import datetime
# noinspection PyUnresolvedReferences,PyPackageRequirements
import pytz
import json
import logging
import atexit
import os
import uuid
import time
import traceback
import inspect
from functools import wraps
import threading
from threading import Lock
import threading
from threading import Lock
import asyncio

from croniter import croniter, CroniterBadCronError
from cron_descriptor import get_description, Options


import nb_log
from funboost.core.current_task import FctContext,set_fct_context
from funboost.core.loggers import develop_logger

from funboost.core.func_params_model import BoosterParams, PublisherParams, BaseJsonAbleModel
from funboost.core.serialization import PickleHelper, Serialization
from funboost.core.task_id_logger import TaskIdLogger
from funboost.constant import FunctionKind, StrConst

from nb_libs.path_helper import PathHelper
from nb_log import (get_logger, LoggerLevelSetterMixin, LogManager, is_main_process,
                    nb_log_config_default)
from funboost.core.loggers import FunboostFileLoggerMixin, logger_prompt

from apscheduler.jobstores.redis import RedisJobStore

from apscheduler.executors.pool import ThreadPoolExecutor as ApschedulerThreadPoolExecutor

from funboost.funboost_config_deafult import FunboostCommonConfig
from funboost.concurrent_pool.single_thread_executor import SoloExecutor

from funboost.core.function_result_status_saver import ResultPersistenceHelper, FunctionResultStatus, RunStatus

from funboost.core.helper_funs import delete_keys_and_return_new_dict, get_func_only_params, get_publish_time, MsgGenerater

from funboost.concurrent_pool.async_helper import get_or_create_event_loop, simple_run_in_executor
from funboost.concurrent_pool.async_pool_executor import AsyncPoolExecutor
# noinspection PyUnresolvedReferences
from funboost.concurrent_pool.bounded_threadpoolexcutor import \
    BoundedThreadPoolExecutor
from funboost.utils.redis_manager import RedisMixin
# from func_timeout import func_set_timeout  # noqa
from funboost.utils.func_timeout import dafunc

from funboost.concurrent_pool.custom_threadpool_executor import check_not_monkey
from funboost.concurrent_pool.flexible_thread_pool import FlexibleThreadPool, sync_or_async_fun_deco
# from funboost.concurrent_pool.concurrent_pool_with_multi_process import ConcurrentPoolWithProcess
from funboost.consumers.redis_filter import RedisFilter, RedisImpermanencyFilter
from funboost.factories.publisher_factotry import get_publisher

from funboost.utils import decorators, time_util, redis_manager
from funboost.constant import ConcurrentModeEnum, BrokerEnum, ConstStrForClassMethod, RedisKeys
from funboost.core import kill_remote_task
from funboost.core.exceptions import ExceptionForRequeue, ExceptionForPushToDlxqueue
from funboost.core.consuming_func_iniput_params_check import ConsumingFuncInputParamsChecker, FakeFunGenerator

# from funboost.core.booster import BoostersManager  # circular import
from funboost.core.lazy_impoter import funboost_lazy_impoter


# patch_apscheduler_run_job()

class GlobalVars:
    global_concurrent_mode = None
    has_start_a_consumer_flag = False


# noinspection DuplicatedCode
class AbstractConsumer(metaclass=abc.ABCMeta, ):
    _time_interval_for_check_allow_run_by_cron = 60
    BROKER_KIND = None

    @property
    def publisher_of_same_queue(self):
        if not self._publisher_of_same_queue:
            with self._lock_for_get_publisher:
                if not self._publisher_of_same_queue:
                    self._publisher_of_same_queue = get_publisher(publisher_params=self.publisher_params)
        return self._publisher_of_same_queue

    def bulid_a_new_publisher_of_same_queue(self):
        return get_publisher(publisher_params=self.publisher_params)

    @property
    def publisher_of_dlx_queue(self):
        """ Dead letter queue publisher """
        if not self._publisher_of_dlx_queue:
            with self._lock_for_get_publisher:
                if not self._publisher_of_dlx_queue:
                    publisher_params_dlx = copy.copy(self.publisher_params)
                    publisher_params_dlx.queue_name = self._dlx_queue_name
                    publisher_params_dlx.consuming_function = None
                    self._publisher_of_dlx_queue = get_publisher(publisher_params=publisher_params_dlx)
        return self._publisher_of_dlx_queue

    @classmethod
    def join_dispatch_task_thread(cls):
        """

        :return:
        """
        # ConsumersManager.join_all_consumer_dispatch_task_thread()
        if GlobalVars.has_start_a_consumer_flag:
            # self.keep_circulating(10,block=True,)(time.sleep)()
            while 1:
                time.sleep(10)

    def __init__(self, consumer_params: BoosterParams):

        """
        """
        self.raw_consumer_params = copy.copy(consumer_params)
        self.consumer_params = copy.copy(consumer_params)
        # noinspection PyUnresolvedReferences
        file_name = self.consumer_params.consuming_function.__code__.co_filename
        # noinspection PyUnresolvedReferences
        line = self.consumer_params.consuming_function.__code__.co_firstlineno
        self.consumer_params.auto_generate_info['where_to_instantiate'] = f'{file_name}:{line}'

        self.queue_name = self._queue_name = consumer_params.queue_name
        self.consuming_function = consumer_params.consuming_function
        if consumer_params.consuming_function is None:
            raise ValueError('consuming_function parameter must be provided')

        self._msg_schedule_time_intercal = 0 if consumer_params.qps in (None, 0) else 1.0 / consumer_params.qps

        self._concurrent_mode_dispatcher = ConcurrentModeDispatcher(self)
        if consumer_params.concurrent_mode == ConcurrentModeEnum.ASYNC:
            self._any_run = self._async_run  # Automatic conversion here: use async_run instead of run
        else:
            self._any_run = self._run
        self.logger: logging.Logger
        self._build_logger()
        # stdout_write(f'''{time.strftime("%H:%M:%S")} "{self.consumer_params.auto_generate_info['where_to_instantiate']}"  \033[0;37;44m This line instantiates a consumer for queue name {self.queue_name}, type is {self.__class__}\033[0m\n''')
        print(f'''\033[0m
         "{self.consumer_params.auto_generate_info['where_to_instantiate']}" \033[0m This line instantiates a consumer for queue name {self.queue_name}, type is {self.__class__} ''')

        # only_print_on_main_process(f'Consumer config for {current_queue__info_dict["queue_name"]}:\n', un_strict_json_dumps.dict2json(current_queue__info_dict))

        # self._do_task_filtering = consumer_params.do_task_filtering
        # self.consumer_params.is_show_message_get_from_broker = consumer_params.is_show_message_get_from_broker
        self._redis_filter_key_name = f'filter_zset:{consumer_params.queue_name}' if consumer_params.task_filtering_expire_seconds else f'filter_set:{consumer_params.queue_name}'
        filter_class = RedisFilter if consumer_params.task_filtering_expire_seconds == 0 else RedisImpermanencyFilter
        self._redis_filter = filter_class(self._redis_filter_key_name, consumer_params.task_filtering_expire_seconds)
        self._redis_filter.delete_expire_filter_task_cycle()

        # if  self.consumer_params.concurrent_mode == ConcurrentModeEnum.ASYNC and self.consumer_params.specify_async_loop is None:
        #     self.consumer_params.specify_async_loop= get_or_create_event_loop()
        self._lock_for_count_execute_task_times_every_unit_time = Lock()

        # self._unit_time_for_count = 10  # Count every how many seconds; shows how many times executed per unit time. Temporarily fixed at 10 seconds.
        # self._execute_task_times_every_unit_time = 0  # How many times tasks were executed per unit time.
        # self._execute_task_times_every_unit_time_fail =0  # How many times tasks failed per unit time.
        # self._lock_for_count_execute_task_times_every_unit_time = Lock()
        # self._current_time_for_execute_task_times_every_unit_time = time.time()
        # self._consuming_function_cost_time_total_every_unit_time = 0
        # self._last_execute_task_time = time.time()  # Time of the most recent task execution.
        # self._last_10s_execute_count = 0
        # self._last_10s_execute_count_fail = 0
        #
        # self._last_show_remaining_execution_time = 0
        # self._show_remaining_execution_time_interval = 300
        #
        # self._msg_num_in_broker = 0
        # self._last_timestamp_when_has_task_in_queue = 0
        # self._last_timestamp_print_msg_num = 0

        self.metric_calculation = MetricCalculation(self)

        self._result_persistence_helper: ResultPersistenceHelper
        self.consumer_params.broker_exclusive_config = generate_broker_exclusive_config(self.consumer_params.broker_kind, self.consumer_params.broker_exclusive_config, self.logger)

        self._stop_flag = None
        self._pause_flag = threading.Event()  # Pause consumption flag, read from Redis
        self._last_show_pause_log_time = 0
        # self._redis_key_stop_flag = f'funboost_stop_flag'
        # self._redis_key_pause_flag = RedisKeys.REDIS_KEY_PAUSE_FLAG

        # Member variables used for rate limiting
        self._last_submit_task_timestamp = 0
        self._last_start_count_qps_timestamp = time.time()
        self._has_execute_times_in_recent_second = 0
        
        self._last_judge_is_allow_run_by_cron_time = 0
        self._last_judge_is_allow_run_by_cron_result = True
        
        self._lock_for_get_publisher = Lock()
        self._publisher_of_same_queue = None  #
        self._dlx_queue_name = f'{self.queue_name}_dlx'
        self._publisher_of_dlx_queue = None  # Dead letter queue publisher

        self._do_not_delete_extra_from_msg = False
        self._concurrent_pool = None

        self.consumer_identification = f'{nb_log_config_default.computer_name}_{nb_log_config_default.computer_ip}_' \
                                       f'{time_util.DatetimeConverter().datetime_str.replace(":", "-")}_{os.getpid()}_{id(self)}'
        # noinspection PyUnresolvedReferences
        self.consumer_identification_map = {'queue_name': self.queue_name,
                                            'computer_name': nb_log_config_default.computer_name,
                                            'computer_ip': nb_log_config_default.computer_ip,
                                            'process_id': os.getpid(),
                                            'consumer_id': id(self),
                                            'consumer_uuid': str(uuid.uuid4()),
                                            'start_datetime_str': time_util.DatetimeConverter().datetime_str,
                                            'start_timestamp': time.time(),
                                            'hearbeat_datetime_str': time_util.DatetimeConverter().datetime_str,
                                            'hearbeat_timestamp': time.time(),
                                            'consuming_function': self.consuming_function.__name__,
                                            'code_filename': Path(self.consuming_function.__code__.co_filename).as_posix()
                                            }

        self._has_start_delay_task_scheduler = False
        self._consuming_function_is_asyncio = inspect.iscoroutinefunction(self.consuming_function)

        ConsumingFuncInputParamsChecker.gen_final_func_input_params_info(self.consumer_params)
        # print(self.consumer_params)

        # develop_logger.warning(consumer_params._log_filename)
        # self.publisher_params = PublisherParams(queue_name=consumer_params.queue_name, consuming_function=consumer_params.consuming_function,
        #                                         broker_kind=self.BROKER_KIND, log_level=consumer_params.log_level,
        #                                         logger_prefix=consumer_params.logger_prefix,
        #                                         create_logger_file=consumer_params.create_logger_file,
        #                                         log_filename=consumer_params.log_filename,
        #                                         logger_name=consumer_params.logger_name,
        #                                         broker_exclusive_config=self.consumer_params.broker_exclusive_config)
        self.publisher_params = BaseJsonAbleModel.init_by_another_model(PublisherParams, self.consumer_params)
        # print(self.publisher_params)
        self._init_advanced_retry_config()
        self.custom_init()
        if is_main_process:
            self.logger.info(f'Consumer configuration for {self.queue_name}:\n {self.consumer_params.json_str_value()}')

        atexit.register(self.join_dispatch_task_thread)

        self._save_consumer_params()

        if self.consumer_params.is_auto_start_consuming_message:
            _ = self.publisher_of_same_queue
            self.start_consuming_message()

    def _save_consumer_params(self):
        """
        Save the consumer parameters of the queue for viewing in the web interface.
        :return:
        """
        # pass
        if self.consumer_params.is_fake_booster is True:
            return
        if self.consumer_params.is_send_consumer_heartbeat_to_redis:
            RedisMixin().redis_db_frame.hmset(RedisKeys.FUNBOOST_QUEUE__CONSUMER_PARAMS,{self.queue_name: self.consumer_params.json_str_value()})
            RedisMixin().redis_db_frame.sadd(RedisKeys.FUNBOOST_ALL_QUEUE_NAMES, self.queue_name)
            RedisMixin().redis_db_frame.sadd(RedisKeys.FUNBOOST_ALL_IPS, nb_log_config_default.computer_ip)
            if self.consumer_params.project_name:
                RedisMixin().redis_db_frame.sadd(RedisKeys.FUNBOOST_ALL_PROJECT_NAMES, self.consumer_params.project_name)
                RedisMixin().redis_db_frame.sadd(RedisKeys.gen_funboost_project_name_key(self.consumer_params.project_name), self.queue_name)

       

    def _build_logger(self):
        logger_prefix = self.consumer_params.logger_prefix
        if logger_prefix != '':
            logger_prefix += '--'
            # logger_name = f'{logger_prefix}{self.__class__.__name__}--{concurrent_name}--{queue_name}--{self.consuming_function.__name__}'
        logger_name = self.consumer_params.logger_name or f'funboost.{logger_prefix}{self.__class__.__name__}--{self.queue_name}'
        self.logger_name = logger_name
        log_filename = self.consumer_params.log_filename or f'funboost.{self.queue_name}.log'
        self.logger = LogManager(logger_name, logger_cls=TaskIdLogger).get_logger_and_add_handlers(
            log_level_int=self.consumer_params.log_level,
            log_filename=log_filename if self.consumer_params.create_logger_file else None,
            error_log_filename=nb_log.generate_error_file_name(log_filename),
            formatter_template=FunboostCommonConfig.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER, )
        self.logger.info(f'Logs for queue {self.queue_name} are written to files {log_filename} and {nb_log.generate_error_file_name(log_filename)} in the {nb_log_config_default.LOG_PATH} folder')

    def _check_monkey_patch(self):
        if self.consumer_params.concurrent_mode == ConcurrentModeEnum.GEVENT:
            from funboost.concurrent_pool.custom_gevent_pool_executor import check_gevent_monkey_patch
            check_gevent_monkey_patch()
        elif self.consumer_params.concurrent_mode == ConcurrentModeEnum.EVENTLET:
            from funboost.concurrent_pool.custom_evenlet_pool_executor import check_evenlet_monkey_patch
            check_evenlet_monkey_patch()
        else:
            check_not_monkey()

    # def _log_error(self, msg, exc_info=None):
    #     self.logger.error(msg=f'{msg} \n', exc_info=exc_info, extra={'sys_getframe_n': 3})  # This changes the log stack level
    #     self.error_file_logger.error(msg=f'{msg} \n', exc_info=exc_info, extra={'sys_getframe_n': 3})
    #
    # def _log_critical(self, msg, exc_info=None):
    #     self.logger.critical(msg=f'{msg} \n', exc_info=exc_info, extra={'sys_getframe_n': 3})
    #     self.error_file_logger.critical(msg=f'{msg} \n', exc_info=exc_info, extra={'sys_getframe_n': 3})

    @property
    @decorators.synchronized
    def concurrent_pool(self):
        return self._concurrent_mode_dispatcher.build_pool()

    def custom_init(self):
        pass

    def _init_advanced_retry_config(self):
        if not self.consumer_params.is_using_advanced_retry:
            return
        cfg = self.consumer_params.advanced_retry_config
        self._adv_retry_mode = cfg['retry_mode']
        self._adv_retry_base_interval = cfg['retry_base_interval']
        self._adv_retry_multiplier = cfg['retry_multiplier']
        self._adv_retry_max_interval = cfg['retry_max_interval']
        self._adv_retry_jitter = cfg['retry_jitter']
        if self._adv_retry_mode not in ('sleep', 'requeue'):
            raise ValueError(f"advanced_retry_config's retry_mode must be 'sleep' or 'requeue', current value is '{self._adv_retry_mode}'")
        self.logger.info(
            f"Advanced retry enabled: mode={self._adv_retry_mode}, "
            f"base_interval={self._adv_retry_base_interval}s, multiplier={self._adv_retry_multiplier}, "
            f"max_interval={self._adv_retry_max_interval}s, jitter={self._adv_retry_jitter}"
        )

    

    def keep_circulating(self, time_sleep=0.001, exit_if_function_run_sucsess=False, is_display_detail_exception=True,
                         block=True, daemon=False):
        """A decorator that continuously runs a method at a specified interval.
        :param time_sleep: Loop interval time
        :param is_display_detail_exception
        :param exit_if_function_run_sucsess: Exit the loop if successful
        :param block: Whether to block on the current main thread.
        :param daemon: Whether the thread is a daemon thread
        """

        def _keep_circulating(func):
            @wraps(func)
            def __keep_circulating(*args, **kwargs):

                # noinspection PyBroadException
                def ___keep_circulating():
                    while 1:
                        if self._stop_flag == 1:
                            break
                        try:
                            result = func(*args, **kwargs)
                            if exit_if_function_run_sucsess:
                                return result
                        except BaseException as e:
                            log_msg = func.__name__ + '   runtime error\n ' + traceback.format_exc(
                                limit=10) if is_display_detail_exception else str(e)
                            # self.logger.error(msg=f'{log_msg} \n', exc_info=True)
                            # self.error_file_logger.error(msg=f'{log_msg} \n', exc_info=True)
                            self.logger.error(msg=log_msg, exc_info=True)
                        finally:
                            time.sleep(time_sleep)
                            # print(func,time_sleep)

                if block:
                    return ___keep_circulating()
                else:
                    threading.Thread(target=___keep_circulating, daemon=daemon).start()

            return __keep_circulating

        return _keep_circulating
    
    def _before_start_consuming_message_hook(self):
        pass

    # noinspection PyAttributeOutsideInit
    def start_consuming_message(self):
        # ConsumersManager.show_all_consumer_info()
        # noinspection PyBroadException
        pid_queue_name_tuple = (os.getpid(), self.queue_name)
        if pid_queue_name_tuple in funboost_lazy_impoter.BoostersManager.pid_queue_name__has_start_consume_set:
            self.logger.warning(f'{pid_queue_name_tuple} has already started consuming. Do not keep starting consumption; the funboost framework automatically prevents this.')  # Some people write messy code and call f.consume() countless times inside functions or for loops. A queue only needs to start consuming once; otherwise each start causes large performance overhead until the program crashes.
            return
        else:
            funboost_lazy_impoter.BoostersManager.pid_queue_name__has_start_consume_set.add(pid_queue_name_tuple)
        GlobalVars.has_start_a_consumer_flag = True
        try:
            self._concurrent_mode_dispatcher.check_all_concurrent_mode()
            self._check_monkey_patch()
        except BaseException:  # noqa
            traceback.print_exc()
            os._exit(4444)  # noqa
        self.logger.info(f'Starting to consume messages from {self._queue_name}')
        self._result_persistence_helper = ResultPersistenceHelper(self.consumer_params.function_result_status_persistance_conf, self.queue_name)

        self._distributed_consumer_statistics = DistributedConsumerStatistics(self)
        if self.consumer_params.is_send_consumer_heartbeat_to_redis:
            self._distributed_consumer_statistics.run()
            self.logger.warning(f'Distributed environment started, using Redis key hearbeat:{self._queue_name} to track active consumers, current consumer unique ID is {self.consumer_identification}')

        self.keep_circulating(60, block=False, daemon=False)(self.check_heartbeat_and_message_count)()
        if self.consumer_params.is_support_remote_kill_task:
            kill_remote_task.RemoteTaskKiller(self.queue_name, None).start_cycle_kill_task()
            self.consumer_params.is_show_message_get_from_broker = True  # Makes it easy for users to see the task_id of messages fetched from the queue, so they can use task_id to kill running tasks.
        if self.consumer_params.do_task_filtering:
            self._redis_filter.delete_expire_filter_task_cycle()  # This defaults to the RedisFilter class, which is a pass and does not run. So when using other message middleware modes, Redis does not need to be installed or configured.
        self._before_start_consuming_message_hook()
        if self.consumer_params.schedule_tasks_on_main_thread:
            self.keep_circulating(1, daemon=False)(self._dispatch_task)()
        else:
            self._concurrent_mode_dispatcher.schedulal_task_with_no_block()

    def _start_delay_task_scheduler(self):
        from funboost.timing_job import FsdfBackgroundScheduler
        from funboost.timing_job.apscheduler_use_redis_store import FunboostBackgroundSchedulerProcessJobsWithinRedisLock
        # print(self.consumer_params.delay_task_apsscheduler_jobstores_kind )
        if self.consumer_params.delay_task_apscheduler_jobstores_kind == 'redis':
            jobstores = {
                "default": RedisJobStore(**redis_manager.get_redis_conn_kwargs(),
                                         jobs_key=RedisKeys.gen_funboost_redis_apscheduler_jobs_key_by_queue_name(self.queue_name),
                                         run_times_key=RedisKeys.gen_funboost_redis_apscheduler_run_times_key_by_queue_name(self.queue_name),
                                         )
            }
            self._delay_task_scheduler = FunboostBackgroundSchedulerProcessJobsWithinRedisLock(timezone=FunboostCommonConfig.TIMEZONE, daemon=False,
                                                                                               jobstores=jobstores  # push method serialization with threading.lock
                                                                                               )
            self._delay_task_scheduler.set_process_jobs_redis_lock_key(
                RedisKeys.gen_funboost_apscheduler_redis_lock_key_by_queue_name(self.queue_name))
        elif self.consumer_params.delay_task_apscheduler_jobstores_kind == 'memory':
            jobstores = {"default": MemoryJobStore()}
            self._delay_task_scheduler = FsdfBackgroundScheduler(timezone=FunboostCommonConfig.TIMEZONE, daemon=False,
                                                                 jobstores=jobstores  # push method serialization with threading.lock
                                                                 )

        else:
            raise Exception(f'delay_task_apsscheduler_jobstores_kind is error: {self.consumer_params.delay_task_apscheduler_jobstores_kind}')

        # self._delay_task_scheduler.add_executor(ApschedulerThreadPoolExecutor(2))  # Only submits tasks to the concurrent pool; does not need many threads.
        # self._delay_task_scheduler.add_listener(self._apscheduler_job_miss, EVENT_JOB_MISSED)
        self._delay_task_scheduler.start()

        self.logger.warning('Starting delayed task scheduler')

    logger_apscheduler = get_logger('push_for_apscheduler_use_database_store', log_filename='push_for_apscheduler_use_database_store.log')

    @classmethod
    def _push_apscheduler_task_to_broker(cls, queue_name, msg):
        funboost_lazy_impoter.BoostersManager.get_or_create_booster_by_queue_name(queue_name).publish(msg)

    @abc.abstractmethod
    def _dispatch_task(self):
        """
        Each subclass must implement this method to define how to fetch messages from the middleware and add the function and its run parameters to the worker pool.

        The philosophy of funboost's _dispatch_task is: "I don't care how you get tasks from your system. I only require that once you have a task,
        you call self._submit_task(msg) to hand it to me for processing."

        Therefore, regardless of whether message fetching uses pull mode, push mode, or polling mode; whether it fetches one message at a time or multiple in batch;
        whether it's traditional MQ, kafka, databases, socket/grpc/tcp, kombu, Python task frameworks like celery/rq/dramatiq,
        file systems, or the popular MySQL CDC (change data capture) — anything can easily be extended as funboost middleware.

        _dispatch_task is the core that allows anything to be a broker. Nothing cannot be a broker; extensibility is unmatched.

        :return:
        """

        """
        In contrast, with celery, because kombu forcibly emulates the classic AMQP protocol, only RabbitMQ works perfectly as a celery broker.
        When Redis is used as a celery broker, consumption acknowledgment (ACK) uses visibility_timeout, which is a terrible approach.
        Force-restarting the program after a power cut either causes orphan messages to be requeued too slowly, or treats long-running tasks as orphan messages and endlessly re-queues them.

        Implementing Kafka as a celery broker has been an open issue for over a decade and has never been perfectly realized — this is the limitation of celery+kombu.
        Not to mention using MySQL CDC as a celery broker. funboost's design is far superior to celery in this regard.
        """

        raise NotImplementedError

    def _convert_msg_before_run(self, msg: typing.Union[str, dict]) -> dict:
        """
        Convert the message when it was not sent using funboost and does not have the extra-related fields.
        Users can also follow the 4.21 documentation, inherit any Consumer class, and implement the _user_convert_msg_before_run method to first convert non-standard messages.
        """
        """ A typical message looks at least like this:
        {
          "a": 42,
          "b": 84,
          "extra": {
            "task_id": "queue_2_result:9b79a372-f765-4a33-8639-9d15d7a95f61",
            "publish_time": 1701687443.3596,
            "publish_time_format": "2023-12-04 18:57:23"
          }
        }
        """

        """
        extra_params = {'task_id': task_id, 'publish_time': round(time.time(), 4),
                        'publish_time_format': time.strftime('%Y-%m-%d %H:%M:%S')}
        """
        msg = self._user_convert_msg_before_run(msg)
        msg = Serialization.to_dict(msg)
        # The following cleans and fills in the fields.
        if 'extra' not in msg:
            msg['extra'] = {'is_auto_fill_extra': True}
        extra = msg['extra']
        if 'task_id' not in extra:
            extra['task_id'] = MsgGenerater.generate_task_id(self._queue_name)
        if 'publish_time' not in extra:
            extra['publish_time'] = MsgGenerater.generate_publish_time()
        if 'publish_time_format' not in extra:  # Bug fix: originally was `if 'publish_time_format':` which was always True
            extra['publish_time_format'] = MsgGenerater.generate_publish_time_format()
        return msg

    def _user_convert_msg_before_run(self, msg: typing.Union[str, dict]) -> dict:
        """
        Users can also pre-process/clean data here
        """
        # print(msg)
        return msg

    def _submit_task(self, kw):
        kw['body'] = self._convert_msg_before_run(kw['body'])
        self._print_message_get_from_broker(kw['body'])
        self._judge_is_allow_run_by_cron()
        if self._last_judge_is_allow_run_by_cron_result is False:
            self._requeue(kw)
            time.sleep(self._time_interval_for_check_allow_run_by_cron)
            return
        function_only_params = get_func_only_params(kw['body'], )
        kw['function_only_params'] = function_only_params
        publish_time = get_publish_time(kw['body'])
        msg_expire_seconds_priority = self._get_priority_conf(kw, 'msg_expire_seconds')
        if msg_expire_seconds_priority:
            # Optimization: call time.time() only once
            current_time = time.time()
            if current_time - msg_expire_seconds_priority > publish_time:
                self.logger.warning(
                    f'Message publish timestamp is {publish_time} {kw["body"].get("publish_time_format", "")}, elapsed {round(current_time - publish_time, 4)} seconds since now,'
                    f' exceeded the specified {msg_expire_seconds_priority} seconds, discarding task')
                self._confirm_consume(kw)
                return

        if self._should_filter_task(kw, function_only_params):
            task_id = kw['body']['extra']['task_id']
            current_function_result_status = FunctionResultStatus(
                self.queue_name, self.consuming_function.__name__, kw['body'], function_only_params)
            self._handle_filtered_task(kw, task_id, current_function_result_status)
            return

        msg_eta = self._get_priority_conf(kw, 'eta')
        msg_countdown = self._get_priority_conf(kw, 'countdown')
        misfire_grace_time = self._get_priority_conf(kw, 'misfire_grace_time')
        run_date = None
        # print(kw)
        if msg_countdown:
            run_date = FunboostTime(kw['body']['extra']['publish_time']).datetime_obj + datetime.timedelta(seconds=msg_countdown)
        if msg_eta:
            run_date = FunboostTime(msg_eta).datetime_obj
        # print(run_date,time_util.DatetimeConverter().datetime_obj)
        # print(run_date.timestamp(),time_util.DatetimeConverter().datetime_obj.timestamp())
        # print(self.concurrent_pool)
        if run_date:  # delayed task
            # print(repr(run_date),repr(datetime.datetime.now(tz=pytz.timezone(frame_config.TIMEZONE))))
            if self._has_start_delay_task_scheduler is False:
                self._has_start_delay_task_scheduler = True
                self._start_delay_task_scheduler()

            # This approach submits to the thread pool
            # self._delay_task_scheduler.add_job(self.concurrent_pool.submit, 'date', run_date=run_date, args=(self._any_run,), kwargs={'kw': kw},
            #                                    misfire_grace_time=misfire_grace_time)

            # This approach re-sends the delayed task as a normal task to the message queue
            # Optimization: use shallow copy + extra dict comprehension to avoid full deepcopy
            body = kw['body']
            if isinstance(body, str):
                body = Serialization.to_dict(body)
            # Shallow copy of the message, with special handling for the extra dict (excluding delay-related keys)
            msg_no_delay = dict(body)
            if 'extra' in msg_no_delay:
                # Create a new extra dict, excluding delay task related keys
                msg_no_delay['extra'] = {k: v for k, v in msg_no_delay['extra'].items() 
                                         if k not in ('eta', 'countdown', 'misfire_grace_time')}
            # print(msg_no_delay)
            # When using a database as apscheduler's jobstores, self.publisher_of_same_queue.publish cannot be used because self cannot be serialized
            self._delay_task_scheduler.add_job(self._push_apscheduler_task_to_broker, 'date', run_date=run_date,
                                               kwargs={'queue_name': self.queue_name, 'msg': msg_no_delay, },
                                               misfire_grace_time=misfire_grace_time,
                                               )
            self._confirm_consume(kw)

        else:  # Normal task
            self.concurrent_pool.submit(self._any_run, kw)

        if self.consumer_params.is_using_distributed_frequency_control:  # If distributed rate limiting is needed.
            active_num = self._distributed_consumer_statistics.active_consumer_num
            self._frequency_control(self.consumer_params.qps / active_num, self._msg_schedule_time_intercal * active_num)
        else:
            self._frequency_control(self.consumer_params.qps, self._msg_schedule_time_intercal)

        while 1:  # This block of code supports pausing consumption.
            # print(self._pause_flag)
            if self._pause_flag.is_set():
                if time.time() - self._last_show_pause_log_time > 60:
                    self.logger.warning(f'Tasks in queue {self.queue_name} have been set to paused consumption')
                    self._last_show_pause_log_time = time.time()
                time.sleep(5)
            else:
                break

    # def __delete_eta_countdown(self, msg_body: dict):
    #     self.__dict_pop(msg_body.get('extra', {}), 'eta')
    #     self.__dict_pop(msg_body.get('extra', {}), 'countdown')
    #     self.__dict_pop(msg_body.get('extra', {}), 'misfire_grace_time')

    # @staticmethod
    # def __dict_pop(dictx, key):
    #     try:
    #         dictx.pop(key)
    #     except KeyError:
    #         pass

    def _frequency_control(self, qpsx: float, msg_schedule_time_intercalx: float):
        # The following is the QPS control code for the consuming function. Whether for single-consumer rate limiting or distributed rate limiting, it is based on direct calculation without relying on Redis incr counting, which improves rate limiting performance.
        if qpsx is None:  # When rate limiting is not needed, no sleep is required.
            return
        if qpsx <= 5:
            """ Original simple version """
            time.sleep(msg_schedule_time_intercalx)
        elif 5 < qpsx <= 20:
            """ Improved rate control version to prevent network fluctuations in the message queue middleware. For example, at 1000 QPS with Redis, you cannot fetch the next message at 1ms intervals each time.
            If fetching a message takes more than 1ms, you cannot maintain uniform 1ms intervals afterward, and time.sleep cannot sleep a negative number to go back in time. """
            time_sleep_for_qps_control = max((msg_schedule_time_intercalx - (time.time() - self._last_submit_task_timestamp)) * 0.99, 10 ** -3)
            # print(time.time() - self._last_submit_task_timestamp)
            # print(time_sleep_for_qps_control)
            time.sleep(time_sleep_for_qps_control)
            self._last_submit_task_timestamp = time.time()
        else:
            """Rate limiting based on current consumer count, needed when QPS is very high"""
            if time.time() - self._last_start_count_qps_timestamp > 1:
                self._has_execute_times_in_recent_second = 1
                self._last_start_count_qps_timestamp = time.time()
            else:
                self._has_execute_times_in_recent_second += 1
            # print(self._has_execute_times_in_recent_second)
            if self._has_execute_times_in_recent_second >= qpsx:
                time.sleep((1 - (time.time() - self._last_start_count_qps_timestamp)) * 1)

    def _print_message_get_from_broker(self, msg, broker_name=None):
        # Optimization: check log level and config first to avoid unnecessary string formatting and JSON serialization
        if self.consumer_params.is_show_message_get_from_broker and self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f'Message fetched from {broker_name or self.consumer_params.broker_kind} middleware queue {self._queue_name}: {Serialization.to_json_str(msg)}')

    def _get_priority_conf(self, kw: dict, broker_task_config_key: str):
        broker_task_config = kw['body'].get('extra', {}).get(broker_task_config_key, None)
        if not broker_task_config:
            return getattr(self.consumer_params, f'{broker_task_config_key}', None)
        else:
            return broker_task_config

    # noinspection PyMethodMayBeStatic
    def _get_concurrent_info(self):
        concurrent_info = ''
        '''  Affects log length and slightly impacts performance.
        if self._concurrent_mode == 1:
            concurrent_info = f'[{threading.current_thread()}  {threading.active_count()}]'
        elif self._concurrent_mode == 2:
            concurrent_info = f'[{gevent.getcurrent()}  {threading.active_count()}]'
        elif self._concurrent_mode == 3:
            # noinspection PyArgumentList
            concurrent_info = f'[{eventlet.getcurrent()}  {threading.active_count()}]'
        '''
        return concurrent_info

    def _set_do_not_delete_extra_from_msg(self):
        """For example, when moving a complete message including extra from the dead letter queue to another normal queue, do not remove the parameters in extra.
        This is used in queue2queue.py's consume_and_push_to_another_queue. Regular users do not need to call this method.
        """
        self._do_not_delete_extra_from_msg = True

    def _frame_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus, kw: dict):
        pass

    async def _aio_frame_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus, kw: dict):
        pass

    def _both_sync_and_aio_frame_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus, kw: dict):
        pass

    def user_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus, ):  # This can be overridden by inheritance
        pass

    async def aio_user_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus, ):  # This can be overridden by inheritance
        pass

    def _convert_real_function_only_params_by_conusuming_function_kind(self, function_only_params: dict, extra_params: dict):
        """For instance methods and class methods, restore the first parameter (self and cls) from the message queue message"""
        can_not_json_serializable_keys = extra_params.get('can_not_json_serializable_keys', [])
        if self.consumer_params.consuming_function_kind in [FunctionKind.CLASS_METHOD, FunctionKind.INSTANCE_METHOD]:
            real_function_only_params = copy.copy(function_only_params)
            method_first_param_name = None
            method_first_param_value = None
            for k, v in function_only_params.items():
                if isinstance(v, dict) and ConstStrForClassMethod.FIRST_PARAM_NAME in v:
                    method_first_param_name = k
                    method_first_param_value = v
                    break
            # method_cls = getattr(sys.modules[self.consumer_params.consuming_function_class_module],
            #                      self.consumer_params.consuming_function_class_name)
            if self.publisher_params.consuming_function_kind == FunctionKind.CLASS_METHOD:
                method_cls = getattr(PathHelper.import_module(method_first_param_value[ConstStrForClassMethod.CLS_MODULE]),
                                     method_first_param_value[ConstStrForClassMethod.CLS_NAME])
                real_function_only_params[method_first_param_name] = method_cls
            elif self.publisher_params.consuming_function_kind == FunctionKind.INSTANCE_METHOD:
                method_cls = getattr(PathHelper.import_module(method_first_param_value[ConstStrForClassMethod.CLS_MODULE]),
                                     method_first_param_value[ConstStrForClassMethod.CLS_NAME])
                obj = method_cls(**method_first_param_value[ConstStrForClassMethod.OBJ_INIT_PARAMS])
                real_function_only_params[method_first_param_name] = obj
            # print(real_function_only_params)
            if can_not_json_serializable_keys:
                for key in can_not_json_serializable_keys:
                    real_function_only_params[key] = PickleHelper.to_obj(real_function_only_params[key])
            return real_function_only_params
        else:
            if can_not_json_serializable_keys:
                for key in can_not_json_serializable_keys:
                    function_only_params[key] = PickleHelper.to_obj(function_only_params[key])
            return function_only_params
     
    def _set_rpc_result(self,
             task_id:str,
             kw:dict,
             current_function_result_status:FunctionResultStatus,
             current_retry_times:int,
             redis_retry_times:int=3,
             ):
        if self._get_priority_conf(kw, 'is_using_rpc_mode') is True:
            max_retry_times = self._get_priority_conf(kw, 'max_retry_times')
            # print(function_result_status.get_status_dict(without_datetime_obj=
            if (current_function_result_status.success is False and current_retry_times == max_retry_times) or current_function_result_status.success is True:
                for i in range(redis_retry_times):
                    # Some users reported this can still fail; added retry
                    try:
                        with RedisMixin().redis_db_filter_and_rpc_result.pipeline() as p:
                            current_function_result_status.rpc_result_expire_seconds = self.consumer_params.rpc_result_expire_seconds
                            p.lpush(task_id,
                                    Serialization.to_json_str(current_function_result_status.get_status_dict(without_datetime_obj=True)))
                            p.expire(task_id, self.consumer_params.rpc_result_expire_seconds)
                            p.execute()
                    except Exception:
                        err_msg = f'Failed to set rpc result {task_id} {current_function_result_status.get_status_dict(without_datetime_obj=True)}'
                        if i == redis_retry_times - 1:
                            self.logger.critical(err_msg, exc_info=True)
                        else:
                            self.logger.error(err_msg, exc_info=True)
    
    @staticmethod
    def _calculate_exponential_backoff(current_retry_times, base_interval, multiplier, max_interval, jitter):
        """Calculate the retry interval for exponential backoff"""
        interval = base_interval * (multiplier ** current_retry_times)
        interval = min(interval, max_interval)
        if jitter:
            interval = interval * (0.5 + random.random())
            interval = min(interval, max_interval)
        return interval
    
    def _get_retry_range(self, kw, max_retry_times):
        """Return the iteration range for retries.
        Non-advanced retry: full loop from 0 to max_retry_times.
        Advanced retry requeue mode: each consumption attempt is made only once (starting from the retry count recorded in the message).
        """
        if self.consumer_params.is_using_advanced_retry and self._adv_retry_mode == 'requeue':
            adv_count = kw['body'].get('extra', {}).get(StrConst._ADVANCED_RETRY_COUNT, 0)
            return range(adv_count, adv_count + 1)
        return range(max_retry_times + 1)

    def _get_retry_interval(self, kw, current_retry_times):
        """Calculate the retry interval (seconds).
        Non-advanced retry: return 0 (retry immediately).
        Advanced retry: exponential backoff calculation.
        """
        if not self.consumer_params.is_using_advanced_retry:
            return 0
        return self._calculate_exponential_backoff(
            current_retry_times,
            self._adv_retry_base_interval,
            self._adv_retry_multiplier,
            self._adv_retry_max_interval,
            self._adv_retry_jitter,
        )

    def _wait_before_retry(self, kw, current_retry_times, interval):
        """Wait behavior before retrying. Returns True to continue the retry loop, False to break out.
        Advanced retry requeue mode: release the thread immediately after sending the message back to the queue.
        Advanced retry sleep mode / non-advanced retry: sleep in the current thread.
        """
        if self.consumer_params.is_using_advanced_retry and self._adv_retry_mode == 'requeue':
            self._republish_with_countdown(kw, current_retry_times + 1, interval)
            return False
        self.logger.info(
            f"Function {self.consuming_function.__name__} "
            f"failed on attempt {current_retry_times + 1}, waiting {interval:.1f}s before retrying"
        )
        time.sleep(interval)
        return True

    async def _async_wait_before_retry(self, kw, current_retry_times, interval):
        """Async version of wait behavior before retrying. Returns True to continue the retry loop, False to break out.
        Advanced retry requeue mode: release the coroutine immediately after sending the message back to the queue.
        Advanced retry sleep mode / non-advanced retry: sleep in the current coroutine.
        """
        if self.consumer_params.is_using_advanced_retry and self._adv_retry_mode == 'requeue':
            await simple_run_in_executor(self._republish_with_countdown, kw, current_retry_times + 1, interval)
            return False
        self.logger.info(
            f"Function {self.consuming_function.__name__} "
            f"failed on attempt {current_retry_times + 1}, waiting {interval:.1f}s before retrying"
        )
        await asyncio.sleep(interval)
        return True

    def _republish_with_countdown(self, kw, next_retry_count, countdown_seconds):
        """Re-publish the message with a countdown delay to the same queue, releasing the thread/coroutine"""
        body = kw['body']
        if isinstance(body, str):
            body = Serialization.to_dict(body)
        new_body = dict(body)
        new_extra = dict(new_body.get('extra', {}))
        new_extra[StrConst._ADVANCED_RETRY_COUNT] = next_retry_count
        new_extra.pop('eta', None)
        new_extra.pop('countdown', None)
        new_extra['countdown'] = countdown_seconds
        new_extra['publish_time'] = round(time.time(), 4)
        new_extra['publish_time_format'] = time.strftime('%Y-%m-%d %H:%M:%S')
        new_body['extra'] = new_extra
        self.publisher_of_same_queue.publish(new_body)
        self.logger.info(
            f"[retry-requeue] Function {self.consuming_function.__name__} "
            f"retry #{next_retry_count}, message has been sent back to queue, will be re-consumed after {countdown_seconds:.1f}s delay"
        )

    def _should_filter_task(self, kw, function_only_params):
        """Determine whether a task should be filtered (same input parameters have already been successfully executed).
        In advanced retry requeue mode, retry messages that have not yet exhausted their retry count will not be filtered.
        """
        if not self._get_priority_conf(kw, 'do_task_filtering'):
            return False
        if not self._redis_filter.check_value_exists(function_only_params, self._get_priority_conf(kw, 'filter_str')):
            return False
        if self.consumer_params.is_using_advanced_retry and self._adv_retry_mode == 'requeue':
            adv_count = kw['body'].get('extra', {}).get(StrConst._ADVANCED_RETRY_COUNT, 0)
            if 0 < adv_count <= self._get_priority_conf(kw, 'max_retry_times'):
                return False
        return True

    def _handle_filtered_task(self, kw, task_id, current_function_result_status:FunctionResultStatus):
        """Handle a filtered task: confirm consumption and set the RPC result so the publisher does not wait forever."""
        self.logger.warning(f'Task filtered in Redis key [{self._redis_filter_key_name}]: {kw["body"]}')
        self._confirm_consume(kw)
        current_function_result_status.success = False # Function input parameters were filtered, message was not executed, set to False.
        current_function_result_status.result = StrConst.FILTERED_TASK_RESULT # Function input parameters were filtered, message was not executed.
        self._set_rpc_result(task_id, kw, current_function_result_status, 0)

    # noinspection PyProtectedMember
    def _run(self, kw: dict, ):
        # print(kw)
        # Optimization: pass in already-computed function_only_params to avoid redundant computation
        function_only_params = kw['function_only_params']
        current_function_result_status = FunctionResultStatus(self.queue_name, self.consuming_function.__name__, kw['body'], function_only_params)
        fct_context = FctContext(function_result_status=current_function_result_status,
                                 logger=self.logger, )
        set_fct_context(fct_context)
        task_id = kw['body']['extra']['task_id']
        try:
            
            t_start_run_fun = time.time()
            max_retry_times = self._get_priority_conf(kw, 'max_retry_times')
            current_retry_times = 0
            for current_retry_times in self._get_retry_range(kw, max_retry_times):
                current_function_result_status.run_times = current_retry_times + 1
                current_function_result_status.run_status = RunStatus.running
                self._result_persistence_helper.save_function_result_to_mongo(current_function_result_status)
                current_function_result_status = self._run_consuming_function_with_confirm_and_retry(kw, current_retry_times=current_retry_times,
                                                                                                     function_result_status=current_function_result_status)
                if (current_function_result_status.success is True or current_retry_times == max_retry_times
                        or current_function_result_status._has_requeue
                        or current_function_result_status._has_to_dlx_queue
                        or current_function_result_status._has_kill_task):
                    break
                else:
                    interval = self._get_retry_interval(kw, current_retry_times)
                    if interval:
                        if not self._wait_before_retry(kw, current_retry_times, interval):
                            break
            if not (current_function_result_status._has_requeue and self.BROKER_KIND in [BrokerEnum.RABBITMQ_AMQPSTORM, BrokerEnum.RABBITMQ_PIKA, BrokerEnum.RABBITMQ_RABBITPY]):  # Already nacked; cannot ack, otherwise rabbitmq delivery tag error
                self._confirm_consume(kw)
            current_function_result_status.run_status = RunStatus.finish
            current_function_result_status.time_end = time.time()
            current_function_result_status.time_cost = round(current_function_result_status.time_end - current_function_result_status.time_start, 4)
            self._result_persistence_helper.save_function_result_to_mongo(current_function_result_status)
            if self._get_priority_conf(kw, 'do_task_filtering'):
                self._redis_filter.add_a_value(function_only_params, self._get_priority_conf(kw, 'filter_str'))  # After successful function execution, add the sorted key-value pair string of function parameters to the set.
            if current_function_result_status.success is False and current_retry_times == max_retry_times:
                log_msg = f'Function {self.consuming_function.__name__} reached max retry times {self._get_priority_conf(kw, "max_retry_times")} and still failed, input params: {function_only_params} '
                if self.consumer_params.is_push_to_dlx_queue_when_retry_max_times:
                    log_msg += f'  . Sending to dead letter queue {self._dlx_queue_name}'
                    self.publisher_of_dlx_queue.publish(kw['body'])
                # self.logger.critical(msg=f'{log_msg} \n', )
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)

            self._set_rpc_result(task_id, kw, current_function_result_status, current_retry_times)

            with self._lock_for_count_execute_task_times_every_unit_time:
                self.metric_calculation.cal(t_start_run_fun, current_function_result_status)
            self._both_sync_and_aio_frame_custom_record_process_info_func(current_function_result_status, kw)
            self._frame_custom_record_process_info_func(current_function_result_status, kw)
            self.user_custom_record_process_info_func(current_function_result_status, )  # Both methods can be customized to record results; the inheritance approach is recommended over specifying user_custom_record_process_info_func in boost
            if self.consumer_params.user_custom_record_process_info_func:
                self.consumer_params.user_custom_record_process_info_func(current_function_result_status, )
        except BaseException as e:
            log_msg = f' error critical error {type(e)} {e} '
            # self.logger.critical(msg=f'{log_msg} \n', exc_info=True)
            # self.error_file_logger.critical(msg=f'{log_msg} \n', exc_info=True)
            self.logger.critical(msg=log_msg, exc_info=True)
        set_fct_context(None)
        return current_function_result_status


    # noinspection PyProtectedMember
    def _run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times,
                                                       function_result_status: FunctionResultStatus, ):
        function_only_params = kw['function_only_params'] if self._do_not_delete_extra_from_msg is False else kw['body']
        
        t_start = time.time()
        task_id = kw['body']['extra']['task_id']
        try:
            
            function_run = self.consuming_function
            
            if self._consuming_function_is_asyncio:
                function_run = sync_or_async_fun_deco(function_run)
            function_timeout = self._get_priority_conf(kw, 'function_timeout')
            function_run = function_run if self.consumer_params.consuming_function_decorator is None else self.consumer_params.consuming_function_decorator(function_run)
            function_run = function_run if not function_timeout else self._concurrent_mode_dispatcher.timeout_deco(
                function_timeout)(function_run)

            if self.consumer_params.is_support_remote_kill_task:
                if kill_remote_task.RemoteTaskKiller(self.queue_name, task_id).judge_need_revoke_run():  # If a remote command kills the task and the function hasn't started yet, cancel execution
                    function_result_status._has_kill_task = True
                    self.logger.warning(f'Cancelling execution of {task_id} {function_only_params}')
                    return function_result_status
                function_run = kill_remote_task.kill_fun_deco(task_id)(function_run)  # Wrap with kill decorator to run the function in another thread, enabling remote kill waiting.
            function_result_status.result = function_run(**self._convert_real_function_only_params_by_conusuming_function_kind(function_only_params, kw['body']['extra']))
            function_result_status.success = True
            # Optimization: use isEnabledFor to check log level, avoiding unnecessary string formatting
            if self.logger.isEnabledFor(logging.DEBUG):
                result_str_to_be_print = str(function_result_status.result)[:100] if len(str(function_result_status.result)) < 100 else str(function_result_status.result)[:100] + '  ......  '
                self.logger.debug(f' Function {self.consuming_function.__name__}  '
                                  f'run #{current_retry_times + 1}, succeeded, function runtime is {round(time.time() - t_start, 4)} seconds, input params: {function_only_params} , '
                                  f'result: {result_str_to_be_print}   {self._get_concurrent_info()}  ')
        except BaseException as e:
            if isinstance(e, (ExceptionForRequeue,)):  # When Mongo is frequently in maintenance/backup mode and cannot insert or goes down, or when you actively raise an ExceptionForRequeue error, the message will be re-queued, not limited by the specified retry count.
                log_msg = f'Error occurred in function [{self.consuming_function.__name__}] {type(e)}  {e}. Message re-queued to current queue {self._queue_name}'
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                time.sleep(0.1)  # Prevent rapid infinite error-enqueue-dequeue cycles that would overload CPU and middleware
                self._requeue(kw)
                function_result_status._has_requeue = True
            if isinstance(e, ExceptionForPushToDlxqueue):
                log_msg = f'Error occurred in function [{self.consuming_function.__name__}] {type(e)}  {e}, message sent to dead letter queue {self._dlx_queue_name}'
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                self.publisher_of_dlx_queue.publish(kw['body'])  # Publish to dead letter queue, not back to current queue
                function_result_status._has_to_dlx_queue = True
            if isinstance(e, kill_remote_task.TaskHasKilledError):
                log_msg = f'task_id: {task_id}, function [{self.consuming_function.__name__}] with input params {function_only_params} has been killed by remote command {type(e)}  {e}'
                # self.logger.critical(msg=f'{log_msg} ')
                # self.error_file_logger.critical(msg=f'{log_msg} ')
                self.logger.critical(msg=log_msg)
                function_result_status._has_kill_task = True
            if isinstance(e, (ExceptionForRequeue, ExceptionForPushToDlxqueue, kill_remote_task.TaskHasKilledError)):
                return function_result_status
            log_msg = f'''Function {self.consuming_function.__name__}  error on run #{current_retry_times + 1},
                          function runtime was {round(time.time() - t_start, 4)} seconds, input params: {function_only_params}
                          {type(e)} {e} '''
            # self.logger.error(msg=f'{log_msg} \n', exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            # self.error_file_logger.error(msg=f'{log_msg} \n', exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            self.logger.error(msg=log_msg, exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            # traceback.print_exc()
            function_result_status.exception = f'{e.__class__.__name__}    {str(e)}'
            function_result_status.exception_msg = str(e)
            function_result_status.exception_type = e.__class__.__name__

            function_result_status.result = FunctionResultStatus.FUNC_RUN_ERROR
        return function_result_status

    def _gen_asyncio_objects(self):
        if getattr(self, '_async_lock_for_count_execute_task_times_every_unit_time', None) is None:
            self._async_lock_for_count_execute_task_times_every_unit_time = asyncio.Lock()

    # noinspection PyProtectedMember
    async def _async_run(self, kw: dict, ):
        """
        Although async def _async_run and the def _run above share a lot of structural similarity, this one is for asyncio mode.
        The asyncio mode really differs greatly from ordinary synchronous mode in terms of code thinking and form.
        Making the framework compatible with async consuming functions is complex and troublesome, even the concurrent pool needs to be written separately.

        _run and _async_run cannot be merged into one method:
        because inside a function body, you cannot conditionally decide whether to use await.

        Python syntax does not allow this:
        # Pseudocode, this is invalid
        def _unified_run(self, kw, is_async):
            # ...
            if is_async:
                await asyncio.sleep(1) # 'await' outside async function - classic error
            else:
                time.sleep(1)

        You cannot write await inside a synchronous function. Once await appears in a function, it must be declared as async def.



        The cost for funboost is relatively small — to support the full asyncio ecosystem including publishing/consuming/getting RPC results, the total dedicated code for asyncio is less than 500 lines.
        If celery were to be adapted for asyncio, it would require at least 10x more code changes, and modifying 5000 lines still wouldn't achieve true asyncio concurrency support.
        What I mean is supporting genuine asyncio concurrency, not each thread creating a temporary loop and calling loop.run_until_complete(user_async_function) — that is fake asyncio concurrency.
        True asyncio concurrency runs countless coroutines inside a single loop.
        Fake asyncio concurrency starts a temporary loop in each thread, with each loop running only one coroutine and waiting for it to finish — this completely violates the core philosophy of asyncio and performs even worse than multi-threading.
        """
        # Optimization: pass in already-computed function_only_params to avoid redundant computation
        function_only_params = kw['function_only_params']
        current_function_result_status = FunctionResultStatus(self.queue_name, self.consuming_function.__name__, kw['body'], function_only_params)
        fct_context = FctContext(function_result_status=current_function_result_status,
                                 logger=self.logger, )
        set_fct_context(fct_context)
        task_id = kw['body']['extra']['task_id']
        try:
            self._gen_asyncio_objects()
            t_start_run_fun = time.time()
            max_retry_times = self._get_priority_conf(kw, 'max_retry_times')
            current_retry_times = 0
            function_only_params = kw['function_only_params']
            for current_retry_times in self._get_retry_range(kw, max_retry_times):
                current_function_result_status.run_times = current_retry_times + 1
                current_function_result_status.run_status = RunStatus.running
                self._result_persistence_helper.save_function_result_to_mongo(current_function_result_status)
                current_function_result_status = await self._async_run_consuming_function_with_confirm_and_retry(kw, current_retry_times=current_retry_times,
                                                                                                                  function_result_status=current_function_result_status)
                if current_function_result_status.success is True or current_retry_times == max_retry_times or current_function_result_status._has_requeue:
                    break
                else:
                    interval = self._get_retry_interval(kw, current_retry_times)
                    if interval:
                        if not await self._async_wait_before_retry(kw, current_retry_times, interval):
                            break

            if not (current_function_result_status._has_requeue and self.BROKER_KIND in [BrokerEnum.RABBITMQ_AMQPSTORM, BrokerEnum.RABBITMQ_PIKA, BrokerEnum.RABBITMQ_RABBITPY]):
                await simple_run_in_executor(self._confirm_consume, kw)
            current_function_result_status.run_status = RunStatus.finish
            current_function_result_status.time_end = time.time()
            current_function_result_status.time_cost = round(current_function_result_status.time_end - current_function_result_status.time_start, 4)
            await simple_run_in_executor(self._result_persistence_helper.save_function_result_to_mongo, current_function_result_status)
            if self._get_priority_conf(kw, 'do_task_filtering'):
                # self._redis_filter.add_a_value(function_only_params)  # After successful function execution, add the sorted key-value pair string of function parameters to the set.
                await simple_run_in_executor(self._redis_filter.add_a_value, function_only_params, self._get_priority_conf(kw, 'filter_str'))
            if current_function_result_status.success is False and current_retry_times == max_retry_times:
                log_msg = f'Function {self.consuming_function.__name__} reached max retry times {self._get_priority_conf(kw, "max_retry_times")} and still failed, input params: {function_only_params} '
                if self.consumer_params.is_push_to_dlx_queue_when_retry_max_times:
                    log_msg += f'  . Sending to dead letter queue {self._dlx_queue_name}'
                    await simple_run_in_executor(self.publisher_of_dlx_queue.publish, kw['body'])
                # self.logger.critical(msg=f'{log_msg} \n', )
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)

                # self._confirm_consume(kw)  # Exceeded the specified number of errors; confirm consumption.
            await simple_run_in_executor(self._set_rpc_result, task_id, kw, current_function_result_status, current_retry_times)
            async with self._async_lock_for_count_execute_task_times_every_unit_time:
                self.metric_calculation.cal(t_start_run_fun, current_function_result_status)

            self._both_sync_and_aio_frame_custom_record_process_info_func(current_function_result_status, kw)
            await self._aio_frame_custom_record_process_info_func(current_function_result_status, kw)
            await self.aio_user_custom_record_process_info_func(current_function_result_status, )
            if self.consumer_params.user_custom_record_process_info_func:
                await self.consumer_params.user_custom_record_process_info_func(current_function_result_status, )

        except BaseException as e:
            log_msg = f' error critical error {type(e)} {e} '
            # self.logger.critical(msg=f'{log_msg} \n', exc_info=True)
            # self.error_file_logger.critical(msg=f'{log_msg} \n', exc_info=True)
            self.logger.critical(msg=log_msg, exc_info=True)
        set_fct_context(None)
        return current_function_result_status

    # noinspection PyProtectedMember
    async def _async_run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times,
                                                                   function_result_status: FunctionResultStatus, ):
        """Although similar in structure to the method above, this one is for asyncio mode. The asyncio mode really differs greatly from ordinary synchronous mode in code thinking and form.
        Making the framework compatible with async consuming functions is complex and troublesome, and even the concurrent pool needs to be written separately."""
        function_only_params = kw['function_only_params'] if self._do_not_delete_extra_from_msg is False else kw['body']

        # noinspection PyBroadException
        t_start = time.time()
        try:
            corotinue_obj = self.consuming_function(**self._convert_real_function_only_params_by_conusuming_function_kind(function_only_params, kw['body']['extra']))
            if not asyncio.iscoroutine(corotinue_obj):
                log_msg = f'''The current concurrency mode is set to async, but the consuming function is not an async coroutine function. Please do not set the wrong concurrent_mode for consuming function {self.consuming_function.__name__}'''
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                # noinspection PyProtectedMember,PyUnresolvedReferences
                os._exit(444)
            if not self.consumer_params.function_timeout:
                rs = await corotinue_obj
                # rs = await asyncio.wait_for(corotinue_obj, timeout=4)
            else:
                rs = await asyncio.wait_for(corotinue_obj, timeout=self.consumer_params.function_timeout)
            function_result_status.result = rs
            function_result_status.success = True
            # Optimization: use isEnabledFor to check log level, avoiding unnecessary string formatting
            if self.logger.isEnabledFor(logging.DEBUG):
                result_str_to_be_print = str(rs)[:100] if len(str(rs)) < 100 else str(rs)[:100] + '  ......  '
                self.logger.debug(f' Function {self.consuming_function.__name__}  '
                                  f'run #{current_retry_times + 1}, succeeded, function runtime is {round(time.time() - t_start, 4)} seconds,'
                                  f'input params: [ {function_only_params} ], result: {result_str_to_be_print}  . {corotinue_obj} ')
        except BaseException as e:
            if isinstance(e, (ExceptionForRequeue,)):  # When Mongo is frequently in maintenance/backup mode and cannot insert or goes down, or when you actively raise an ExceptionForRequeue error, the message will be re-queued, not limited by the specified retry count.
                log_msg = f'Error occurred in function [{self.consuming_function.__name__}] {type(e)}  {e}. Message re-queued to current queue {self._queue_name}'
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                # time.sleep(1)  # Prevent rapid infinite error-enqueue-dequeue cycles that would overload CPU and middleware
                await asyncio.sleep(0.1)
                # return self._requeue(kw)
                await simple_run_in_executor(self._requeue, kw)
                function_result_status._has_requeue = True
            if isinstance(e, ExceptionForPushToDlxqueue):
                log_msg = f'Error occurred in function [{self.consuming_function.__name__}] {type(e)}  {e}, message sent to dead letter queue {self._dlx_queue_name}'
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                await simple_run_in_executor(self.publisher_of_dlx_queue.publish, kw['body'])  # Publish to dead letter queue, not back to current queue
                function_result_status._has_to_dlx_queue = True
            if isinstance(e, (ExceptionForRequeue, ExceptionForPushToDlxqueue)):
                return function_result_status
            log_msg = f'''Function {self.consuming_function.__name__}  error on run #{current_retry_times + 1},
                          function runtime was {round(time.time() - t_start, 4)} seconds, input params: {function_only_params}
                          reason: {type(e)} {e} '''
            # self.logger.error(msg=f'{log_msg} \n', exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            # self.error_file_logger.error(msg=f'{log_msg} \n', exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            self.logger.error(msg=log_msg, exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            function_result_status.exception = f'{e.__class__.__name__}    {str(e)}'
            function_result_status.exception_msg = str(e)
            function_result_status.exception_type = e.__class__.__name__
            function_result_status.result = FunctionResultStatus.FUNC_RUN_ERROR
        return function_result_status

    @abc.abstractmethod
    def _confirm_consume(self, kw):
        """Confirm consumption"""
        raise NotImplementedError

    def check_heartbeat_and_message_count(self):
        self.metric_calculation.msg_num_in_broker = self.publisher_of_same_queue.get_message_count()
        self.metric_calculation.last_get_msg_num_ts = time.time()
        if time.time() - self.metric_calculation.last_timestamp_print_msg_num > 600:
            if self.metric_calculation.msg_num_in_broker != -1:
                self.logger.info(f'Queue [{self._queue_name}] still has [{self.metric_calculation.msg_num_in_broker}] tasks')
            self.metric_calculation.last_timestamp_print_msg_num = time.time()
        if self.metric_calculation.msg_num_in_broker != 0:
            self.metric_calculation.last_timestamp_when_has_task_in_queue = time.time()
        return self.metric_calculation.msg_num_in_broker

    @abc.abstractmethod
    def _requeue(self, kw):
        """Re-queue the message"""
        raise NotImplementedError

    def _apscheduler_job_miss(self, event):
        """
        This is the event hook for the apscheduler package.
        ev.function_args = job.args
        ev.function_kwargs = job.kwargs
        ev.function = job.func
        :return:
        """
        # print(event.scheduled_run_time)
        misfire_grace_time = self._get_priority_conf(event.function_kwargs["kw"], 'misfire_grace_time')
        log_msg = f''' Current time is {time_util.DatetimeConverter().datetime_str}, compared to the task's scheduled run time {event.scheduled_run_time}, exceeded the specified {misfire_grace_time} seconds, abandoning task execution
                             {event.function_kwargs["kw"]["body"]} '''
        # self.logger.critical(msg=f'{log_msg} \n')
        # self.error_file_logger.critical(msg=f'{log_msg} \n')
        self.logger.critical(msg=log_msg)
        self._confirm_consume(event.function_kwargs["kw"])

        '''
        if self._get_priority_conf(event.function_kwargs["kw"], 'execute_delay_task_even_if_when_task_is_expired') is False:
            self.logger.critical(f'Current time is {time_util.DatetimeConverter().datetime_str}, the delayed run for this task has expired \n'
                                 f'{event.function_kwargs["kw"]["body"]}, this task is abandoned')
            self._confirm_consume(event.function_kwargs["kw"])
        else:
            self.logger.warning(f'Current time is {time_util.DatetimeConverter().datetime_str}, the delayed run for this task has expired \n'
                                f'{event.function_kwargs["kw"]["body"]},'
                                f'but the framework still runs it once to prevent task backlog from causing delayed consumption')
            event.function(*event.function_args, **event.function_kwargs)
        '''

    def pause_consume(self):
        """From a remote machine, you can set the queue to a paused consumption state. The funboost framework will automatically stop consuming. This feature requires Redis to be configured."""
        RedisMixin().redis_db_frame.hset(RedisKeys.REDIS_KEY_PAUSE_FLAG, self.queue_name, '1')

    def continue_consume(self):
        """From a remote machine, you can set the queue to resume consumption. The funboost framework will automatically continue consuming. This feature requires Redis to be configured."""
        RedisMixin().redis_db_frame.hset(RedisKeys.REDIS_KEY_PAUSE_FLAG, self.queue_name, '0')

    
    def _judge_is_allow_run_by_cron(self):
        allow_run_time_cron = self.consumer_params.allow_run_time_cron
        if allow_run_time_cron is None:
            self._last_judge_is_allow_run_by_cron_result = True
            return
        else:
            if time.time() - self._last_judge_is_allow_run_by_cron_time < self._time_interval_for_check_allow_run_by_cron:
                return 
            try:
                if croniter.match(allow_run_time_cron, datetime.datetime.now()):
                    self._last_judge_is_allow_run_by_cron_result = True
                else:
                    try:
                        opts = Options()
                        # opts.locale_code = 'zh_CN' # Use English description
                        opts.use_24hour_time_format = True
                        cron_desc = get_description(allow_run_time_cron, opts)
                        human_msg = f'({cron_desc}) '
                    except Exception:
                        human_msg = ''
                    self.logger.warning(f'Current time {time_util.DatetimeConverter()} is not within the allowed run range of allow_run_time_cron [{allow_run_time_cron}] {human_msg}, pausing execution')
                    self._last_judge_is_allow_run_by_cron_result = False
            except (Exception,BaseException) as e:
                self.logger.error(f'Cron expression configuration error {e}')
                self._last_judge_is_allow_run_by_cron_result = True
        self._last_judge_is_allow_run_by_cron_time = time.time()
        

    def wait_for_possible_has_finish_all_tasks(self, minutes: int = 3):
        """
        Determine whether all tasks in the queue have been consumed.
        Due to asynchronous consumption, a queue may be consumed while being pushed to, or a small number of tasks at the end may still be awaiting confirmation while the consumer has not yet fully finished running them. But sometimes there is a need to determine whether all tasks are complete — this provides an imprecise judgment. Understand the reasons and scenarios before using it cautiously.
        Generally, like celery, it runs as a permanently running background task that loops infinitely consuming tasks. But some users need to determine whether execution is complete.
        :param minutes: If the consumer has not executed any tasks for this many consecutive minutes AND there are no tasks in the message queue middleware, it is judged that consumption is complete. To account for long-running tasks, the judgment of completion is generally twice the specified minutes period.
        :return:

        """
        if minutes <= 1:
            raise ValueError('Suspected task completion. The judgment time must be at least 3 minutes, preferably 10 minutes')
        no_task_time = 0
        while 1:
            # noinspection PyBroadException
            message_count = self.metric_calculation.msg_num_in_broker
            # print(message_count,self._last_execute_task_time,time.time() - self._last_execute_task_time,no_task_time)
            if message_count == 0 and self.metric_calculation.last_execute_task_time != 0 and (time.time() - self.metric_calculation.last_execute_task_time) > minutes * 60:
                no_task_time += 30
            else:
                no_task_time = 0
            time.sleep(30)
            if no_task_time > minutes * 60:
                break

    def clear_filter_tasks(self):
        RedisMixin().redis_db_frame.delete(self._redis_filter_key_name)
        self.logger.warning(f'Cleared task filter for key {self._redis_filter_key_name}')

    def __str__(self):
        return f'Consumer for queue {self.queue_name} with function {self.consuming_function}'


# noinspection PyProtectedMember
class ConcurrentModeDispatcher(FunboostFileLoggerMixin):

    def __init__(self, consumerx: AbstractConsumer):
        self.consumer = consumerx
        self._concurrent_mode = self.consumer.consumer_params.concurrent_mode
        self.timeout_deco = None
        if self._concurrent_mode in (ConcurrentModeEnum.THREADING, ConcurrentModeEnum.SINGLE_THREAD):
            # self.timeout_deco = decorators.timeout
            self.timeout_deco = dafunc.func_set_timeout  # This timeout decorator has much better performance.
        elif self._concurrent_mode == ConcurrentModeEnum.GEVENT:
            from funboost.concurrent_pool.custom_gevent_pool_executor import gevent_timeout_deco
            self.timeout_deco = gevent_timeout_deco
        elif self._concurrent_mode == ConcurrentModeEnum.EVENTLET:
            from funboost.concurrent_pool.custom_evenlet_pool_executor import evenlet_timeout_deco
            self.timeout_deco = evenlet_timeout_deco
        # self.logger.info(f'{self.consumer} setting concurrent mode {self.consumer.consumer_params.concurrent_mode}')

    def check_all_concurrent_mode(self):
        if GlobalVars.global_concurrent_mode is not None and \
                self.consumer.consumer_params.concurrent_mode != GlobalVars.global_concurrent_mode:
            # print({self.consumer._concurrent_mode, ConsumersManager.global_concurrent_mode})
            if not {self.consumer.consumer_params.concurrent_mode, GlobalVars.global_concurrent_mode}.issubset({ConcurrentModeEnum.THREADING,
                                                                                                                ConcurrentModeEnum.ASYNC,
                                                                                                                ConcurrentModeEnum.SINGLE_THREAD}):
                # threading, asyncio, solo modes can coexist. But within the same interpreter, gevent + other concurrency modes cannot be combined, nor can eventlet + other concurrency modes.
                raise ValueError('''Due to monkey patching, two different concurrency types cannot be set in the same interpreter. Please check the displayed information for all consumers,
                                 search for the concurrent_mode keyword, and ensure all consumers in the current interpreter use only one concurrency mode (or compatible modes).
                                 asyncio, threading, and single_thread concurrency modes can coexist, but gevent and threading cannot coexist,
                                 and gevent and eventlet cannot coexist.''')

        GlobalVars.global_concurrent_mode = self.consumer.consumer_params.concurrent_mode

    def build_pool(self):
        if self.consumer._concurrent_pool is not None:
            return self.consumer._concurrent_pool

        pool_type = None  # Three duck-typing classes written following ThreadPoolExecutor, with identical public method names and functionality, interchangeable with each other.
        if self._concurrent_mode == ConcurrentModeEnum.THREADING:
            # pool_type = CustomThreadPoolExecutor
            # pool_type = BoundedThreadPoolExecutor
            pool_type = FlexibleThreadPool
        elif self._concurrent_mode == ConcurrentModeEnum.GEVENT:
            from funboost.concurrent_pool.custom_gevent_pool_executor import get_gevent_pool_executor
            pool_type = get_gevent_pool_executor
        elif self._concurrent_mode == ConcurrentModeEnum.EVENTLET:
            from funboost.concurrent_pool.custom_evenlet_pool_executor import get_eventlet_pool_executor
            pool_type = get_eventlet_pool_executor
        elif self._concurrent_mode == ConcurrentModeEnum.ASYNC:
            pool_type = AsyncPoolExecutor
        elif self._concurrent_mode == ConcurrentModeEnum.SINGLE_THREAD:
            pool_type = SoloExecutor
        # elif self._concurrent_mode == ConcurrentModeEnum.LINUX_FORK:
        #     pool_type = SimpleProcessPool
        # pool_type = BoundedProcessPoolExecutor
        # from concurrent.futures import ProcessPoolExecutor
        # pool_type = ProcessPoolExecutor
        if self._concurrent_mode == ConcurrentModeEnum.ASYNC:
            self.consumer._concurrent_pool = self.consumer.consumer_params.specify_concurrent_pool or pool_type(
                self.consumer.consumer_params.concurrent_num,
                specify_async_loop=self.consumer.consumer_params.specify_async_loop,
                is_auto_start_specify_async_loop_in_child_thread=self.consumer.consumer_params.is_auto_start_specify_async_loop_in_child_thread)
        else:
            # print(pool_type)
            self.consumer._concurrent_pool = self.consumer.consumer_params.specify_concurrent_pool or pool_type(self.consumer.consumer_params.concurrent_num)
        # print(self._concurrent_mode,self.consumer._concurrent_pool)
        return self.consumer._concurrent_pool

    # def schedulal_task_with_no_block(self):
    #     if ConsumersManager.schedual_task_always_use_thread:
    #         t = Thread(target=self.consumer.keep_circulating(1)(self.consumer._dispatch_task))
    #         ConsumersManager.schedulal_thread_to_be_join.append(t)
    #         t.start()
    #     else:
    #         if self._concurrent_mode in [ConcurrentModeEnum.THREADING, ConcurrentModeEnum.ASYNC,
    #                                      ConcurrentModeEnum.SINGLE_THREAD, ]:
    #             t = Thread(target=self.consumer.keep_circulating(1)(self.consumer._dispatch_task))
    #             ConsumersManager.schedulal_thread_to_be_join.append(t)
    #             t.start()
    #         elif self._concurrent_mode == ConcurrentModeEnum.GEVENT:
    #             import gevent
    #             g = gevent.spawn(self.consumer.keep_circulating(1)(self.consumer._dispatch_task), )
    #             ConsumersManager.schedulal_thread_to_be_join.append(g)
    #         elif self._concurrent_mode == ConcurrentModeEnum.EVENTLET:
    #             import eventlet
    #             g = eventlet.spawn(self.consumer.keep_circulating(1)(self.consumer._dispatch_task), )
    #             ConsumersManager.schedulal_thread_to_be_join.append(g)

    def schedulal_task_with_no_block(self):
        self.consumer.keep_circulating(1, block=False, daemon=False)(self.consumer._dispatch_task)()


def wait_for_possible_has_finish_all_tasks_by_conusmer_list(consumer_list: typing.List[AbstractConsumer], minutes: int = 3):
    """
   Determine whether multiple consumers have finished consuming.
   Due to asynchronous consumption, a queue may be consumed while being pushed to, or a small number of tasks at the end may still be awaiting confirmation while the consumer has not yet fully finished running them. But sometimes there is a need to determine whether all tasks are complete — this provides an imprecise judgment. Understand the reasons and scenarios before using it cautiously.
   Generally, like celery, it runs as a permanently running background task that loops infinitely consuming tasks. But some users need to determine whether execution is complete.
   :param consumer_list: List of multiple consumers
   :param minutes: If consumers have not executed any tasks for this many consecutive minutes AND there are no tasks in the message queue middleware, it is judged that consumption is complete. To account for long-running tasks, the judgment of completion is generally twice the specified minutes period.
   :return:

    """
    with BoundedThreadPoolExecutor(len(consumer_list)) as pool:
        for consumer in consumer_list:
            pool.submit(consumer.wait_for_possible_has_finish_all_tasks(minutes))


class MetricCalculation:
    """
    MetricCalculation tracks metrics such as the number of function executions, failures, average time cost, and remaining messages in the queue.
    When is_send_consumer_heartbeat_to_redis is set to True, this can be reported to Redis and displayed as charts in funboost_web_manager.


    Users can also use PrometheusConsumerMixin and PrometheusPushGatewayConsumerMixin to use
    the well-known Prometheus and Grafana systems for metric reporting and visualization.
    """
    UNIT_TIME_FOR_COUNT = 10  # Do not change this arbitrarily; other places depend on it. How often to count in seconds, displaying how many times executed per unit time. Currently fixed at 10 seconds.

    def __init__(self, conusmer: AbstractConsumer) -> None:
        self.consumer = conusmer

        self.unit_time_for_count = self.UNIT_TIME_FOR_COUNT  #
        self.execute_task_times_every_unit_time_temp = 0  # How many times tasks were executed per unit time.
        self.execute_task_times_every_unit_time_temp_fail = 0  # How many task executions failed per unit time.
        self.current_time_for_execute_task_times_every_unit_time = time.time()
        self.consuming_function_cost_time_total_every_unit_time_tmp = 0
        self.last_execute_task_time = time.time()  # The time of the most recent task execution.
        self.last_x_s_execute_count = 0
        self.last_x_s_execute_count_fail = 0
        self.last_x_s_avarage_function_spend_time = None
        self.last_show_remaining_execution_time = 0
        self.show_remaining_execution_time_interval = 300
        self.msg_num_in_broker = 0
        self.last_get_msg_num_ts = 0
        self.last_timestamp_when_has_task_in_queue = 0
        self.last_timestamp_print_msg_num = 0

        self.total_consume_count_from_start = 0
        self.total_consume_count_from_start_fail = 0
        self.total_cost_time_from_start = 0  # Total cumulative function execution time
        self.last_x_s_total_cost_time = None

    def cal(self, t_start_run_fun: float, current_function_result_status: FunctionResultStatus):
        self.last_execute_task_time = time.time()
        current_msg_cost_time = time.time() - t_start_run_fun
        self.execute_task_times_every_unit_time_temp += 1
        self.total_consume_count_from_start += 1
        self.total_cost_time_from_start += current_msg_cost_time
        if current_function_result_status.success is False:
            self.execute_task_times_every_unit_time_temp_fail += 1
            self.total_consume_count_from_start_fail += 1
        self.consuming_function_cost_time_total_every_unit_time_tmp += current_msg_cost_time

        if time.time() - self.current_time_for_execute_task_times_every_unit_time > self.unit_time_for_count:
            self.last_x_s_execute_count = self.execute_task_times_every_unit_time_temp
            self.last_x_s_execute_count_fail = self.execute_task_times_every_unit_time_temp_fail
            self.last_x_s_total_cost_time = self.consuming_function_cost_time_total_every_unit_time_tmp
            self.last_x_s_avarage_function_spend_time = round(self.last_x_s_total_cost_time / self.last_x_s_execute_count, 3)
            msg = f'Executed function [ {self.consumer.consuming_function.__name__} ] {self.last_x_s_execute_count} times in {self.unit_time_for_count} seconds,' \
                  f' failed {self.last_x_s_execute_count_fail} times, average function runtime {self.last_x_s_avarage_function_spend_time} seconds. '
            self.consumer.logger.info(msg)
            if time.time() - self.last_show_remaining_execution_time > self.show_remaining_execution_time_interval:
                self.msg_num_in_broker = self.consumer.publisher_of_same_queue.get_message_count()
                self.last_get_msg_num_ts = time.time()
                if self.msg_num_in_broker != -1:  # Some middlewares cannot count or haven't implemented queue remaining count statistics; they return -1 uniformly, and this message is not displayed.
                    need_time = time_util.seconds_to_hour_minute_second(self.msg_num_in_broker / (self.execute_task_times_every_unit_time_temp / self.unit_time_for_count) /
                                                                        self.consumer._distributed_consumer_statistics.active_consumer_num)
                    msg += f''' Estimated {need_time} remaining time to complete the {self.msg_num_in_broker} remaining tasks in queue {self.consumer.queue_name}'''
                    self.consumer.logger.info(msg)
                self.last_show_remaining_execution_time = time.time()
            if self.consumer.consumer_params.is_send_consumer_heartbeat_to_redis is True:
                RedisMixin().redis_db_frame.hincrby(RedisKeys.FUNBOOST_QUEUE__RUN_COUNT_MAP, self.consumer.queue_name, self.execute_task_times_every_unit_time_temp)
                RedisMixin().redis_db_frame.hincrby(RedisKeys.FUNBOOST_QUEUE__RUN_FAIL_COUNT_MAP, self.consumer.queue_name, self.execute_task_times_every_unit_time_temp_fail)

            self.current_time_for_execute_task_times_every_unit_time = time.time()
            self.consuming_function_cost_time_total_every_unit_time_tmp = 0
            self.execute_task_times_every_unit_time_temp = 0
            self.execute_task_times_every_unit_time_temp_fail = 0

    def get_report_hearbeat_info(self) -> dict:
        return {
            'unit_time_for_count': self.unit_time_for_count,
            'last_x_s_execute_count': self.last_x_s_execute_count,
            'last_x_s_execute_count_fail': self.last_x_s_execute_count_fail,
            'last_execute_task_time': self.last_execute_task_time,
            'last_x_s_avarage_function_spend_time': self.last_x_s_avarage_function_spend_time,
            # 'last_show_remaining_execution_time':self.last_show_remaining_execution_time,
            'msg_num_in_broker': self.msg_num_in_broker,
            'current_time_for_execute_task_times_every_unit_time': self.current_time_for_execute_task_times_every_unit_time,
            'last_timestamp_when_has_task_in_queue': self.last_timestamp_when_has_task_in_queue,
            'total_consume_count_from_start': self.total_consume_count_from_start,
            'total_consume_count_from_start_fail': self.total_consume_count_from_start_fail,
            'total_cost_time_from_start': self.total_cost_time_from_start,
            'last_x_s_total_cost_time': self.last_x_s_total_cost_time,
            'avarage_function_spend_time_from_start': round(self.total_cost_time_from_start / self.total_consume_count_from_start, 3) if self.total_consume_count_from_start else None,
        }


class DistributedConsumerStatistics(RedisMixin, FunboostFileLoggerMixin):
    """
    To be compatible with middlewares that simulate MQ (e.g. Redis, which does not implement the AMQP protocol and whose list structure is far from a true MQ), this gets the number of active connected consumers for a queue.
    Consumer statistics in a distributed environment. Three main purposes:

    1. Count active consumers for distributed rate limiting.
       After getting the distributed consumer count, it is used for distributed QPS rate control. Without getting the count of all consumers in the environment, rate limiting is only applicable to the current process.
       Even with a single machine, for example starting xx.py 3 times with the consumer QPS set to 10, without distributed rate limiting, the function would be executed 30 times per second instead of 10.

    2. Record all active consumer IDs in the distributed environment. If a consumer ID is not in this set, it indicates the consumer has disconnected or been closed, and messages can be redistributed. Used for middlewares that do not natively support server-side consumption confirmation.

    3. Get stop and pause states from Redis to support sending commands from other places to stop or pause consumption.
    """
    SHOW_CONSUMER_NUM_INTERVAL = 600
    HEARBEAT_EXPIRE_SECOND = 25
    SEND_HEARTBEAT_INTERVAL = 10

    if HEARBEAT_EXPIRE_SECOND < SEND_HEARTBEAT_INTERVAL * 2:
        raise ValueError(f'HEARBEAT_EXPIRE_SECOND:{HEARBEAT_EXPIRE_SECOND} , SEND_HEARTBEAT_INTERVAL:{SEND_HEARTBEAT_INTERVAL} ')

    def __init__(self, consumer: AbstractConsumer):
        # self._consumer_identification = consumer_identification
        # self._consumer_identification_map = consumer_identification_map
        # self._queue_name = queue_name
        self._consumer_identification = consumer.consumer_identification
        self._consumer_identification_map = consumer.consumer_identification_map
        self._queue_name = consumer.queue_name
        self._consumer = consumer
        self.active_consumer_num = 1
        self._redis_key_name = RedisKeys.gen_redis_hearbeat_set_key_by_queue_name(self._queue_name)  
        self._last_show_consumer_num_timestamp = 0

        self._queue__consumer_identification_map_key_name = RedisKeys.gen_funboost_hearbeat_queue__dict_key_by_queue_name(self._queue_name)
        self._server__consumer_identification_map_key_name = RedisKeys.gen_funboost_hearbeat_server__dict_key_by_ip(nb_log_config_default.computer_ip)

    def run(self):
        self.send_heartbeat()
        self._consumer.keep_circulating(self.SEND_HEARTBEAT_INTERVAL, block=False, daemon=False)(self.send_heartbeat)()

    def _send_heartbeat_with_dict_value(self, redis_key, ):
        # Sends the heartbeat of the current consumer process, with the value as a dictionary, grouped by which processes are running on a machine or for a queue.

        results = self.redis_db_frame.smembers(redis_key)
        with self.redis_db_frame.pipeline() as p:
            for result in results:
                result_dict = Serialization.to_dict(result)
                if self.timestamp() - result_dict['hearbeat_timestamp'] > self.HEARBEAT_EXPIRE_SECOND \
                        or self._consumer_identification_map['consumer_uuid'] == result_dict['consumer_uuid']:
                    # Since this runs every 10 seconds, if not updated within 15 seconds, it has definitely gone offline. If the consumer itself is its own, delete it first.
                    p.srem(redis_key, result)
            self._consumer_identification_map['hearbeat_datetime_str'] = time_util.DatetimeConverter().datetime_str
            self._consumer_identification_map['hearbeat_timestamp'] = self.timestamp()
            self._consumer_identification_map.update(self._consumer.metric_calculation.get_report_hearbeat_info())
            value = Serialization.to_json_str(self._consumer_identification_map, )
            p.sadd(redis_key, value)
            p.execute()

    def _send_msg_num(self):
        dic = {'msg_num_in_broker': self._consumer.metric_calculation.msg_num_in_broker,
               'last_get_msg_num_ts': self._consumer.metric_calculation.last_get_msg_num_ts,
               'report_ts': time.time(),
               }
        self.redis_db_frame.hset(RedisKeys.QUEUE__MSG_COUNT_MAP, self._consumer.queue_name, json.dumps(dic))

    def send_heartbeat(self):
        # Heartbeat keyed by queue name, value is a string for use as Redis key names

        results = self.redis_db_frame.smembers(self._redis_key_name)
        with self.redis_db_frame.pipeline() as p:
            for result in results:
                if self.timestamp() - float(result.split('&&')[-1]) > self.HEARBEAT_EXPIRE_SECOND or \
                        self._consumer_identification == result.split('&&')[0]:  # Since this runs every 10 seconds, if not updated within 15 seconds, it has definitely gone offline. If the consumer itself is its own entry, delete it first.
                    p.srem(self._redis_key_name, result)
            p.sadd(self._redis_key_name, f'{self._consumer_identification}&&{self.timestamp()}')
            p.execute()

        self._send_heartbeat_with_dict_value(self._queue__consumer_identification_map_key_name)
        self._send_heartbeat_with_dict_value(self._server__consumer_identification_map_key_name)
        self._show_active_consumer_num()
        self._get_stop_and_pause_flag_from_redis()
        self._send_msg_num()

    def _show_active_consumer_num(self):
        self.active_consumer_num = self.redis_db_frame.scard(self._redis_key_name) or 1
        if time.time() - self._last_show_consumer_num_timestamp > self.SHOW_CONSUMER_NUM_INTERVAL:
            self.logger.info(f'Total of {self.active_consumer_num} consumers using queue {self._queue_name} across all distributed environments')
            self._last_show_consumer_num_timestamp = time.time()

    def get_queue_heartbeat_ids(self, without_time: bool):
        if without_time:
            return [idx.split('&&')[0] for idx in self.redis_db_frame.smembers(self._redis_key_name)]
        else:
            return [idx for idx in self.redis_db_frame.smembers(self._redis_key_name)]

    # noinspection PyProtectedMember
    def _get_stop_and_pause_flag_from_redis(self):
        stop_flag = self.redis_db_frame.hget(RedisKeys.REDIS_KEY_STOP_FLAG, self._consumer.queue_name)
        if stop_flag is not None and int(stop_flag) == 1:
            self._consumer._stop_flag = 1
        else:
            self._consumer._stop_flag = 0

        pause_flag = self.redis_db_frame.hget(RedisKeys.REDIS_KEY_PAUSE_FLAG, self._consumer.queue_name)
        if pause_flag is not None and int(pause_flag) == 1:
            self._consumer._pause_flag.set()
        else:
            self._consumer._pause_flag.clear()
