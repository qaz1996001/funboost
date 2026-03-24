# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 11:57
from pathlib import Path

import abc
import copy
import inspect
import atexit
import json
import logging
import multiprocessing
import sys
import threading
import time
import typing
from functools import wraps
from threading import Lock

import nb_log
from funboost.concurrent_pool.async_helper import simple_run_in_executor
from funboost.constant import BrokerEnum, ConstStrForClassMethod, FunctionKind
from funboost.core.broker_kind__exclusive_config_default_define import generate_broker_exclusive_config
from funboost.core.func_params_model import PublisherParams, TaskOptions
from funboost.core.function_result_status_saver import FunctionResultStatus
from funboost.core.helper_funs import MsgGenerater, get_func_only_params
from funboost.core.loggers import develop_logger

# from nb_log import LoggerLevelSetterMixin, LoggerMixin
from funboost.core.loggers import LoggerLevelSetterMixin, FunboostFileLoggerMixin, get_logger
from funboost.core.msg_result_getter import AsyncResult, AioAsyncResult
from funboost.core.serialization import PickleHelper, Serialization
from funboost.core.task_id_logger import TaskIdLogger
from funboost.utils import decorators
from funboost.funboost_config_deafult import BrokerConnConfig, FunboostCommonConfig
from nb_libs.path_helper import PathHelper
from funboost.core.consuming_func_iniput_params_check import ConsumingFuncInputParamsChecker

RedisAsyncResult = AsyncResult  # alias
RedisAioAsyncResult = AioAsyncResult  # alias


class AbstractPublisher(metaclass=abc.ABCMeta, ):
    """
    Publish messages to a message queue.
    For synchronous programming, the most important methods are push and publish.
    For asyncio asynchronous programming, the most important methods are aio_push and aio_publish.

    Usage: booster.push(1, y=2)
    Or: booster.publish({"x":1,"y":2}, task_options=TaskOptions(max_retry_times=3,...))
    In summary, push is simpler and more magical, while publish is more powerful and flexible,
    because publish can pass task_options parameters in addition to the function input parameters.
    """
    def __init__(self, publisher_params: PublisherParams, ):
        self.publisher_params = publisher_params
        
        self.queue_name = self._queue_name = publisher_params.queue_name
        self.logger: logging.Logger
        self._build_logger()
        
        self.publisher_params.broker_exclusive_config = generate_broker_exclusive_config(self.publisher_params.broker_kind,self.publisher_params.broker_exclusive_config,self.logger)
        self.has_init_broker = 0
        self._lock_for_count = Lock()
        self._current_time = None
        self.count_per_minute = None
        self._init_count()
        self.custom_init()
        self.logger.info(f'{self.__class__} has been instantiated')
        self.publish_msg_num_total = 0
        
        ConsumingFuncInputParamsChecker.gen_final_func_input_params_info(publisher_params)
        self.publish_params_checker = ConsumingFuncInputParamsChecker(self.final_func_input_params_info) if publisher_params.consuming_function else None

        self.__init_time = time.time()
        atexit.register(self._at_exit)
        if publisher_params.clear_queue_within_init:
            self.clear()
        
        # 
        self._is_memory_queue = self.publisher_params.broker_kind in [BrokerEnum.MEMORY_QUEUE, BrokerEnum.FASTEST_MEM_QUEUE]
        
        # Optimization: memory queues don't need decorators (no network exceptions), direct call is faster
        if self._is_memory_queue:
            self._wrapped_publish_impl = self._publish_impl
        else:
            # Optimization: cache the wrapped _publish_impl method to avoid reapplying decorators on every publish
            self._wrapped_publish_impl = decorators.handle_exception(
                retry_times=10, is_throw_error=True, time_sleep=0.1
            )(self._publish_impl)
    
    @property
    def final_func_input_params_info(self):
        """
        {...
         "auto_generate_info": {
    "where_to_instantiate": "D:\\codes\\funboost\\examples\\example_faas\\task_funs_dir\\sub.py:5",
    "final_func_input_params_info": {
      "func_name": "sub",
      "func_position": "<function sub at 0x00000272649BBA60>",
      "is_manual_func_input_params": false,
      "all_arg_name_list": [
        "a",
        "b"
      ],
      "must_arg_name_list": [
        "a",
        "b"
      ],
      "optional_arg_name_list": []
    }
  }}
        """
        return self.publisher_params.auto_generate_info['final_func_input_params_info']

    def _build_logger(self):
        logger_prefix = self.publisher_params.logger_prefix
        if logger_prefix != '':
            logger_prefix += '--'
        self.logger_name = self.publisher_params.logger_name or f'funboost.{logger_prefix}{self.__class__.__name__}--{self.queue_name}'
        self.log_filename = self.publisher_params.log_filename or f'funboost.{self.queue_name}.log'
        self.logger = nb_log.LogManager(self.logger_name, logger_cls=TaskIdLogger).get_logger_and_add_handlers(
            log_level_int=self.publisher_params.log_level,
            log_filename=self.log_filename if self.publisher_params.create_logger_file else None,
            error_log_filename=nb_log.generate_error_file_name(self.log_filename),
            formatter_template=FunboostCommonConfig.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER, )

    def _init_count(self):
        self._current_time = time.time()
        self.count_per_minute = 0

    def custom_init(self):
        pass

    

    @staticmethod
    def _get_from_other_extra_params(k: str, msg):
        # msg_dict = json.loads(msg) if isinstance(msg, str) else msg
        msg_dict = Serialization.to_dict(msg)
        return msg_dict['extra'].get('other_extra_params', {}).get(k, None)

    def _convert_msg(self, msg: typing.Union[str, dict], task_id=None,
                     task_options: TaskOptions = None) -> (typing.Dict, typing.Dict, typing.Dict, str):
        """
        Optimization: reduce unnecessary deep copies, use dict comprehension to create msg_function_kw
        """
        msg = Serialization.to_dict(msg)
        # Use dict comprehension instead of deepcopy, excluding the extra key
        raw_extra = msg.get('extra', {})
        msg_function_kw = get_func_only_params(msg)
        self.check_func_msg_dict(msg_function_kw)

        if task_options:
            task_options_dict = Serialization.to_dict(task_options.to_json(exclude_unset=True))
        else:
            task_options_dict = {}
        task_id = task_id or task_options_dict.get('task_id') or raw_extra.get('task_id') or MsgGenerater.generate_task_id(self._queue_name)
        task_options_dict['task_id'] = task_id
        task_options_dict['publish_time'] = task_options_dict.get('publish_time') or raw_extra.get('publish_time') or MsgGenerater.generate_publish_time()
        task_options_dict['publish_time_format'] = task_options_dict.get('publish_time_format') or raw_extra.get('publish_time_format') or MsgGenerater.generate_publish_time_format()
    
        new_extra = {}
        new_extra.update(raw_extra)
        new_extra.update(task_options_dict) # task_options.json is to fully utilize pydantic's custom time formatting strings
        msg['extra'] = new_extra
        extra_params = new_extra
        return msg, msg_function_kw, extra_params, task_id

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                task_options: TaskOptions = None):
        """

        :param msg: Function input parameter dict or dict-to-json. E.g., if the consuming function is def add(x,y), you publish {"x":1,"y":2}
        :param task_id: Can specify a task_id, or leave it unspecified to auto-generate a uuid
        :param task_options: Priority configuration; messages can carry priority config to override boost settings.
        :return: AsyncResult object that can be used to wait for results. E.g., status_and_result = async_result.status_and_result to wait for the return result.

        The extra dict in the funboost message body contains keys declared in TaskOptions fields, such as task_id, publish_time, publish_time_format, etc.
        If the user passes task_options, task_options takes precedence.
        If the user does not pass task_options, the extra dict in the message body is used.
        If task_id, publish_time, publish_time_format, etc. are still missing, they are auto-generated.

        This means if you want to pass values from task_options, your msg dict can either:
        Option 1: Have an extra field containing various task_options fields (suitable for cross-language scenarios)
        Option 2: Specify a TaskOptions pydantic model object via the publish method's task_options parameter (suitable for Python, since funboost can be used directly)

        For cross-business, cross-language scenarios where Java cannot call Python funboost's publish method:
        Java can publish messages via HTTP interface or funboost.faas like this: {"user_id":123,"name":"John","extra": {"task_id":"1234567890","max_retry_times":3}}

        """
        # Optimization: use shallow copy instead of deep copy, _convert_msg no longer copies internally
        # For nested extra dicts, a new dict is created when modification is needed
        if isinstance(msg, str):
            msg = Serialization.to_dict(msg)
        else:
            msg = dict(msg)  # shallow copy, don't modify the user's original dict
        msg, msg_function_kw, extra_params, task_id = self._convert_msg(msg, task_id, task_options)
        t_start = time.time()

        if self._is_memory_queue: # memory queue doesn't need serialization
            msg_json =msg
        else:
            try:
                msg_json = Serialization.to_json_str(msg)
            except Exception as e:
                can_not_json_serializable_keys = Serialization.find_can_not_json_serializable_keys(msg)
                self.logger.warning(f'msg contains keys that cannot be serialized: {can_not_json_serializable_keys}')
                # raise ValueError(f'msg contains keys that cannot be serialized: {can_not_json_serializable_keys}')
                new_msg = copy.deepcopy(Serialization.to_dict(msg))
                for key in can_not_json_serializable_keys:
                    new_msg[key] = PickleHelper.to_str(new_msg[key])
                new_msg['extra']['can_not_json_serializable_keys'] = can_not_json_serializable_keys
                msg_json = Serialization.to_json_str(new_msg)
        # print(msg_json)
        # Optimization: use cached wrapped method to avoid reapplying decorators each time
        self._wrapped_publish_impl(msg_json)

        # Optimization: get current time first for subsequent checks, reduce time.time() calls
        current_time = time.time()
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f'Pushed message to queue {self._queue_name}, took {round(current_time - t_start, 4)} seconds  {msg_json if self.publisher_params.publish_msg_log_use_full_msg else msg_function_kw}',
                              extra={'task_id': task_id})
        
        # Optimization: reduce in-lock operations, count first then check if logging is needed
        self.count_per_minute += 1
        self.publish_msg_num_total += 1
        # Output statistics log every 10 seconds, reduce lock contention
        if current_time - self._current_time > 10:
            with self._lock_for_count:
                # Double-check to avoid duplicate output in multi-threading
                if current_time - self._current_time > 10:
                    self.logger.info(
                        f'Pushed {self.count_per_minute} messages in 10 seconds, total {self.publish_msg_num_total} messages pushed to queue {self._queue_name}')
                    self._init_count()
        self._after_publish(msg, msg_function_kw, task_id)
        # AsyncResult itself is lazy-loaded, redis connection is only established when accessing result and other attributes
        return AsyncResult(task_id, timeout=self.publisher_params.rpc_timeout)
    
    def _after_publish(self, msg: dict, msg_function_kw: dict, task_id: str):
        """Hook method after publishing a message. Subclasses can override this to implement custom logic, e.g., recording metrics."""
        pass

    def send_msg(self, msg: typing.Union[dict, str]):
        """Directly send any raw message content to the message queue, without generating auxiliary parameters, ignoring function parameter names, without validating parameter count or key names."""
        # Optimization: use cached wrapped method
        self._wrapped_publish_impl(Serialization.to_json_str(msg))

    @staticmethod
    def __get_cls_file(cls: type):
        if cls.__module__ == '__main__':
            cls_file = Path(sys.argv[0]).resolve().as_posix()
        else:
            cls_file = Path(sys.modules[cls.__module__].__file__).resolve().as_posix()
        return cls_file

    def push(self, *func_args, **func_kwargs):
        """
        Shorthand that only supports passing the consuming function's own parameters, without task_options.
        The relationship between publish and push is similar to apply_async and delay. The former is more powerful, the latter is simpler.

        For example, if the consuming function is:
        def add(x, y):
            print(x + y)

        publish({"x":1,'y':2}) and push(1,2) are equivalent. But the former can pass task_options. The latter can only pass parameters accepted by the add function.
        :param func_args:
        :param func_kwargs:
        :return:
        """
        # print(func_args, func_kwargs, self.publish_params_checker.all_arg_name)
        msg_dict = func_kwargs
        # print(msg_dict)
        # print(self.publish_params_checker.position_arg_name_list)
        # print(func_args)
        func_args_list = list(func_args)

        # print(func_args_list)
        if self.publisher_params.consuming_function_kind == FunctionKind.CLASS_METHOD:
            # print(self.publish_params_checker.all_arg_name[0])
            # func_args_list.insert(0, {'first_param_name': self.publish_params_checker.all_arg_name[0],
            #        'cls_type': ClsHelper.get_classs_method_cls(self.publisher_params.consuming_function).__name__},
            #                       )
            cls = func_args_list[0]
            # print(cls,cls.__name__, sys.modules[cls.__module__].__file__)
            if not inspect.isclass(cls):
                raise ValueError(f'The consuming_function {self.publisher_params.consuming_function} is class_method,the first params of push must be a class')
            func_args_list[0] = {ConstStrForClassMethod.FIRST_PARAM_NAME: self.publish_params_checker.all_arg_name_list[0],
                                 ConstStrForClassMethod.CLS_NAME: cls.__name__,
                                 ConstStrForClassMethod.CLS_FILE: self.__get_cls_file(cls),
                                 ConstStrForClassMethod.CLS_MODULE: PathHelper(self.__get_cls_file(cls)).get_module_name(),
                                 }
        elif self.publisher_params.consuming_function_kind == FunctionKind.INSTANCE_METHOD:
            obj = func_args[0]

            cls = type(obj)
            if not hasattr(obj, ConstStrForClassMethod.OBJ_INIT_PARAMS):
                raise ValueError(f'''The consuming_function {self.publisher_params.consuming_function} is an instance method, and the instance must have the {ConstStrForClassMethod.OBJ_INIT_PARAMS} attribute.
The first argument of the push method must be the instance of the class.
                ''')
            func_args_list[0] = {ConstStrForClassMethod.FIRST_PARAM_NAME: self.publish_params_checker.all_arg_name_list[0],
                                 ConstStrForClassMethod.CLS_NAME: cls.__name__,
                                 ConstStrForClassMethod.CLS_FILE: self.__get_cls_file(cls),
                                 ConstStrForClassMethod.CLS_MODULE: PathHelper(self.__get_cls_file(cls)).get_module_name(),
                                 ConstStrForClassMethod.OBJ_INIT_PARAMS: getattr(obj, ConstStrForClassMethod.OBJ_INIT_PARAMS),

                                 }

        for index, arg in enumerate(func_args_list):
            # print(index,arg,self.publish_params_checker.position_arg_name_list)
            # msg_dict[self.publish_params_checker.position_arg_name_list[index]] = arg
            msg_dict[self.publish_params_checker.all_arg_name_list[index]] = arg

        # print(msg_dict)
        return self.publish(msg_dict)

    delay = push  # An alias, both can be used.

    @abc.abstractmethod
    def _publish_impl(self, msg: str):
        raise NotImplementedError

    def sync_call(self, msg_dict: dict, is_return_rpc_data_obj=True) -> typing.Union[dict, FunctionResultStatus]:
        """Only some brokers support synchronous call with blocking wait for results, not relying on AsyncResult + redis as RPC, e.g., http, grpc, etc."""
        raise NotImplementedError(f'broker  {self.publisher_params.broker_kind} not support sync_call method')

    @abc.abstractmethod
    def clear(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_message_count(self):
        raise NotImplementedError

    @abc.abstractmethod
    def close(self):
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        self.logger.warning(f'Auto-closed publisher connection in with block, total {self.publish_msg_num_total} messages pushed')

    def _at_exit(self):
        if multiprocessing.current_process().name == 'MainProcess':
            self.logger.warning(
                f'Before program shutdown, pushed {self.publish_msg_num_total} messages to {self._queue_name} in {round(time.time() - self.__init_time)} seconds')

    async def aio_push(self, *func_args, **func_kwargs) -> AioAsyncResult:
        """Publish messages in asyncio ecosystem. Since synchronous push takes less than 1ms, you can generally call the synchronous push method directly in asyncio,
        but to better handle network fluctuations (e.g., publishing to a remote message queue takes up to 10ms), use aio_push."""
        async_result = await simple_run_in_executor(self.push, *func_args, **func_kwargs)
        return AioAsyncResult(async_result.task_id,timeout=async_result.timeout )

    async def aio_publish(self, msg: typing.Union[str, dict], task_id=None,
                          task_options: TaskOptions = None) -> AioAsyncResult:
        """Publish messages in asyncio ecosystem. Since synchronous push takes less than 1ms, you can generally call the synchronous push method directly in asyncio,
        but to better handle network fluctuations (e.g., publishing to a remote message queue takes up to 10ms), use aio_publish."""
        async_result = await simple_run_in_executor(self.publish, msg, task_id, task_options)
        return AioAsyncResult(async_result.task_id, timeout=async_result.timeout)

    def check_func_msg_dict(self, msg_dict: dict):
        if self.publish_params_checker and self.publisher_params.should_check_publish_func_params:
            if not isinstance(msg_dict, dict):
                raise ValueError(f"check_func_msg_dict input must be a dict, current type is: {type(msg_dict)}")
            msg_function_kw = get_func_only_params(msg_dict)
            self.publish_params_checker.check_func_msg_dict(msg_function_kw)
        return True

    def check_func_input_params(self, *args, **kwargs):
        """
        Validate push-style parameters: f.check_params(1, y=2)
        Uses the final_func_input_params_info parsed at framework startup for parameter mapping and validation.
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: Returns True if validation passes, raises exception on failure
        """

        params_dict = dict(zip(self.publish_params_checker.all_arg_name_list, args))
        if kwargs:
            params_dict.update(kwargs)
        # print(4444,args,kwargs, params_dict)
        return self.check_func_msg_dict(params_dict)

        




has_init_broker_lock = threading.Lock()


def deco_mq_conn_error(f):
    @wraps(f)
    def _deco_mq_conn_error(self, *args, **kwargs):
        with has_init_broker_lock:
            if not self.has_init_broker:
                self.logger.warning(f'Method [{f.__name__}] first use, initializing by executing init_broker method')
                self.init_broker()
                self.has_init_broker = 1
                return f(self, *args, **kwargs)
            # noinspection PyBroadException
            try:
                return f(self, *args, **kwargs)
            except Exception as e:
                # Determine by exception class module name and class name, no need to import packages
                exc_module = type(e).__module__
                exc_name = type(e).__name__
                
                # Reconnect for any AMQP/Connection related exceptions from these packages
                is_amqp_error = (
                    ('amqpstorm' in exc_module or 'pika' in exc_module or 'amqp' in exc_module)
                    and ('AMQP' in exc_name or 'Connection' in exc_name or 'Channel' in exc_name)
                )
                
                if is_amqp_error:
                    self.logger.error(f'Broker connection error, method {f.__name__} failed, {e}')
                    self.init_broker()
                    return f(self, *args, **kwargs)
                raise  # Re-raise other exceptions
            except BaseException as e:
                self.logger.critical(e, exc_info=True)

    return _deco_mq_conn_error
