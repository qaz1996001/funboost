# # noinspection PyUnresolvedReferences
# import types
#
# # noinspection PyUnresolvedReferences
# from funboost.utils.dependency_packages_in_pythonpath import add_to_pythonpath
#
# import typing
# # noinspection PyUnresolvedReferences
# from functools import update_wrapper, wraps, partial
# import copy
# # noinspection PyUnresolvedReferences
# import nb_log
# from funboost.funboost_config_deafult import BoostDecoratorDefaultParams
# from funboost.helpers import (multi_process_pub_params_list,
#                               run_consumer_with_multi_process, )
# from funboost.core.global_boosters import GlobalBoosters
# from funboost.core.fabric_deploy_helper import fabric_deploy
#
# from funboost.consumers.base_consumer import (AbstractConsumer, FunctionResultStatusPersistanceConfig)
# from funboost.publishers.base_publisher import (AbstractPublisher)
# from funboost.factories.consumer_factory import get_consumer
#
# # noinspection PyUnresolvedReferences
# from funboost.utils import nb_print, patch_print, LogManager, get_logger, LoggerMixin
#
#
# # Some packages don't add handlers by default, making raw logs ugly and non-clickable with no source info. Here we add handlers by default for WARNING level and above.
# # nb_log.get_logger(name='', log_level_int=30, _log_filename='pywarning.log')
#
#
# class Booster(LoggerMixin):
#     """
#     A class written to enable PyCharm auto-completion for decorated consuming functions.
#     """
#
#     def __init__(self, consuming_func_decorated: callable):
#         """
#         :param consuming_func_decorated:   Pass in the function decorated by boost
#
#         This framework places great emphasis on auto-completion of public function/method/class names and parameters in IDE environments. Without this goal, the framework could have much less repetition.
#         This class exists to prevent users from mistyping or not knowing what parameters are available.
#
#         This is a completion helper class that enables PyCharm auto-completion for method names and parameters. It's optional — using it will enable auto-completion in PyCharm.
#
#
#        from funboost import boost, IdeAutoCompleteHelper
#
#        @boost('queue_test_f01', qps=2, broker_kind=3)
#        def f(a, b):
#            print(f'{a} + {b} = {a + b}')
#
#
#        if __name__ == '__main__':
#            f(1000, 2000)
#            IdeAutoCompleteHelper(f).clear()  # f.clear()
#            for i in range(100, 200):
#                f.pub(dict(a=i, b=i * 2))  # f.sub method is forcibly added to f via metaprogramming at runtime; PyCharm can only auto-complete static (non-runtime) things.
#                IdeAutoCompleteHelper(f).pub({'a': i * 3, 'b': i * 4})  # Equivalent to the publish above, but with auto-completion for method names and parameters.
#                f.push(a=i, b=i * 2)
#                IdeAutoCompleteHelper(f).delay(i * 3,  i * 4)
#
#            IdeAutoCompleteHelper(f).start_consuming_message()  # Equivalent to f.consume()
#
#         """
#         wraps(consuming_func_decorated)(self)
#         self.init_params: dict = consuming_func_decorated.init_params
#         self.is_decorated_as_consume_function = consuming_func_decorated.is_decorated_as_consume_function
#         self.consuming_func_decorated = consuming_func_decorated
#
#         self.queue_name = consuming_func_decorated.queue_name
#
#         self.consumer = consuming_func_decorated.consumer  # type: AbstractConsumer
#
#         self.publisher = consuming_func_decorated.publisher  # type: AbstractPublisher
#         self.publish = self.pub = self.apply_async = self.publisher.publish  # type: AbstractPublisher.publish
#         self.push = self.delay = self.publisher.push  # type: AbstractPublisher.push
#         self.clear = self.clear_queue = self.publisher.clear  # type: AbstractPublisher.clear
#         self.get_message_count = self.publisher.get_message_count
#
#         self.start_consuming_message = self.consume = self.start = self.consumer.start_consuming_message
#
#         self.clear_filter_tasks = self.consumer.clear_filter_tasks
#
#         self.wait_for_possible_has_finish_all_tasks = self.consumer.wait_for_possible_has_finish_all_tasks
#
#         # self.pause = self.pause_consume = self.consumer.pause_consume
#         self.continue_consume = self.consumer.continue_consume
#
#         for k, v in consuming_func_decorated.__dict__.items():
#             ''' The above manual assignments are for code completion convenience; this loop automatically supplements all remaining attributes '''
#             if not k.startswith('_'):
#                 setattr(self, k, v)
#
#     def multi_process_consume(self, process_num=1):
#         """Ultra-high-speed multi-process consuming"""
#         run_consumer_with_multi_process(self.consuming_func_decorated, process_num)
#
#     multi_process_start = multi_process_consume
#
#     def multi_process_pub_params_list(self, params_list, process_num=16):
#         """Ultra-high-speed multi-process publishing, e.g., quickly publish 10 million tasks to the broker, then consume them later"""
#         """
#         Usage example: quickly publish 10 million tasks using 20 processes, fully utilizing multi-core CPUs.
#         @boost('test_queue66c', qps=1/30,broker_kind=BrokerEnum.KAFKA_CONFLUENT)
#         def f(x, y):
#             print(f'Function execution start time {time.strftime("%H:%M:%S")}')
#         if __name__ == '__main__':
#             f.multi_process_pub_params_list([{'x':i,'y':i*3}  for i in range(10000000)],process_num=20)
#             f.consume()
#         """
#         multi_process_pub_params_list(self.consuming_func_decorated, params_list=params_list, process_num=process_num)
#
#     # noinspection PyDefaultArgument
#     def fabric_deploy(self, host, port, user, password,
#                       path_pattern_exluded_tuple=('/.git/', '/.idea/', '/dist/', '/build/'),
#                       file_suffix_tuple_exluded=('.pyc', '.log', '.gz'),
#                       only_upload_within_the_last_modify_time=3650 * 24 * 60 * 60,
#                       file_volume_limit=1000 * 1000, sftp_log_level=20, extra_shell_str='',
#                       invoke_runner_kwargs={'hide': None, 'pty': True, 'warn': False},
#                       python_interpreter='python3',
#                       process_num=1):
#         """
#         See fabric_deploy function for parameter details. Parameters are repeated here for PyCharm auto-completion.
#         """
#         in_kwargs = locals()
#         in_kwargs.pop('self')
#         fabric_deploy(self.consuming_func_decorated, **in_kwargs)
#
#     def __call__(self, *args, **kwargs):
#         return self.consuming_func_decorated(*args, **kwargs)
#
#     def __get__(self, instance, cls):
#         """ https://python3-cookbook.readthedocs.io/zh_CN/latest/c09/p09_define_decorators_as_classes.html """
#         if instance is None:
#             return self
#         else:
#             return types.MethodType(self, instance)
#
#
# IdeAutoCompleteHelper = Booster  # Backward compatibility alias
#
#
# class _Undefined:
#     pass
#
#
# def boost(queue_name,
#           *,
#           consuming_function_decorator: typing.Callable = _Undefined,
#           function_timeout: float = _Undefined,
#           concurrent_num: int = _Undefined,
#           specify_concurrent_pool=_Undefined,
#           specify_async_loop=_Undefined,
#           concurrent_mode: int = _Undefined,
#           max_retry_times: int = _Undefined,
#           is_push_to_dlx_queue_when_retry_max_times: bool = _Undefined,
#           log_level: int = _Undefined,
#           is_print_detail_exception: bool = _Undefined,
#           is_show_message_get_from_broker: bool = _Undefined,
#           qps: float = _Undefined,
#           is_using_distributed_frequency_control: bool = _Undefined,
#           msg_expire_seconds: float = _Undefined,
#           is_send_consumer_heartbeat_to_redis: bool = _Undefined,
#           logger_prefix: str = _Undefined,
#           create_logger_file: bool = _Undefined,
#           do_task_filtering: bool = _Undefined,
#           task_filtering_expire_seconds: float = _Undefined,
#           is_do_not_run_by_specify_time_effect: bool = _Undefined,
#           do_not_run_by_specify_time: bool = _Undefined,
#           schedule_tasks_on_main_thread: bool = _Undefined,
#           function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = _Undefined,
#           user_custom_record_process_info_func: typing.Union[typing.Callable, None] = _Undefined,
#           is_using_rpc_mode: bool = _Undefined,
#           broker_exclusive_config: dict = _Undefined,
#           broker_kind: int = _Undefined,
#           boost_decorator_default_params=BoostDecoratorDefaultParams()
#           ):
#     """
#     The values of funboost.funboost_config_deafult.BoostDecoratorDefaultParams will be automatically overridden by the values in funboost_config.BoostDecoratorDefaultParams in your project root directory.
#     If the boost decorator does not pass parameters, it defaults to using the configuration in funboost_config.BoostDecoratorDefaultParams.
#
#     For parameters, also see the documentation at https://funboost.readthedocs.io/zh-cn/latest/articles/c3.html section 3.3.
#
#     # For better code hints, the parameter meanings are repeated here. The function f decorated by this decorator automatically gets some methods added, e.g., f.push, f.consume, etc.
#     :param queue_name: Queue name.
#     :param consuming_function_decorator: Function decorator. Since this framework performs automatic parameter conversion and needs precise parameter names, it does not support stacking @decorators with *args/**kwargs on consuming functions. If you want to use a decorator, specify it here.
#     :param function_timeout: Timeout in seconds. If the function runs longer than this, it will be automatically killed. Set to 0 for no limit. Setting this will degrade code performance; do not set it unless necessary.
#     # If qps is set and concurrent_num is the default 50, it will automatically open 500 concurrent workers. Since the smart thread pool doesn't actually create that many threads when tasks are few and automatically shrinks, see ThreadPoolExecutorShrinkAble docs.
#     # Thanks to the useful qps frequency control and smart auto-scaling thread pool, this framework recommends ignoring concurrent_num and just setting qps. The framework's concurrency is adaptive, which is very powerful and convenient.
#     :param concurrent_num: Number of concurrent workers.
#     :param specify_concurrent_pool: Use a specified thread pool (or coroutine pool). Multiple consumers can share one pool. When not None, threads_num is ignored.
#     :param specify_async_loop: Specify an async event loop. Only takes effect when concurrent mode is set to async.
#     :param concurrent_mode: Concurrency mode. 1=threading (ConcurrentModeEnum.THREADING), 2=gevent (ConcurrentModeEnum.GEVENT),
#                               3=eventlet (ConcurrentModeEnum.EVENTLET), 4=asyncio (ConcurrentModeEnum.ASYNC), 5=single thread (ConcurrentModeEnum.SINGLE_THREAD)
#     :param max_retry_times: Maximum auto-retry count. When a function errors, it immediately retries n times automatically, useful for certain unstable situations.
#            You can actively raise ExceptionForRetry in the function, and the framework will immediately retry.
#            Raising ExceptionForRequeue will return the current message to the broker.
#            Raising ExceptionForPushToDlxqueue will send the message to a separate dead letter queue named queue_name + _dlx.
#     :param is_push_to_dlx_queue_when_retry_max_times: Whether to send to dead letter queue when max retries are reached without success. Dead letter queue name is queue_name + _dlx.
#     :param log_level: Framework log level. logging.DEBUG(10) logging.INFO(20) logging.WARNING(30) logging.ERROR(40) logging.CRITICAL(50)
#     :param is_print_detail_exception: Whether to print detailed stack traces. Set to 0 for brief errors that take fewer console lines.
#     :param is_show_message_get_from_broker: Whether to print messages when they are fetched from the broker.
#     :param qps: Specifies function executions per second. Can be a decimal like 0.01 (once per 100 seconds) or 50 (50 times per second). Set to 0 for no rate limiting.
#     :param msg_expire_seconds: Message expiration time. 0 means never expire. 10 means tasks published more than 10 seconds ago will be discarded if not yet consumed.
#     :param is_using_distributed_frequency_control: Whether to use distributed rate limiting (relies on Redis to count consumers and split the rate evenly). By default, rate limiting only applies to the current consumer instance.
#             If 2 consumers with qps=10 share the same queue and both start, the total rate will reach 20/s. With distributed rate limiting, all consumers combined will run at 10/s total.
#     :param is_send_consumer_heartbeat_to_redis: Whether to send consumer heartbeat to Redis. Some features need to count active consumers, since some brokers are not true MQs.
#     :param logger_prefix: Log prefix, allowing different consumers to generate different log prefixes.
#     :param create_logger_file: Whether to create a file logger.
#     :param do_task_filtering: Whether to perform task filtering based on function parameters.
#     :param task_filtering_expire_seconds: Task filtering expiration time. 0 means permanent filtering. E.g., if set to 1800 seconds,
#            a task 1+2 published 30 minutes ago will still execute,
#            but if published within the last 30 minutes, 1+2 won't execute again. This logic is integrated into the framework, commonly used for API response caching.
#     :param is_do_not_run_by_specify_time_effect: Whether to enable the do-not-run time period.
#     :param do_not_run_by_specify_time: Time period during which tasks should not run.
#     :param schedule_tasks_on_main_thread: Schedule tasks directly on the main thread. This means you cannot start two consumers on the same main thread. fun.consume() will block, and code after it won't run.
#     :param function_result_status_persistance_conf: Configuration for whether to save function parameters, results, and status to MongoDB.
#            This is used for parameter tracing, task statistics, and web display. Requires MongoDB installation.
#     :param user_custom_record_process_info_func: Provide a user-defined function to save message processing records to a destination like MySQL. The function accepts a single parameter of type FunctionResultStatus.
#     :param is_using_rpc_mode: Whether to use RPC mode, allowing the publisher to get result callbacks from the consumer. This has some performance cost. Using async_result.result will block the current thread.
#     :param broker_exclusive_config: Broker-specific non-universal configuration. Different brokers have their own unique settings not compatible across all brokers. Since the framework supports 30+ message queues — which are not just simple FIFO queues —
#             e.g., Kafka supports consumer groups, RabbitMQ supports various unique concepts like ACK mechanisms and complex routing. Each message queue has unique configuration parameters that can be passed here.
#     :param broker_kind: Broker type, supports 30+ message queues. See BrokerEnum class attributes.
#     :param boost_decorator_default_params: BoostDecoratorDefaultParams provides
#             the default global parameters for the @boost decorator. If boost doesn't explicitly specify a parameter, it automatically uses the configuration from funboost_config.py's BoostDecoratorDefaultParams.
#                     If you find too much repetition in boost decorator parameters, you can set global defaults in funboost_config.py.
#             BoostDecoratorDefaultParams() can also accept any boost decorator parameters during instantiation. BoostDecoratorDefaultParams is a dataclass (similar to Python 3.7 dataclass concept).
#
#             The values of funboost.funboost_config_deafult.BoostDecoratorDefaultParams will be automatically overridden by funboost_config.BoostDecoratorDefaultParams in your project root directory.
#
#     """
#
#     """
#     This is the most important function in the framework. You must understand all its parameters.
#     For the meaning of parameters, see the parameter comments of get_consumer.
#
#     Originally defined as: def boost(queue_name, **consumer_init_kwargs):
#     Parameters are fully written out for better IDE auto-completion.
#
#     Decorator-based task registration. If you prefer the decorator style (like Celery's decorator-based task registration), you can use this decorator.
#     If your function is named f, you can call f.publish or f.pub to publish tasks, and f.start_consuming_message or f.consume or f.start to consume tasks.
#     When necessary, call f.publisher.funcxx and f.consumer.funcyy.
#
#
#     Decorator version usage example:
#     '''
#     @boost('queue_test_f01', qps=0.2, broker_kind=2)
#     def f(a, b):
#         print(a + b)
#
#     for i in range(10, 20):
#         f.pub(dict(a=i, b=i * 2))
#         f.push(i, i * 2)
#     f.consume()
#     # f.multi_process_conusme(8)             # # This is a newly added method — fine-grained thread/coroutine concurrency stacked with 8 processes for blazing speed. No need to import run_consumer_with_multi_process.
#     # run_consumer_with_multi_process(f,8)   # # This provides fine-grained thread/coroutine concurrency stacked with 8 processes for blazing speed.
#     '''
#
#     Standard (non-decorator) usage:
#     '''
#     def f(a, b):
#         print(a + b)
#
#     consumer = get_consumer('queue_test_f01', consuming_function=f,qps=0.2, broker_kind=2)
#     # You need to manually specify the consuming_function parameter.
#     for i in range(10, 20):
#         consumer.publisher_of_same_queue.publish(dict(a=i, b=i * 2))
#     consumer.start_consuming_message()
#
#     '''
#
#     The decorator version of boost has 99% the same parameters as get_consumer. The only difference is that the decorator version is placed on the function, so it automatically knows the consuming function
#     and doesn't need the consuming_function parameter.
#     """
#     # The decorator version automatically knows the consuming function, preventing duplicate passing of the consuming_function parameter like in get_consumer.
#     consumer_init_params_include_boost_decorator_default_params = copy.copy(locals())
#     consumer_init_params0 = copy.copy(consumer_init_params_include_boost_decorator_default_params)
#     consumer_init_params0.pop('boost_decorator_default_params')
#     consumer_init_params = copy.copy(consumer_init_params0)
#     for k, v in consumer_init_params0.items():
#         if v == _Undefined:
#             # print(k,v,boost_decorator_default_params[k])
#             consumer_init_params[k] = boost_decorator_default_params[k]  # If the boost decorator didn't explicitly specify a parameter, use the global config from funboost_config.py's BoostDecoratorDefaultParams.
#
#     # print(consumer_init_params)
#     def _deco(func) -> Booster:  # Adding this -> enables PyCharm dynamic auto-completion
#
#         func.init_params = consumer_init_params
#         consumer = get_consumer(consuming_function=func, **consumer_init_params)  # type: AbstractConsumer
#         func.is_decorated_as_consume_function = True
#         func.consumer = consumer
#         func.queue_name = queue_name
#
#         func.publisher = consumer.publisher_of_same_queue
#         func.publish = func.pub = func.apply_async = consumer.publisher_of_same_queue.publish
#         func.push = func.delay = consumer.publisher_of_same_queue.push
#         func.multi_process_pub_params_list = partial(multi_process_pub_params_list, func)
#         func.clear = func.clear_queue = consumer.publisher_of_same_queue.clear
#         func.get_message_count = consumer.publisher_of_same_queue.get_message_count
#
#         func.start_consuming_message = func.consume = func.start = consumer.start_consuming_message
#         func.multi_process_start = func.multi_process_consume = partial(run_consumer_with_multi_process, func)
#
#         func.fabric_deploy = partial(fabric_deploy, func)
#
#         func.clear_filter_tasks = consumer.clear_filter_tasks
#
#         func.wait_for_possible_has_finish_all_tasks = consumer.wait_for_possible_has_finish_all_tasks
#
#         func.pause = func.pause_consume = consumer.pause_consume
#         func.continue_consume = consumer.continue_consume
#
#         GlobalBoosters.regist(queue_name,func)
#
#         # @wraps(func)
#         # def __deco(*args, **kwargs):  # This changes the function's id, making it inconvenient to start multiprocessing inside the decorator on Windows.
#         #     return func(*args, **kwargs)
#         return func
#
#         # return __deco  # noqa # 两种方式都可以
#         # return update_wrapper(__deco, func)
#
#     return _deco  # noqa
#
#
# task_deco = boost  # Both decorator names work. task_deco is the original name, kept for backward compatibility.
