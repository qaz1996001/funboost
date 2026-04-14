"""
Pydantic model definitions. funboost uses pydantic for important function parameters,
making it easy to pass many parameters across multiple layers without the hassle of repeatedly adding them everywhere.
For example, BoosterParams often gains new fields; if funboost used direct parameters, adding a field at every layer would be very cumbersome.

BoosterParams is funboost's most core input model. Mastering BoosterParams means mastering 90% of funboost's usage.

"""

import functools
import typing
import asyncio
import logging
import datetime
from pydantic.fields import Field


from funboost.concurrent_pool.pool_commons import ConcurrentPoolBuilder
from funboost.concurrent_pool.flexible_thread_pool import FlexibleThreadPool
from funboost.core.lazy_impoter import funboost_lazy_impoter
from funboost.core.pydantic_compatible_base import compatible_root_validator
from funboost.core.pydantic_compatible_base import BaseJsonAbleModel
from funboost.constant import BrokerEnum, ConcurrentModeEnum, StrConst


from funboost.concurrent_pool import FunboostBaseConcurrentPool

class FunctionResultStatusPersistanceConfig(BaseJsonAbleModel):
    is_save_status: bool = False # Whether to save the function's runtime status info
    is_save_result: bool = False  # Whether to save the function's runtime result
    expire_seconds: int = 7 * 24 * 3600  # How long to keep function runtime status in MongoDB before auto-expiry
    is_use_bulk_insert: bool = False  # Whether to use bulk insert to save results. Bulk insert saves all function consumption status results from the last 0.5 seconds every 0.5 seconds, so the last 0.5 seconds' results may not be inserted in time. When False, writes to MongoDB in real-time after each function completion.
    table_name:typing.Optional[str] = None # Table name, used to specify the table for saving function runtime status and results. Defaults to the queue name.

    @compatible_root_validator(skip_on_failure=True)
    def check_values(self, ):
        expire_seconds = self.expire_seconds
        if expire_seconds > 10 * 24 * 3600:
            funboost_lazy_impoter.flogger.warning(f'The expire_seconds you set is {expire_seconds} seconds, which is too long.')
        if not self.is_save_status and self.is_save_result:
            raise ValueError(f'You have set is_save_status=False but is_save_result=True. This combination is not allowed.')
        return self


booster_params_has_been_deleted_fields = [
    # Fields removed from functionality
    'retry_interval',
    'is_do_not_run_by_specify_time_effect',
    'do_not_run_by_specify_time',
    # Spelling corrections: old versions had typos; corrected in new versions. Old redis metadata stores the misspelled keys.
    'is_send_consumer_hearbeat_to_redis',  # Correct spelling: is_send_consumer_heartbeat_to_redis
    'consumin_function_decorator',         # Correct spelling: consuming_function_decorator
    'msg_expire_senconds',                 # Correct spelling: msg_expire_seconds
]


class BoosterParamsFieldsAssit:
    # Fields that have been deleted and replaced by other field functionality.
    has_been_deleted_fields = [
        'retry_interval',
        'is_do_not_run_by_specify_time_effect',
        'do_not_run_by_specify_time',
    ]

    # Previously misspelled fields that were later corrected; need to map old keys to new keys.
    rename_fields = {
        # 'old_name':'new_name',
        'is_send_consumer_hearbeat_to_redis': 'is_send_consumer_heartbeat_to_redis',
        'consumin_function_decorator': 'consuming_function_decorator',
        'msg_expire_senconds': 'msg_expire_seconds',
    }

class BoosterParams(BaseJsonAbleModel):
    """
    The key to mastering funboost is knowing the parameters of BoosterParams. Knowing all the input fields means mastering 90% of funboost's usage.

    For pydantic PyCharm code completion, install the pydantic plugin: PyCharm -> File -> Settings -> Plugins -> search 'pydantic' and install.

    The @boost decorator's parameters must be this class or a subclass. If you want to avoid many repetitive params per decorator, write a subclass of BoosterParams and pass that subclass, like BoosterParamsComplete below.
    """


    queue_name: str  # Queue name, required, each function should use a different queue name.
    broker_kind: str = BrokerEnum.SQLITE_QUEUE  # Broker selection, see section 3.1 https://funboost.readthedocs.io/zh-cn/latest/articles/c3.html

    """ project_name is the project name, a management-level label. Defaults to None. Assigns a project name to the booster, used for viewing related queues in funboost's Redis-stored info by project name.
    # Without this, it's hard to distinguish which queue names belong to which project from Redis-stored funboost info. Mainly used for web interface viewing.
    # The queue names for a project are stored in a Redis set with key f'funboost.project_name:{project_name}'.
    # Usually used together with CareProjectNameEnv.set($project_name), so you can "only see your own domain" during monitoring and management, avoiding noise from other projects' queues."""
    project_name: typing.Optional[str] = None

    """If qps is set and concurrent_num is at the default 50, it will auto-expand to 500 concurrent. Since the smart thread pool won't actually start that many threads when tasks are few, and it auto-shrinks thread count,
    see ThreadPoolExecutorShrinkAble for details.
    Thanks to the powerful qps-based frequency control and the smart expanding/shrinking thread pool, this framework recommends ignoring concurrent_num and only caring about qps. Concurrency is self-adaptive, which is very powerful and convenient."""
    concurrent_mode: str = ConcurrentModeEnum.THREADING  # Concurrency mode; supports THREADING, GEVENT, EVENTLET, ASYNC, SINGLE_THREAD. multi_process_consume supports coroutine/thread stacked with multi-process for blazing performance.
    concurrent_num: int = 50  # Concurrency count; the type of concurrency is determined by concurrent_mode.
    specify_concurrent_pool: typing.Optional[FunboostBaseConcurrentPool] = None  # Use a specified thread pool / coroutine pool. Multiple consumers can share one thread pool to save threads. When not None, threads_num is ignored.

    specify_async_loop: typing.Optional[asyncio.AbstractEventLoop] = None  # Specify the async event loop. Only takes effect when concurrent_mode is set to async. Some packages like aiohttp require requests and the httpclient instantiation to be in the same loop; pass it here if needed.
    is_auto_start_specify_async_loop_in_child_thread: bool = True  # Whether to automatically start the specified async loop in a child thread of funboost's asyncio pool. Only takes effect when concurrent_mode is async. If False, the user must manually call loop.run_forever() in their own code.
    
    """qps:
    A powerful throttling feature. Specifies the number of function executions per second. E.g. 0.01 means once every 100 seconds; 50 means 50 times per second. None means no throttling.
    When qps is set, you don't need to specify concurrent_num; funboost adaptively and dynamically adjusts the concurrency pool size."""
    qps: typing.Union[float, int, None] = None
    """is_using_distributed_frequency_control:
    Whether to use distributed frequency control (relies on Redis to count consumer instances, then divides the rate equally). By default, frequency control only applies to the current consumer instance.
    If 2 consumers with qps=10 using the same queue name are started, the total executions per second will be 20.
    With distributed frequency control, the total executions per second across all consumers is 10."""
    is_using_distributed_frequency_control: bool = False

    is_send_consumer_heartbeat_to_redis: bool = False  # Whether to send the consumer's heartbeat to Redis. Some features require counting active consumers. Since some brokers are not true MQ, this feature requires Redis to be installed.
    
    # --------------- Retry configuration start
    """max_retry_times:
    Maximum number of automatic retries. When the function errors, it immediately retries up to n times. Useful for certain unstable conditions.
    You can actively raise ExceptionForRetry in the function to trigger an immediate auto-retry.
    Raising ExceptionForRequeue will return the current message to the broker.
    Raising ExceptionForPushToDlxqueue will send the message to a separate dead-letter queue; the dead-letter queue name is queue_name + _dlx."""
    max_retry_times: int = 3

    """
    is_using_advanced_retry:
    Whether to use advanced retry, which supports exponential backoff. is_using_advanced_retry=True must be set for this to take effect.

    Retry intervals have 2 modes: requeue mode and sleep mode.
    requeue mode: Sends the message back to the queue with a delay, immediately releasing the thread. Suitable for large retry intervals, prevents long sleeps from occupying threads and reducing system throughput.
    sleep mode: Sleeps in the current thread/coroutine before retrying. Suitable for small retry intervals and infrequent messages. Sleep in this mode occupies the worker thread/coroutine.

    If retry_base_interval=1.0, retry_multiplier=2.0, retry_max_interval=60.0, the retry intervals are:
    1s, 2s, 4s, 8s, 16s, 32s, 60s, 60s, 60s...
    """
    is_using_advanced_retry: bool = False
    advanced_retry_config :dict =  {
        'retry_mode': 'sleep', # Can be 'sleep' or 'requeue'. If retry intervals are large and the exponential backoff multiplier is large, use requeue mode to avoid sleep occupying threads/coroutines and reducing service throughput.
        'retry_base_interval': 1.0, # Base retry interval (seconds): 1s, 2s, 4s, 8s, 16s, 30s, 30s, 30s...
        'retry_multiplier': 2.0, # Exponential backoff multiplier. Set to 1.0 for fixed retry intervals.
        'retry_max_interval': 60.0, # Maximum retry interval cap (seconds)
        'retry_jitter': False, # Whether to add random jitter
    }

    is_push_to_dlx_queue_when_retry_max_times: bool = False  # Whether to send to the dead-letter queue if the function still fails after reaching max_retry_times. Dead-letter queue name is queue_name + _dlx.
    # --------------- Retry configuration end

    consuming_function_decorator: typing.Optional[typing.Callable[..., typing.Any]] = None  # Function decorator. Since this framework auto-resolves parameters and needs accurate parameter names, it does not support stacking @*args/**kwargs decorators on consuming functions. Specify decorators here if needed.
    
    
    """
    function_timeout:
    Timeout in seconds. If the function runs longer than this, it is automatically killed. 0 means no limit.
    Users should prefer using timeout settings from third-party packages (e.g. aiohttp, pymysql socket timeout) rather than blindly using funboost's function_timeout.
    Use with caution; avoid setting a timeout unless necessary. Setting it reduces performance (because the user function must be wrapped and run in a separate thread), and forcefully killing a running function may cause deadlocks.
    (For example, if the user function is killed after acquiring a thread lock, other threads can never acquire the lock again.)
    """
    function_timeout: typing.Union[int, float,None] = None
    """
    is_support_remote_kill_task:
    Whether to support remote task killing. Only set to True if tasks are few, individual tasks take a long time, and you genuinely need to remotely send a command to kill a running function. Otherwise this feature is not recommended.
    (Implemented by running the function in a separate thread, always ready to be killed by a remote command, so performance is reduced.)
    """
    is_support_remote_kill_task: bool = False

    """
    log_level:
        The log level corresponding to logger_name.
        The log level for consumers and publishers. It is recommended to set DEBUG level; otherwise you won't know what messages are being processed.
        This is funboost's per-queue individual namespace log level; it will not affect user's other loggers or the root namespace log level at all. DEBUG level is fine.
        Users who don't understand Python logger name should not change the level out of curiosity.
        If you don't understand Python log namespacing, read the nb_log docs or ask an AI model what Python logger name means.
    """
    log_level: int = logging.DEBUG # No need to change this level; see the reason above.
    logger_prefix: str = ''  # Logger name prefix; can set a prefix.
    create_logger_file: bool = True  # Whether the publisher and consumer create a file log. False means only console output, no file written.
    logger_name: typing.Union[str, None] = ''  # Queue consumer/publisher log namespace.
    log_filename: typing.Union[str, None] = None  # Consumer/publisher file log name. If None, automatically uses 'funboost.{queue_name}' as the file log name. The log folder is determined by LOG_PATH in nb_log_config.py.
    is_show_message_get_from_broker: bool = False  # Whether to log the message content retrieved from the message queue at runtime.
    is_print_detail_exception: bool = True  # Whether to print detailed error stack trace when the consuming function errors. False means only a brief error message without the stack trace.
    publish_msg_log_use_full_msg: bool = False # Whether the publish log shows the full message body or just the function input params.

    msg_expire_seconds: typing.Union[float, int,None] = None  # Message expiry time. Messages published longer ago than this value will be discarded and not executed. None means never discard.

    do_task_filtering: bool = False  # Whether to deduplicate/filter function input params.
    task_filtering_expire_seconds: int = 0  # Expiry duration for task filtering. 0 means permanent filtering. E.g. setting 1800 seconds means: if a task with params 1+2 was published within the last 30 minutes, it won't execute again; if it was published more than 30 minutes ago, it will execute.

    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_result=False, is_save_status=False, expire_seconds=7 * 24 * 3600, is_use_bulk_insert=False)  # Whether to save function input params, results, and runtime status to MongoDB. Used for later parameter tracing, task statistics, and web display. Requires MongoDB to be installed.

    user_custom_record_process_info_func: typing.Optional[typing.Callable[..., typing.Any]] = None  # Provide a user-defined function to save message processing records somewhere (e.g. MySQL). The function accepts only one argument of type FunctionResultStatus; users can print the parameter.

    is_using_rpc_mode: bool = False  # Whether to use RPC mode. Allows the publisher to obtain the consumer's result callback, but at some performance cost. Accessing async_result.result will block the current thread until the function completes.
    rpc_result_expire_seconds: int = 1800  # Expiry time for RPC results stored in Redis.
    rpc_timeout:int = 1800 # Timeout for waiting for RPC result to return in RPC mode.

    delay_task_apscheduler_jobstores_kind :str = 'redis'  # Which jobstore type to use for the apscheduler object for delayed tasks; can be 'redis' or 'memory'.

    
    """
    allow_run_time_cron:
    Only allow running within the specified crontab expression time window.

    E.g. '* 23,0-2 * * *' means only run from 23:00 to 02:59.
    allow_run_time_cron='* 9-17 * * 1-5' means only run Monday to Friday from 09:00 to 17:59:59.
    None means no time restriction.
    The syntax is from the well-known croniter package, not funboost-specific syntax. Users should learn it via Google or AI.
    """
    allow_run_time_cron: typing.Optional[str] = None

    schedule_tasks_on_main_thread: bool = False  # Schedule tasks directly on the main thread, meaning you cannot start two consumers on the same main thread at the same time.

    is_auto_start_consuming_message: bool = False  # Whether to auto-start consuming after definition, without needing the user to manually call .consume() to start message consumption.

    # booster_group: Consumer group name. BoostersManager.consume_group starts multiple consuming functions based on booster_group, reducing the need to write f1.consume() f2.consume() etc.
    # Unlike BoostersManager.consume_all() which starts all unrelated consuming functions, and unlike f1.consume() f2.consume() which requires starting each individually.
    # Different groups can be created based on business logic for flexible consumption startup strategies.
    # See section 4.2d.3 in the documentation. Use BoostersManager.consume_group to start a group of consuming functions.
    booster_group:typing.Union[str, None] = None

    consuming_function: typing.Optional[typing.Callable[..., typing.Any]] = None  # The consuming function. No need to specify in @boost because the decorator knows the decorated function.
    consuming_function_raw: typing.Optional[typing.Callable[..., typing.Any]] = None  # No need to pass; auto-generated.
    consuming_function_name: str = '' # No need to pass; auto-generated.


    """
    # Adds non-universal exclusive configuration for different broker types. Each broker has its own unique config that is not compatible with all brokers.
    # Since the framework supports 30 message queues, and message queues are more complex than simple FIFO queues:
    # e.g. kafka supports consumer groups, rabbitmq supports various unique concepts like various ack mechanisms and complex routing,
    # some brokers natively support message priority while others don't.
    # Each message queue has unique config parameter semantics, which can be passed here.
    # For the key-value pairs each broker supports, see the BROKER_EXCLUSIVE_CONFIG_DEFAULT attribute in funboost/core/broker_kind__exclusive_config_default.py.
    """
    broker_exclusive_config: dict = {}
    


    should_check_publish_func_params: bool = True  # Whether to validate the published message content. E.g. if someone publishes a message but the function only accepts a and b, and they pass extra params or non-existent param names. If the consuming function uses a *args/**kwargs decorator, you need to disable this check.
    manual_func_input_params :dict= {'is_manual_func_input_params': False,'must_arg_name_list':[],'optional_arg_name_list':[]} # You can also manually specify function input fields; by default this is auto-generated from the consuming function's def signature.


    consumer_override_cls: typing.Optional[typing.Type] = None  # Use consumer_override_cls and publisher_override_cls to customize or extend consumers/publishers; see section 4.21b in the docs.
    publisher_override_cls: typing.Optional[typing.Type] = None

    # func_params_is_pydantic_model: bool = False  # funboost supports functions that accept pydantic model types; funboost auto-converts before publishing and when retrieving.

    consuming_function_kind: typing.Optional[str] = None  # Auto-generated info; no need for users to pass this unless auto-detection is wrong. Determines whether the consuming function is a plain function, instance method, or class method. If passed, auto-detection is skipped.
    """ consuming_function_kind can be one of the following:
    class FunctionKind:
        CLASS_METHOD = 'CLASS_METHOD'
        INSTANCE_METHOD = 'INSTANCE_METHOD'
        STATIC_METHOD = 'STATIC_METHOD'
        COMMON_FUNCTION = 'COMMON_FUNCTION'
    """

    """
    user_options:
    User-defined extra configuration. Useful for advanced users or unusual requirements; users can store any settings freely.
    user_options provides a unified user-defined namespace for passing configuration for "unusual requirements" or "advanced customizations" without waiting for the framework developer to add official support.
    funboost is a free framework, not a restrictive one. Not only is the consuming function logic free and directory structure free, but custom extensions should also be free. Users don't need to modify BoosterParams source code to add decorator parameters.

    See section 4b.6 in the docs for usage scenarios.
    """
    user_options: dict = {} # User-defined configuration; useful for advanced users or unusual requirements. Store any settings freely, e.g. read in consumer_override_cls or use with register_custom_broker.


    auto_generate_info: dict = {}  # Auto-generated information; users do not need to pass this. Contains e.g. final_func_input_params_info and where_to_instantiate.

    """# is_fake_booster: Whether this is a fake booster.
    # Used in faas mode where cross-project faas management only retrieves basic Redis metadata, without the actual booster function logic.
    # For example, ApsJobAdder manages scheduled tasks and needs a booster, but has no real function logic.
    # See SingleQueueConusmerParamsGetter.gen_booster_for_faas for usage. Currently mainly controls whether BoostersManager.regist_booster is executed.
    # Regular users don't need to change this parameter at all.
    """
    is_fake_booster: bool = False

    # Regular users don't need to manage or change this. Used to isolate booster registration.
    # E.g. faas fake cross-service cross-project boosters have no specific function logic and must not pollute the real registration.
    # If you want to start a subset of boosters by group, use the booster_group parameter instead.
    booster_registry_name: str = StrConst.BOOSTER_REGISTRY_NAME_DEFAULT


    def __init__(self, **data):
        # Remove deprecated old fields before Pydantic validation, to prevent extra="forbid" from raising a ValidationError at __init__ time.
        # Main scenario: when restoring BoosterParams from Redis metadata, the metadata may contain fields removed in old versions.
        for old_field in BoosterParamsFieldsAssit.has_been_deleted_fields:
            data.pop(old_field, None)
        for old_field, new_field in BoosterParamsFieldsAssit.rename_fields.items():
            if old_field in data:
                data[new_field] = data.pop(old_field)
        super().__init__(**data)

    @compatible_root_validator(skip_on_failure=True, )
    def check_values(self):

        # If qps is set and concurrent_num is the default 50, it auto-expands to 500 concurrent.
        # Since the smart thread pool doesn't actually start that many threads when tasks are few and auto-shrinks thread count, see ThreadPoolExecutorShrinkAble for details.
        # Thanks to the powerful qps control and smart expanding/shrinking thread pool, this framework recommends ignoring concurrent_num and only caring about qps. Concurrency is self-adaptive, which is very powerful.
        if self.qps and self.concurrent_num == 50:
            self.concurrent_num = 500
        if self.concurrent_mode == ConcurrentModeEnum.SINGLE_THREAD:
            self.concurrent_num = 1

        self.is_send_consumer_heartbeat_to_redis = self.is_send_consumer_heartbeat_to_redis or self.is_using_distributed_frequency_control

        if self.concurrent_mode not in ConcurrentModeEnum.__dict__.values():
            raise ValueError('The concurrency mode set is invalid.')
        if self.broker_kind in [BrokerEnum.REDIS_ACK_ABLE, BrokerEnum.REDIS_STREAM,
                                 BrokerEnum.REDIS_PRIORITY, 
                                     BrokerEnum.REDIS_BRPOP_LPUSH,BrokerEnum.REDIS,
                                     BrokerEnum.REDIS_PUBSUB] or 'REDIS' in self.broker_kind:
            self.is_send_consumer_heartbeat_to_redis = True  # A heartbeat process is needed to help determine whether messages belong to a disconnected or shut-down process and need to be re-queued
       
        if self.function_result_status_persistance_conf.table_name is None:
            self.function_result_status_persistance_conf.table_name = self.queue_name
        
        # Subclasses are not allowed to add fields not present in BoosterParams.
        # This prevents typos in user subclasses where the intent was to override a parent field default, but instead a new field was added.
        # Compatible with Pydantic v1 and v2 for getting all fields.
        self_fields = self.model_fields.keys() if hasattr(self, 'model_fields') else self.__fields__.keys()
        parent_fields = BoosterParams.model_fields.keys() if hasattr(BoosterParams, 'model_fields') else BoosterParams.__fields__.keys()
        for k in self_fields:
            if k not in parent_fields:
                raise ValueError(f'{self.__class__.__name__} added a field "{k}" that does not exist in the parent class BoosterParams.')  # BoosterParams subclasses can only override fields, not add new ones.
        
        return self

    def __call__(self, func):
        """
        New syntax alternative.
        Normally you use @boost(BoosterParams(queue_name='q1', qps=2)); for convenience you can also use @BoosterParams(queue_name='q1', qps=2).

        @BoosterParams(queue_name='q1', qps=2) is equivalent to @boost(BoosterParams(queue_name='q1', qps=2)).

        @BoosterParams(queue_name='q1', qps=2)
        def f(a, b):
            print(a, b)
        :param func:
        :return:
        """
        return funboost_lazy_impoter.boost(self)(func)




class BoosterParamsComplete(BoosterParams):
    """
    Example subclass. This BoosterParams subclass can be used as the parameter for @boost, allowing each @boost to omit some repeated fields.

    function_result_status_persistance_conf: Always enables function consumption status/result persistence.
    is_send_consumer_heartbeat_to_redis: Always sends consumer heartbeat to Redis, convenient for counting active consumers in distributed environments.
    is_using_rpc_mode: Always enables RPC mode.
    broker_kind: Always uses RabbitMQ via the amqpstorm package as the message queue.
    specify_concurrent_pool: Different booster functions in the same process share a thread pool, improving thread resource utilization.
    """

    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_result=True, is_save_status=True, expire_seconds=7 * 24 * 3600, is_use_bulk_insert=True)  # Enable function consumption status/result persistence to MongoDB. When True, users must install MongoDB, at a slight performance cost.
    is_send_consumer_heartbeat_to_redis: bool = True  # Send consumer heartbeat to Redis. When True, users must install Redis.
    is_using_rpc_mode: bool = True  # Always enable RPC mode; no need to specify each time. (Users who don't need RPC mode should not set this to True; requires Redis and has a small performance overhead.)
    rpc_result_expire_seconds: int = 3600
    broker_kind: str = BrokerEnum.RABBITMQ_AMQPSTORM  # Always use RabbitMQ; no need to specify each time.
    specify_concurrent_pool: FunboostBaseConcurrentPool = Field(default_factory=functools.partial(ConcurrentPoolBuilder.get_pool, FlexibleThreadPool, 500))  # Multiple consuming functions share a thread pool.


class TaskOptions(BaseJsonAbleModel):
    """
    Extra parameters supported by publish, published to the broker together with the function parameters.
    There may be occasional needs for this. If you need to publish extra fields to the message queue, you must use the publish method;
    push is like Celery's delay and can only publish the function's own input params.
    Non-None field values here will be placed in the 'extra' field of the message.
    """
    # task_id, publish_time, and publish_time_format can be specified; if not, they are auto-generated.
    task_id: str = None
    publish_time: float = None
    publish_time_format: str = None

    # function_timeout, max_retry_times, is_print_detail_exception, msg_expire_seconds, is_using_rpc_mode are control parameters for consuming function execution.
    # These have higher priority than BoosterParams. E.g. if BoosterParams sets retry 3 times, you can set retry 10 times via TaskOptions; the consuming function will use the TaskOptions setting.
    # Settings in task_options take priority over those in @boost(BoosterParams(...)).
    function_timeout: typing.Union[float, int,None] = None
    max_retry_times: typing.Union[int,None] = None
    is_print_detail_exception: typing.Union[bool,None] = None
    msg_expire_seconds: typing.Union[float, int,None] = None
    is_using_rpc_mode: typing.Union[bool,None] = None

    # countdown, eta, misfire_grace_time are for publishing delayed tasks.
    countdown: typing.Union[float, int,None] = None
    eta: typing.Union[datetime.datetime, str,None] = None  # A datetime object or a %Y-%m-%d %H:%M:%S string.
    misfire_grace_time: typing.Union[int, None] = None

    user_extra_info: typing.Optional[dict] = None # User-defined extra info; users can store anything here, but must ensure it is JSON-serializable. Accessible on the consumer side via fct.full_msg.

    other_extra_params: typing.Optional[dict] = None  # Other parameters unique to certain brokers, e.g. message priority: task_options=TaskOptions(other_extra_params={'priority': priorityxx}).


    do_task_filtering: typing.Optional[bool] = None # Whether to enable task input filtering.
    """filter_str:
    User-specified filter string. E.g. if the function signature is def fun(userid, username, sex, user_description),
    by default all input params are combined as JSON for filtering. But really you only need to filter by userid.
    So users can flexibly specify a string for precise filtering.

    See section 4.35 in the docs.
    f3.publish(msg={'a':i,'b':i*2}, task_options=TaskOptions(filter_str=str(i)))
    """
    filter_str :typing.Optional[str] = None

    can_not_json_serializable_keys: typing.List[str] = None # Names of input params that cannot be JSON-serialized; these fields need to be deserialized with pickle. (This is auto-generated; users do not need to specify this manually.)

    otel_context :typing.Optional[dict] = None # OpenTelemetry context, used for distributed tracing.

    @compatible_root_validator(skip_on_failure=True)
    def cehck_values(self):
        if self.countdown and self.eta:
            raise ValueError('Cannot set both eta and countdown at the same time.')
        if self.misfire_grace_time is not None and self.misfire_grace_time < 1:
            raise ValueError(f'misfire_grace_time must either be an integer greater than 1, or None.')
        return self


# PriorityConsumingControlConfig = TaskOptions # Kept for backward compatibility with the old name

class PublisherParams(BaseJsonAbleModel):
    queue_name: str
    broker_kind: typing.Optional[str] = None

    # Project name. Defaults to None. Assigns a project name to the booster, used for viewing related queues in funboost's Redis-stored info by project name.
    # Without this, it's hard to distinguish which queue names belong to which project from Redis-stored funboost info. Mainly used for web interface viewing.
    project_name: typing.Optional[str] = None # Recommended to set

    log_level: int = logging.DEBUG
    logger_prefix: str = ''
    create_logger_file: bool = True
    logger_name: str = ''  # Queue consumer/publisher log namespace.
    log_filename: typing.Optional[str] = None
    clear_queue_within_init: bool = False  # When using with syntax publishing, clear the message queue first.
    consuming_function: typing.Optional[typing.Callable[..., typing.Any]] = None  # consuming_function is used for the inspect module to get function parameter info.

    broker_exclusive_config: dict = {}

    should_check_publish_func_params: bool = True  # Whether to validate the published message content. E.g. if someone's function only accepts a, b but passes 2 params or non-existent param names. If the consuming function uses *args/**kwargs, disable the publish-time function param check.
    manual_func_input_params :dict= {'is_manual_func_input_params': False,'must_arg_name_list':[],'optional_arg_name_list':[]}

    publisher_override_cls: typing.Optional[typing.Type] = None
    # func_params_is_pydantic_model: bool = False  # funboost supports functions that accept pydantic model types; funboost auto-converts before publishing and when retrieving.
    publish_msg_log_use_full_msg: bool = False # Whether the publish log shows the full message body or just the function input params.
    consuming_function_kind: typing.Optional[str] = None  # Auto-generated info; users do not need to pass this.
    rpc_timeout: int = 1800 # Timeout for waiting for RPC result to return in RPC mode.
    user_options: dict = {}  # User-defined configuration; useful for advanced users or unusual requirements. Store any settings freely.
    auto_generate_info: dict = {}
    is_fake_booster: bool = False # Whether this is a fake booster; not registered to BoostersManager.
    booster_registry_name: str = StrConst.BOOSTER_REGISTRY_NAME_DEFAULT  # Regular users don't need to manage or change this. Used to isolate booster registration. E.g. faas fake cross-service cross-project boosters must not pollute the real registration.
    
    


if __name__ == '__main__':
    from funboost.concurrent_pool import FlexibleThreadPool

    pass
    # print(FunctionResultStatusPersistanceConfig(is_save_result=True, is_save_status=True, expire_seconds=70 * 24 * 3600).update_from_kwargs(expire_seconds=100).get_str_dict())
    #
    # print(TaskOptions().get_str_dict())

    print(BoosterParams(queue_name='3213', 
                         function_result_status_persistance_conf= {
        "is_save_status": False,
        "is_save_result": False,
        "expire_seconds": 604800,
        "is_use_bulk_insert": False,
        "table_name": "3213"
    },
    is_fake_booster=True,
    is_do_not_run_by_specify_time_effect=False,
                        
                        specify_concurrent_pool=FlexibleThreadPool(100)).json_pre())
    # print(PublisherParams.schema_json())  # Commented out because PublisherParams contains Callable type fields which cannot generate a JSON Schema
