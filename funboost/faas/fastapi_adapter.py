
"""
FastAPI out-of-the-box: simply use app.include_router(fastapi_router) to automatically add common routes to the user's FastAPI app, implementing FaaS.




Usage:
    In the user's own FastAPI project:
       app.include_router(fastapi_router)



If you feel you need to add authentication when integrating fastapi_router into your own FastAPI app, you can do this:
app.include_router(
    fastapi_router,
    dependencies=[
        Depends(your_authenticate),
    ]
)

"""

import traceback
import typing
import asyncio

from funboost import AioAsyncResult, AsyncResult, TaskOptions, BoosterParams, Booster

from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter, QueuesConusmerParamsGetter,CareProjectNameEnv
from funboost.core.exceptions import FunboostException
from fastapi import FastAPI, APIRouter, Query, Request
from fastapi.responses import JSONResponse


try:
    from pydantic import BaseModel, ConfigDict  # v2
    pydantic_version = 'v2'
except ImportError:
    from pydantic import BaseModel              # v1
    ConfigDict = None
    pydantic_version = 'v1'
from funboost.core.loggers import get_funboost_file_logger
from funboost.utils.redis_manager import RedisMixin
from funboost.constant import RedisKeys
from funboost.faas.faas_util import gen_aps_job_adder
# from funboost.core.func_params_model import BoosterParams
from funboost.core.func_params_model import BoosterParamsFieldsAssit

logger = get_funboost_file_logger(__name__)





# Create Router instance for users to include in their own app
# Users can use app.include_router(fastapi_router)
fastapi_router = APIRouter(prefix='/funboost', tags=['funboost'])





# ==================== FastAPI app exception handler decorators ====================
# This will affect the user's own app; it depends on user preference, since some users have custom responses, not funboost fastapi_router's BaseResponse.

async def funboost_exception_handler(request: Request, exc: FunboostException) -> JSONResponse:
    """
    Unified handler for FunboostException type exceptions.
    Automatically extracts the exception's code, message, data, etc. and returns them to the frontend.
    """
    # Note: we cannot directly return BaseResponse here because FastAPI's exception handler requires returning a Response object
    # But we can use BaseResponse's structure to maintain format consistency
    response_data = {
        "succ": False,
        "msg": exc.message,
        "code": exc.code or 5000,
        "error_data": exc.error_data,
        "error": exc.__class__.__name__,
        "traceback": None,  # FunboostException does not return traceback
        "trace_id": getattr(exc, "trace_id", None)
    }
    return JSONResponse(
        status_code=200,  # HTTP status code still returns 200, business errors are distinguished by code
        content=response_data
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Unified handler for all other exceptions.
    Returns a fixed code 5555 and includes the full exception traceback.
    """
    logger.exception(f'Unexpected exception: {str(exc)}')
    response_data = {
        "succ": False,
        "msg": f"System error: {type(exc).__name__}: {str(exc)}",
        "code": 5555,
        "error_data": None,
        "error": type(exc).__name__,
        "traceback": traceback.format_exc(),
        "trace_id": None
    }
    return JSONResponse(
        status_code=200,  # HTTP status code still returns 200, business errors are distinguished by code
        content=response_data
    )


def register_funboost_exception_handlers(app: FastAPI):
    """
    Register Funboost's global exception handlers to the FastAPI app.

    Usage example:
        from funboost.faas.fastapi_adapter import fastapi_router, register_funboost_exception_handlers

        app = FastAPI()
        app.include_router(fastapi_router)
        register_funboost_exception_handlers(app)  # Register global exception handling
    """
    app.add_exception_handler(FunboostException, funboost_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)




# ==================== Funboost Router Exception Handling Decorator ====================
# Only applies to funboost router endpoints, does not affect the user's own app

def handle_funboost_exceptions(func):
    """
    Decorator: unified exception handling for funboost router endpoints.
    Only used in funboost endpoints, does not affect the user's own FastAPI app.

    Usage:
        @fastapi_router.get("/some_endpoint")
        @handle_funboost_exceptions
        async def some_endpoint():
            # Write business logic directly, no try-except needed
            return BaseResponse(...)

    Exception handling rules:
        - FunboostException: returns the exception's code, message, data, trace_id
        - Other exceptions: returns code 5555, includes full traceback
    """
    import functools
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            # If it's an async function
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except FunboostException as e:
            # Handle FunboostException
            # print(4444,e.to_dict())
            return BaseResponse(
                succ=False,
                msg=e.message,
                code=e.code or 5000,
                error_data=e.error_data,
                error=e.__class__.__name__,
                traceback=traceback.format_exc(),  
                trace_id=getattr(e, "trace_id", None)
            )
        except Exception as e:
            # Handle other exceptions
            logger.exception(f'Unexpected exception: {str(e)}')
            return BaseResponse(
                succ=False,
                msg=f"System error: {type(e).__name__}: {str(e)}",
                code=5555,
                error_data=None,
                error=type(e).__name__,
                traceback=traceback.format_exc(),
                trace_id=None
            )
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FunboostException as e:
            # Handle FunboostException
            # print(4444,e.to_dict())
            return BaseResponse(
                succ=False,
                msg=e.message,
                code=e.code or 5000,
                error_data=e.error_data,
                error=e.__class__.__name__,
                traceback=traceback.format_exc(),  
                trace_id=getattr(e, "trace_id", None)
            )
        except Exception as e:
            # Handle other exceptions
            logger.exception(f'Unexpected exception: {str(e)}')
            return BaseResponse(
                succ=False,
                msg=f"System error: {type(e).__name__}: {str(e)}",
                code=5555,
                error_data=None,
                error=type(e).__name__,
                traceback=traceback.format_exc(),
                trace_id=None
            )
    
    # Return the corresponding wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper



class BaseAllowExtraModel(BaseModel):
    
    if pydantic_version == 'v2':
        # Pydantic v2 usage
        model_config = ConfigDict(extra="allow")

    elif pydantic_version == 'v1':
        # Pydantic v1 usage
        class Config:
            extra = "allow"



# Unified response model (generic)
T = typing.TypeVar('T')

class BaseResponse(BaseModel, typing.Generic[T]):
    """
    Unified generic response model.

    Field descriptions:
        succ: Whether the request succeeded, True for success, False for failure
        msg: Message description
        data: Returned data, using generic T
        code: Business status code, 200 means success, others indicate various errors
        error: Error type name (optional), e.g., "QueueNameNotExists", "ValueError"
        traceback: Exception traceback info (optional), only returned on errors
        trace_id: Trace ID (optional), for distributed tracing
    """
    succ: bool
    msg: str
    data: typing.Optional[T] = None
    error_data: typing.Optional[typing.Dict] = None
    code: typing.Optional[int] = 200
    error: typing.Optional[str] = None
    traceback: typing.Optional[str] = None
    trace_id: typing.Optional[str] = None


class MsgItem(BaseModel):
    queue_name: str  # Queue name
    msg_body: dict  # Message body, i.e., the boost function's input parameter dictionary, e.g., {"x":1,"y":2}
    need_result: bool = False  # Whether to return the result after publishing the message
    timeout: int = 60  # Maximum wait time for result to return
    task_id: str = None  # Optional: specify task_id


# Unified response format data structures

# Detailed model for function execution result status (references FunctionResultStatus)
class FunctionResultStatusModel(BaseModel):
    """
    Function execution result status model.
    Corresponds to the return value structure of FunctionResultStatus.get_status_dict()
    """
    # Basic info
    host_process: str  # Host name - Process ID, e.g., "LAPTOP-7V78BBO2 - 34572"
    queue_name: str  # Queue name
    function: str  # Function name

    # Message info
    msg_dict: dict  # Original message dictionary
    task_id: str  # Task ID

    # Process and thread info
    process_id: int  # Process ID
    thread_id: int  # Thread ID
    total_thread: int  # Total active threads

    # Time info
    publish_time: float  # Publish time (timestamp)
    publish_time_format: str  # Formatted publish time string, e.g., "2025-12-05 13:28:12"
    time_start: float  # Execution start time (timestamp)
    time_cost: typing.Optional[float]  # Execution duration (seconds)
    time_end: float  # End time (timestamp)
    insert_time_str: str  # Insert time string, e.g., "2025-12-05 13:28:13"
    insert_minutes: str  # Insert time rounded to minute, e.g., "2025-12-05 13:28"

    # Parameter info
    params: dict  # Function parameters (dict form)
    params_str: str  # Function parameters (JSON string form)

    # Execution result info
    result: typing.Any  # Function execution result
    run_times: int  # Number of runs
    success: bool  # Whether successful
    run_status: str  # Run status: 'running' or 'finish'

    # Exception info (optional)
    exception: typing.Optional[str]  # Exception details
    exception_type: typing.Optional[str]  # Exception type
    exception_msg: typing.Optional[str]  # Exception message
    rpc_chain_error_msg_dict: typing.Optional[dict]  # RPC chain call error info

    # RPC config
    rpc_result_expire_seconds: typing.Optional[int]  # RPC result expiration time (seconds)

    # Host info
    host_name: str  # Host name, e.g., "LAPTOP-7V78BBO2"
    script_name: str  # Script name (short), e.g., "example_fastapi_router.py"
    script_name_long: str  # Script name (full path)

    user_context: typing.Optional[dict] = {}  # User-defined extra info, users can store any information here.

    # MongoDB document ID
    _id: str  # MongoDB document ID, usually equals task_id

    class Config:
        # Allow field aliases (e.g., _id)
        populate_by_name = True


class RpcRespData(BaseAllowExtraModel):
    task_id: typing.Optional[str] = None
    status_and_result: typing.Optional[FunctionResultStatusModel] = None  # Consumer function's consumption status and result


class CountData(BaseModel):
    queue_name: str
    count: int = -1


class AllQueuesData(BaseModel):
    queues: typing.List[str] = []
    count: int = 0


class DeprecateQueueRequest(BaseModel):
    """Deprecate queue request model"""
    queue_name: str  # Queue name to deprecate


class DeprecateQueueData(BaseModel):
    """Deprecate queue response data model"""
    queue_name: str
    removed: bool  # Whether removal was successful


@fastapi_router.post("/publish", response_model=BaseResponse[RpcRespData])
async def publish_msg(msg_item: MsgItem):
    """
    Publish message endpoint, supports RPC mode.
    Supports validation of whether queue_name exists and whether message content is correct. So there's no need to worry about cross-department users using wrong queue_name or incorrect message content.

    Users can first get all queue configuration info via the /get_queues_config endpoint to know which queues exist and what input parameter fields each queue's consumer function requires.
    # When publishing a message, the input parameters are immediately validated using the auto_generate_info.final_func_input_params_info from the booster config in redis to check if parameter names and count are correct.
    """
    status_and_result = None
    task_id = None
    try:
        # SingleQueueConusmerParamsGetter(msg_item.queue_name).gen_publisher_for_faas() generates publisher from funboost's redis config
        # No need for users to manually determine queue_name and then precisely use a specific consumer function,


        publisher = SingleQueueConusmerParamsGetter(msg_item.queue_name).gen_publisher_for_faas()
        booster_params_by_redis = SingleQueueConusmerParamsGetter(msg_item.queue_name).get_one_queue_params_use_cache()
        
        # Check if RPC mode is needed
        if msg_item.need_result:

            # Publish with RPC mode enabled
            async_result = await publisher.aio_publish(
                msg_item.msg_body,
                task_id=msg_item.task_id,  # Optional: specify task_id (for retrying failed tasks)
                task_options=TaskOptions(is_using_rpc_mode=True)
            )
            task_id = async_result.task_id
            # Wait for result
            status_and_result = await AioAsyncResult(async_result.task_id, timeout=msg_item.timeout).status_and_result
        else:
            # Normal publish, can specify task_id
            async_result = await publisher.aio_publish(msg_item.msg_body, task_id=msg_item.task_id)
            task_id = async_result.task_id

        return BaseResponse[RpcRespData](
            succ=True,
            msg=f'{msg_item.queue_name} queue, message published successfully',
            data=RpcRespData(
                task_id=task_id,
                status_and_result=status_and_result
            )
        )
    except Exception as e:
        logger.exception(f'Failed to publish message: {str(e)}')
        return BaseResponse[RpcRespData](
            succ=False,
            msg=f'{msg_item.queue_name} queue, message publish failed {type(e)} {e} {traceback.format_exc()}',
            data=RpcRespData(
                task_id=task_id,
                status_and_result=status_and_result
            )
        )


@fastapi_router.get("/get_result", response_model=BaseResponse[RpcRespData])
async def get_result(task_id: str, timeout: int = 5,):
    """
    Get task execution result by task_id
    """
    try:
        # Try to get the result, default to a short timeout to prevent blocking indefinitely, or reuse AioAsyncResult's logic
        # Note: if the task is still running, AioAsyncResult will block until timeout
        # If the task has already completed and expired, this may return None
        status_and_result = await AioAsyncResult(task_id, timeout=timeout).status_and_result
        
        if status_and_result:
            return BaseResponse[RpcRespData](
                succ=True,
                msg="Retrieved successfully",
                data=RpcRespData(
                    task_id=task_id,
                    status_and_result=status_and_result
                )
            )
        else:
            return BaseResponse[RpcRespData](
                succ=False,
                msg="No result retrieved (possibly expired, not started, timed out, or consumer not started at all)",
                data=RpcRespData(
                    task_id=task_id,
                    status_and_result=None
                )
            )
            
    except Exception as e:
        logger.exception(f'Failed to get result: {str(e)}')
        return BaseResponse[RpcRespData](
            succ=False,
            msg=f"Error getting result: {str(e)}",
            data=RpcRespData(
                task_id=task_id,
                status_and_result=None
            )
        )


# Queue control endpoints (pause/resume)

class QueueNameRequest(BaseModel):
    """Queue name request model"""
    queue_name: str


class QueueControlData(BaseModel):
    """Response data for queue control operations"""
    queue_name: str
    success: bool


@fastapi_router.post("/pause_consume", response_model=BaseResponse[QueueControlData])
def pause_consume(request: QueueNameRequest):
    """
    Pause queue consumption.

    Request body:
        {
            "queue_name": "queue name"
        }

    Returns:
        Result of the pause operation.

    Notes:
        This endpoint sets the pause flag to '1' in Redis. Consumers will periodically check this flag and pause consumption.
        Pausing does not take effect immediately; it requires waiting for the consumer's flag check interval.
    """
    try:
        
        
        RedisMixin().redis_db_frame.hset(RedisKeys.REDIS_KEY_PAUSE_FLAG, request.queue_name, '1')
        
        return BaseResponse[QueueControlData](
            succ=True,
            msg=f"队列 {request.queue_name} paused successfully",
            data=QueueControlData(
                queue_name=request.queue_name,
                success=True
            )
        )
    except Exception as e:
        logger.exception(f'Failed to pause queue consumption: {str(e)}')
        return BaseResponse[QueueControlData](
            succ=False,
            msg=f"Pause queue {request.queue_name} 失败: {str(e)}",
            data=QueueControlData(
                queue_name=request.queue_name,
                success=False
            )
        )


@fastapi_router.post("/resume_consume", response_model=BaseResponse[QueueControlData])
def resume_consume(request: QueueNameRequest):
    """
    Resume queue consumption.

    Request body:
        {
            "queue_name": "queue name"
        }

    Returns:
        Result of the resume operation.

    Notes:
        This endpoint sets the pause flag to '0' in Redis. Consumers will periodically check this flag and resume consumption.
        Resuming does not take effect immediately; it requires waiting for the consumer's flag check interval.
    """
    try:
        
        
        RedisMixin().redis_db_frame.hset(RedisKeys.REDIS_KEY_PAUSE_FLAG, request.queue_name, '0')
        
        return BaseResponse[QueueControlData](
            succ=True,
            msg=f"队列 {request.queue_name} resumed successfully",
            data=QueueControlData(
                queue_name=request.queue_name,
                success=True
            )
        )
    except Exception as e:
        logger.exception(f'Failed to resume queue consumption: {str(e)}')
        return BaseResponse[QueueControlData](
            succ=False,
            msg=f"Resume queue {request.queue_name} 失败: {str(e)}",
            data=QueueControlData(
                queue_name=request.queue_name,
                success=False
            )
        )



@fastapi_router.get("/get_msg_count", response_model=BaseResponse[CountData])
@handle_funboost_exceptions  # 使用装饰器统一处理异常，不影响用户的app
def get_msg_count(queue_name: str):
    """
    Get message count by queue_name.

    Note: this endpoint uses the @handle_funboost_exceptions decorator,
    so no try-except is needed; exceptions are automatically caught and returned in a unified format.
    """
    # Write business logic directly, no try-except needed
    publisher = SingleQueueConusmerParamsGetter(queue_name).gen_publisher_for_faas()
    # Get message count (Note: some middleware may not support accurate counting, returns -1)
    count = publisher.get_message_count()
    return BaseResponse[CountData](
        succ=True,
        msg="Retrieved successfully",
        data=CountData(
            queue_name=queue_name,
            count=count
        )
    )
# Queue clear endpoint

class ClearQueueData(BaseModel):
    """Clear queue response data"""
    queue_name: str
    success: bool


@fastapi_router.post("/clear_queue", response_model=BaseResponse[ClearQueueData])
def clear_queue(request: QueueNameRequest):
    """
    Clear all messages in the queue.

    Request body:
        {
            "queue_name": "queue name"
        }

    Returns:
        Result of the clear operation.

    Notes:
        This endpoint clears all pending messages in the specified queue.
        Warning: this operation is irreversible, use with caution!

    Note:
        broker_kind is automatically obtained from the registered booster, no need to specify manually.
    """
    try:
        # Automatically get the corresponding booster by queue_name
        publisher = SingleQueueConusmerParamsGetter(request.queue_name).gen_publisher_for_faas()
        publisher.clear()

        return BaseResponse[ClearQueueData](
            succ=True,
            msg=f"Queue {request.queue_name} cleared successfully",
            data=ClearQueueData(
                queue_name=request.queue_name,
                success=True
            )
        )
    except Exception as e:
        logger.exception(f'Failed to clear queue: {str(e)}')
        return BaseResponse[ClearQueueData](
            succ=False,
            msg=f"Failed to clear queue {request.queue_name}: {str(e)}",
            data=ClearQueueData(
                queue_name=request.queue_name,
                success=False
            )
        )




@fastapi_router.get("/get_all_queues", response_model=BaseResponse[AllQueuesData])
def get_all_queues():
    """
    Get all registered queue names.

    Returns a list of all queue names registered via the @boost decorator.
    """
    try:
        # Get all queue names
        all_queues = QueuesConusmerParamsGetter().get_all_queue_names()
        
        return BaseResponse[AllQueuesData](
            succ=True,
            msg="Retrieved successfully",
            data=AllQueuesData(
                queues=all_queues,
                count=len(all_queues)
            )
        )
    except Exception as e:
        logger.exception(f'Failed to get all queues: {str(e)}')
        return BaseResponse[AllQueuesData](
            succ=False,
            msg=f"Failed to get all queues: {str(e)}",
            data=AllQueuesData(
                queues=[],
                count=0
            )
        )




# Detailed queue configuration parameters model (references BoosterParams)
class QueueParams(BaseAllowExtraModel):
    """
    Complete configuration parameters for a queue.
    Unlike BoosterParams, this version is fully JSON-serializable.
    The data here is obtained from redis, which can only store JSON-serializable data.
    Therefore, fields like specify_async_loop and specify_concurrent_pool are changed to typing.Any.
    """
    
    def __init__(self, **data):
        for old_field in BoosterParamsFieldsAssit.has_been_deleted_fields:
            data.pop(old_field, None)
        for old_field, new_field in BoosterParamsFieldsAssit.rename_fields.items():
            if old_field in data:
                data[new_field] = data.pop(old_field)
        super().__init__(**data)

    # Basic configuration
    queue_name: str  # Queue name
    broker_kind: str  # Middleware type, e.g., REDIS, RABBITMQ, etc.
    project_name: typing.Optional[str] = None # Project name

    # Concurrency configuration
    concurrent_mode: str  # Concurrency mode: threading/gevent/eventlet/async/single_thread
    concurrent_num: int  # Number of concurrent workers
    specify_concurrent_pool: typing.Optional[typing.Any]  # Specified thread pool/coroutine pool
    specify_async_loop: typing.Optional[typing.Any]   # Specified async loop
    is_auto_start_specify_async_loop_in_child_thread: bool  # Whether to auto-start async loop in child thread

    # Rate control
    qps: typing.Optional[float]  # QPS limit (executions per second)
    is_using_distributed_frequency_control: bool  # Whether to use distributed rate control

    # Heartbeat and monitoring
    is_send_consumer_heartbeat_to_redis: bool  # Whether to send consumer heartbeat to redis

    # Retry configuration
    max_retry_times: int  # Maximum auto-retry count
    is_using_advanced_retry: bool  # Whether to use advanced retry
    advanced_retry_config: typing.Dict[str, typing.Any]  # Advanced retry configuration
    is_push_to_dlx_queue_when_retry_max_times: bool  # Whether to push to dead letter queue when max retries reached

    # Function decoration and timeout
    consuming_function_decorator: typing.Optional[typing.Any]    # Function decorator
    function_timeout: typing.Optional[float]  # Function timeout (seconds)
    is_support_remote_kill_task: bool  # Whether to support remote task killing

    # Logging configuration
    log_level: int  # Log level
    logger_prefix: str  # Logger name prefix
    create_logger_file: bool  # Whether to create file log
    logger_name: str  # Logger namespace
    log_filename: typing.Optional[str]  # Log filename
    is_show_message_get_from_broker: bool  # Whether to show messages received from broker
    is_print_detail_exception: bool  # Whether to print detailed exception traceback
    publish_msg_log_use_full_msg: bool  # Whether publish message log shows full message

    # Message expiration and filtering
    msg_expire_seconds: typing.Optional[float]  # Message expiration time (seconds)
    do_task_filtering: bool  # Whether to filter and deduplicate function input parameters
    task_filtering_expire_seconds: int  # Task filtering expiration period

    # Function result persistence
    function_result_status_persistance_conf: typing.Dict[str, typing.Any]  # Function result status persistence configuration

    # User custom
    user_custom_record_process_info_func: typing.Optional[typing.Any]  # User-defined function for saving message processing records

    # RPC mode
    is_using_rpc_mode: bool  # Whether to use RPC mode
    rpc_result_expire_seconds: int  # RPC result expiration time (seconds)
    rpc_timeout: int  # RPC timeout (seconds)

    # Delayed tasks
    delay_task_apscheduler_jobstores_kind: str  # Delayed task jobstore type: redis/memory

    # Scheduled run control
    allow_run_time_cron: typing.Optional[str] = None  # Only allow running during specified crontab expression times, None means no restriction

    # Startup control
    schedule_tasks_on_main_thread: bool  # Whether to schedule tasks on the main thread
    is_auto_start_consuming_message: bool  # Whether to auto-start consuming

    # Group management
    booster_group: typing.Optional[str]  # Consumer group name

    # Consumer function info
    consuming_function: typing.Any  # Consumer function
    consuming_function_raw: typing.Any  # Raw consumer function
    consuming_function_name: str  # Consumer function name

    # Middleware-specific configuration
    broker_exclusive_config: typing.Dict[str, typing.Any]  # Middleware-specific configurations

    # Parameter validation
    should_check_publish_func_params: bool  # Whether to validate function parameters when publishing
    manual_func_input_params :typing.Optional[typing.Dict[str, typing.Any]] = None # Manually specify function input parameter fields; by default, this is generated from the consumer function's def parameter definitions.

    # Custom override classes
    consumer_override_cls: typing.Optional[typing.Any]   # Custom consumer class
    publisher_override_cls: typing.Optional[typing.Any]   # Custom publisher class

    # Function type
    consuming_function_kind: typing.Optional[str]  # Function type: CLASS_METHOD/INSTANCE_METHOD/STATIC_METHOD/COMMON_FUNCTION

    # User custom configuration
    user_options: typing.Dict[str, typing.Any]  # User's additional custom configuration

    # Auto-generated info
    auto_generate_info: typing.Dict[str, typing.Any]  # Auto-generated info, contains final_func_input_params_info which stores function input parameter info. Users can also use this as a microservice API documentation protocol to clearly know what input parameters a message needs.

    # FaaS related
    is_fake_booster: bool = False  # Whether it is a fake booster, used for cross-project management in FaaS mode
    booster_registry_name: str = 'default'  # Used to isolate booster registrations, regular users don't need to change this

    

# 活跃消费者详细模型
class ActiveConsumerRunInfo(BaseAllowExtraModel):
    """
    单个活跃消费者的详细信息
    这些数据是从redis中的心跳信息获取的
    """
    # 基本信息
    queue_name: str  # 队列名
    computer_name: str  # 计算机名
    computer_ip: str  # 计算机IP地址
    process_id: int  # 进程ID
    consumer_id: int  # 消费者ID
    consumer_uuid: str  # 消费者UUID
    
    # 启动和心跳时间
    start_datetime_str: str  # 启动时间字符串，格式：YYYY-MM-DD HH:MM:SS
    start_timestamp: float  # 启动时间戳
    hearbeat_datetime_str: str  # 最近心跳时间字符串
    hearbeat_timestamp: float  # 最近心跳时间戳
    
    # 消费函数信息
    consuming_function: str  # 消费函数名
    code_filename: str  # 代码文件路径
    
    # 时间单位配置
    unit_time_for_count: int  # 统计的时间单位（秒）
    
    # 最近X秒执行统计
    last_x_s_execute_count: int  # 最近X秒执行次数
    last_x_s_execute_count_fail: int  # 最近X秒失败次数
    last_execute_task_time: float  # 最后一次执行任务的时间戳
    last_x_s_avarage_function_spend_time: typing.Optional[float]   # 最近X秒平均耗时（秒）
    last_x_s_total_cost_time: typing.Optional[float]  # 最近X秒总耗时（秒）
    
    # 消息队列状态
    msg_num_in_broker: int  # broker中的消息数量
    current_time_for_execute_task_times_every_unit_time: float  # 当前统计周期的开始时间戳
    last_timestamp_when_has_task_in_queue: float  # 最后一次队列有任务的时间戳
    
    # 从启动开始的统计
    total_consume_count_from_start: int  # 从启动开始的总执行次数
    total_consume_count_from_start_fail: int  # 从启动开始的总失败次数
    total_cost_time_from_start: float  # 从启动开始的总耗时（秒）
    avarage_function_spend_time_from_start: typing.Optional[float]  # 从启动开始的平均耗时（秒）


# 队列运行信息数据模型
class QueueParamsAndActiveConsumersData(BaseModel):
    """队列参数和活跃消费者数据"""
    queue_params: QueueParams  # 队列的booster入参大全
    active_consumers: typing.List[ActiveConsumerRunInfo]   # 队列对应的所有活跃消费者列表
    pause_flag: int  # 暂停标志
    msg_num_in_broker: int   # broker中的消息数量
    history_run_count: typing.Optional[int]   # 历史运行次数
    history_run_fail_count: typing.Optional[int]   # 历史失败次数
    all_consumers_last_x_s_execute_count: int   # 所有消费进程最近X秒所有消费者执行次数
    all_consumers_last_x_s_execute_count_fail: int   # 所有消费进程最近X秒所有消费者失败次数
    all_consumers_last_x_s_avarage_function_spend_time: typing.Optional[float]   # 所有消费进程最近X秒平均耗时
    all_consumers_avarage_function_spend_time_from_start: typing.Optional[float]   # 所有消费进程从启动开始的平均耗时
    all_consumers_total_consume_count_from_start: int   # 所有消费进程从启动开始总消费次数
    all_consumers_total_consume_count_from_start_fail: int   # 所有消费进程从启动开始总失败次数
    all_consumers_last_execute_task_time: typing.Optional[float]   # 所有消费进程中最后一次执行任务的时间戳


class QueueConfigData(BaseModel):
    """队列配置数据"""
    queues_config: typing.Dict[str, QueueParams] = {}
    count: int = 0


@fastapi_router.get("/get_queues_config", response_model=BaseResponse[QueueConfigData])
def get_queues_config():
    """
    获取所有队列的配置信息
    
    返回所有已注册队列的详细配置参数，包括：
    - 队列名称
    - broker 类型
    - 并发数量
    - QPS 限制
    - 是否启用 RPC 模式
    - ！！！重要，消费函数的入参名字列表在 auto_generate_info.final_func_input_params_info 中 ，用于发布消息时校验入参是否正确，不正确的消息格式立刻从接口返回报错消息内容不正确。
      前端或跨部门可以先获取所有队列名字以及队列对应的配置，就知道rpc publish发布接口可以传哪些queue_name以及对应的消息应该包含哪些字段。
      auto_generate_info.final_func_input_params_info ，相当于是funboost能自动根据消费函数的def定义，对外提供消费函数的接口文档字段，就类似fastapi自动对接口函数入参生成了文档，避免需要重复手动一个个的编辑接口文档字段。
    - 等等其他 @boost 装饰器的所有参数
    
    主要用于前端可视化展示和管理
    """
    try:
        queues_config = QueuesConusmerParamsGetter().get_queues_params()
        
        return BaseResponse[QueueConfigData](
            succ=True,
            msg="Retrieved successfully",
            data=QueueConfigData(
                queues_config=queues_config,
                count=len(queues_config)
            )
        )
    except Exception as e:
        logger.exception(f'获取队列配置失败: {str(e)}')
        return BaseResponse[QueueConfigData](
            succ=False,
            msg=f"获取队列配置失败: {str(e)}",
            data=QueueConfigData(
                queues_config={},
                count=0
            )
        )


@fastapi_router.get("/get_one_queue_config", response_model=BaseResponse[QueueParams])
@handle_funboost_exceptions
def get_one_queue_config(queue_name: str):
    """
    获取单个队列的配置信息
    
    参数:
        queue_name: 队列名称（必填）
    
    返回:
        队列的配置信息，包括函数入参信息 (auto_generate_info.final_func_input_params_info)
    """
    queue_params = SingleQueueConusmerParamsGetter(queue_name).get_one_queue_params()
    
    return BaseResponse[QueueParams](
        succ=True,
        msg="Retrieved successfully",
        data=queue_params
    )
@fastapi_router.get("/get_queue_run_info", response_model=BaseResponse[QueueParamsAndActiveConsumersData])
def get_queue_run_info(queue_name: str):
    """
    获取单个队列的运行信息
    
    参数:
        queue_name: 队列名称（必填）
    
    返回:
        队列的详细运行信息，包括：
        - queue_params: 队列配置参数
        - active_consumers: 活跃的消费者列表
        - pause_flag: 暂停标志（-1,0表示未暂停，1表示已暂停）
        - msg_num_in_broker: broker中的消息数量（实时）
        - history_run_count: 历史运行总次数
        - history_run_fail_count: 历史失败总次数
        - all_consumers_last_x_s_execute_count: 所有消费进程，最近X秒所有消费者的执行次数
        - all_consumers_last_x_s_execute_count_fail: 所有消费进程，最近X秒所有消费者的失败次数
        - all_consumers_last_x_s_avarage_function_spend_time: 所有消费进程，最近X秒的平均函数耗时
        - all_consumers_avarage_function_spend_time_from_start: 所有消费进程，从启动开始的平均函数耗时
        - all_consumers_total_consume_count_from_start: 所有消费进程，从启动开始的总消费次数
        - all_consumers_total_consume_count_from_start_fail: 所有消费进程，从启动开始的总失败次数
        - all_consumers_last_execute_task_time: 所有消费进程中，最后一次执行任务的时间戳
    """
    try:
        # 获取单个队列的运行信息
        queue_info = SingleQueueConusmerParamsGetter(queue_name).get_one_queue_params_and_active_consumers()
        
        return BaseResponse[QueueParamsAndActiveConsumersData](
            succ=True,
            msg="Retrieved successfully",
            data=QueueParamsAndActiveConsumersData(**queue_info)
        )
        
    except Exception as e:
        logger.exception(f'获取队列运行信息失败: {str(e)}')
        return BaseResponse[QueueParamsAndActiveConsumersData](
            succ=False,
            msg=f"获取队列运行信息失败: {str(e)}",
            data=None
        )


# 所有队列运行信息数据模型
class AllQueuesRunInfoData(BaseModel):
    """所有队列的运行信息"""
    queues: typing.Dict[str, QueueParamsAndActiveConsumersData]  # 队列名到队列运行信息的映射
    total_count: int  # 队列总数


@fastapi_router.get("/get_all_queue_run_info", response_model=BaseResponse[AllQueuesRunInfoData])
def get_all_queue_run_info():
    """
    获取所有队列的运行信息
    
    返回:
        所有队列的详细运行信息，包括每个队列的：
        - queue_params: 队列配置参数
        - active_consumers: 活跃的消费者列表
        - pause_flag: 暂停标志
        - msg_num_in_broker: broker中的消息数量
        - history_run_count: 历史运行总次数
        - history_run_fail_count: 历史失败总次数
        - 以及各种统计信息
    """
    try:
        # 获取所有队列的运行信息
        all_queues_info = QueuesConusmerParamsGetter().get_queues_params_and_active_consumers()
        print(all_queues_info)
        
        # 转换为 Pydantic 模型
        queues_data = {}
        for queue_name, queue_info in all_queues_info.items():
            queues_data[queue_name] = QueueParamsAndActiveConsumersData(**queue_info)
        
        return BaseResponse[AllQueuesRunInfoData](
            succ=True,
            msg="Retrieved successfully",
            data=AllQueuesRunInfoData(
                queues=queues_data,
                total_count=len(queues_data)
            )
        )
        
    except Exception as e:
        logger.exception(f'获取所有队列运行信息失败: {str(e)}')
        return BaseResponse[AllQueuesRunInfoData](
            succ=False,
            msg=f"获取所有队列运行信息失败: {str(e)}",
            data=None
        )

# ==================== 定时任务管理接口 ====================


# 定时任务相关数据模型
class TimingJobRequest(BaseModel):
    """添加定时任务请求"""
    queue_name: str  # 队列名称
    trigger: str  # 触发器类型: 'date', 'interval', 'cron'
    job_id: typing.Optional[str] = None  # 任务ID，如果不提供则自动生成
    job_store_kind: str = 'redis'  # 任务存储方式: 'redis' 或 'memory'
    replace_existing: bool = False  # 是否替换已存在的任务
    
    # 任务参数
    args: typing.Optional[typing.List] = None  # 位置参数
    kwargs: typing.Optional[typing.Dict] = None  # 关键字参数
    
    # date 触发器参数
    run_date: typing.Optional[str] = None  # 运行时间，格式: 'YYYY-MM-DD HH:MM:SS'
    
    # interval 触发器参数
    weeks: typing.Optional[int] = None
    days: typing.Optional[int] = None
    hours: typing.Optional[int] = None
    minutes: typing.Optional[int] = None
    seconds: typing.Optional[int] = None
    
    # cron 触发器参数
    year: typing.Optional[str] = None
    month: typing.Optional[str] = None
    day: typing.Optional[str] = None
    week: typing.Optional[str] = None
    day_of_week: typing.Optional[str] = None
    hour: typing.Optional[str] = None
    minute: typing.Optional[str] = None
    second: typing.Optional[str] = None


class TimingJobData(BaseModel):
    """定时任务数据"""
    job_id: str
    queue_name: typing.Optional[str] = None
    trigger: typing.Optional[str] = None
    next_run_time: typing.Optional[str] = None
    status: typing.Optional[str] = None  # "running" 或 "paused"
    kwargs: typing.Optional[typing.Dict] = None  # 任务的 kwargs 参数


class TimingJobListData(BaseModel):
    """定时任务列表数据"""
    jobs_by_queue: typing.Dict[str, typing.List[TimingJobData]] = {}  # 按队列分组的任务
    total_count: int = 0





@fastapi_router.post("/add_timing_job", response_model=BaseResponse[TimingJobData])
def add_timing_job(job_request: TimingJobRequest):
    """
    添加定时任务
    
    支持三种触发方式:
    1. date: 在指定日期时间执行一次
       - 需要提供: run_date
       - 示例: {"trigger": "date", "run_date": "2025-12-03 15:00:00"}
    
    2. interval: 按固定时间间隔执行
       - 需要提供: weeks, days, hours, minutes, seconds 中的至少一个
       - 示例: {"trigger": "interval", "seconds": 10}
    
    3. cron: 按cron表达式执行
       - 需要提供: year, month, day, week, day_of_week, hour, minute, second 中的至少一个
       - 示例: {"trigger": "cron", "hour": "*/2", "minute": "30"}
    """
    try:
        # 获取 job_adder
        job_adder = gen_aps_job_adder(job_request.queue_name, job_request.job_store_kind)

        # 构建触发器参数
        trigger_args = {}
        
        if job_request.trigger == 'date':
            if job_request.run_date:
                trigger_args['run_date'] = job_request.run_date
        
        elif job_request.trigger == 'interval':
            if job_request.weeks is not None:
                trigger_args['weeks'] = job_request.weeks
            if job_request.days is not None:
                trigger_args['days'] = job_request.days
            if job_request.hours is not None:
                trigger_args['hours'] = job_request.hours
            if job_request.minutes is not None:
                trigger_args['minutes'] = job_request.minutes
            if job_request.seconds is not None:
                trigger_args['seconds'] = job_request.seconds
        
        elif job_request.trigger == 'cron':
            if job_request.year is not None:
                trigger_args['year'] = job_request.year
            if job_request.month is not None:
                trigger_args['month'] = job_request.month
            if job_request.day is not None:
                trigger_args['day'] = job_request.day
            if job_request.week is not None:
                trigger_args['week'] = job_request.week
            if job_request.day_of_week is not None:
                trigger_args['day_of_week'] = job_request.day_of_week
            if job_request.hour is not None:
                trigger_args['hour'] = job_request.hour
            if job_request.minute is not None:
                trigger_args['minute'] = job_request.minute
            if job_request.second is not None:
                trigger_args['second'] = job_request.second
        
        # 添加任务
        job = job_adder.add_push_job(
            trigger=job_request.trigger,
            args=job_request.args,
            kwargs=job_request.kwargs,
            id=job_request.job_id,
            replace_existing=job_request.replace_existing,
            **trigger_args
        )

        return BaseResponse[TimingJobData](
            succ=True,
            msg="定时任务添加成功",
            data=TimingJobData(
                job_id=job.id,
                queue_name=job_request.queue_name,
                trigger=str(job.trigger),
                next_run_time=str(job.next_run_time) if job.next_run_time else None,
                status="running",
                kwargs=job_request.kwargs
            )
        )
        
    except Exception as e:
        logger.exception(f'添加定时任务失败: {str(e)}')
        return BaseResponse[TimingJobData](
            succ=False,
            msg=f"添加定时任务失败: {str(e)}\n{traceback.format_exc()}",
            data=None
        )


@fastapi_router.get("/get_timing_jobs", response_model=BaseResponse[TimingJobListData])
def get_timing_jobs(
    queue_name: typing.Optional[str] = None,
    job_store_kind: str = 'redis'
):
    """
    获取定时任务列表
    
    参数:
        queue_name: 队列名称（可选，如果不提供则获取所有队列的任务）
        job_store_kind: 任务存储方式，'redis' 或 'memory'
    
    返回格式:
        jobs_by_queue: {queue_name: [jobs]}，按队列分组的任务
        total_count: 总任务数
    """
    try:
        # 使用字典格式存储：{queue_name: [jobs]}
        jobs_by_queue: typing.Dict[str, typing.List[TimingJobData]] = {}
        total_count = 0
        
        if queue_name:
            # 获取指定队列的任务
            jobs_by_queue[queue_name] = []
            try:
                job_adder = gen_aps_job_adder(queue_name, job_store_kind)
                jobs = job_adder.aps_obj.get_jobs()
                
                for job in jobs:
                    status = "paused" if job.next_run_time is None else "running"
                    kwargs = job.kwargs if hasattr(job, 'kwargs') and job.kwargs else {}
                    jobs_by_queue[queue_name].append(TimingJobData(
                        job_id=job.id,
                        queue_name=queue_name,
                        trigger=str(job.trigger),
                        next_run_time=str(job.next_run_time) if job.next_run_time else None,
                        status=status,
                        kwargs=kwargs
                    ))
                    total_count += 1
            except Exception as e:
                logger.exception(f'获取定时任务列表失败: {str(e)}')
                pass  # 队列不存在或没有任务，保持空数组
        else:
            # 获取所有队列的任务
            all_queues = list(QueuesConusmerParamsGetter().get_all_queue_names())
            for q_name in all_queues:
                jobs_by_queue[q_name] = []  # 初始化为空数组
                try:
                    job_adder = gen_aps_job_adder(q_name, job_store_kind)
                    jobs = job_adder.aps_obj.get_jobs()
                    
                    for job in jobs:
                        status = "paused" if job.next_run_time is None else "running"
                        kwargs = job.kwargs if hasattr(job, 'kwargs') and job.kwargs else {}
                        jobs_by_queue[q_name].append(TimingJobData(
                            job_id=job.id,
                            queue_name=q_name,
                            trigger=str(job.trigger),
                            next_run_time=str(job.next_run_time) if job.next_run_time else None,
                            status=status,
                            kwargs=kwargs
                        ))
                        total_count += 1
                except Exception as e:
                    logger.exception(f'获取定时任务列表失败: {str(e)}')
                    pass  # 队列没有任务或出错，保持空数组
        
        return BaseResponse[TimingJobListData](
            succ=True,
            msg="Retrieved successfully",
            data=TimingJobListData(
                jobs_by_queue=jobs_by_queue,
                total_count=total_count
            )
        )
        
    except Exception as e:
        logger.exception(f'获取定时任务列表失败: {str(e)}')
        return BaseResponse[TimingJobListData](
            succ=False,
            msg=f"获取定时任务列表失败: {str(e)}",
            data=TimingJobListData(jobs_by_queue={}, total_count=0)
        )


@fastapi_router.get("/get_timing_job", response_model=BaseResponse[TimingJobData])
def get_timing_job(
    job_id: str,
    queue_name: str,
    job_store_kind: str = 'redis'
):
    """
    获取单个定时任务的详细信息
    
    参数:
        job_id: 任务ID（必填）
        queue_name: 队列名称（必填）
        job_store_kind: 任务存储方式，'redis' 或 'memory'
    
    返回:
        任务的详细信息，包括任务ID、队列名、触发器类型、下次运行时间等
    """
    try:
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        
        # 获取指定的任务
        job = job_adder.aps_obj.get_job(job_id)
        
        if job:
            status = "paused" if job.next_run_time is None else "running"
            kwargs = job.kwargs if hasattr(job, 'kwargs') and job.kwargs else {}
            return BaseResponse[TimingJobData](
                succ=True,
                msg="Retrieved successfully",
                data=TimingJobData(
                    job_id=job.id,
                    queue_name=queue_name,
                    trigger=str(job.trigger),
                    next_run_time=str(job.next_run_time) if job.next_run_time else None,
                    status=status,
                    kwargs=kwargs
                )
            )
        else:
            return BaseResponse[TimingJobData](
                succ=False,
                msg=f"任务 {job_id} 不存在",
                data=None
            )
        
    except Exception as e:
        logger.exception(f'获取定时任务失败: {str(e)}')
        return BaseResponse[TimingJobData](
            succ=False,
            msg=f"获取定时任务失败: {str(e)}",
            data=None
        )


@fastapi_router.delete("/delete_timing_job", response_model=BaseResponse)
def delete_timing_job(
    job_id: str,
    queue_name: str,
    job_store_kind: str = 'redis'
):
    """
    删除定时任务
    
    参数:
        job_id: 任务ID
        queue_name: 队列名称
        job_store_kind: 任务存储方式，'redis' 或 'memory'
    """
    try:
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.remove_job(job_id)
        
        return BaseResponse(
            succ=True,
            msg=f"定时任务 {job_id} 删除成功",
            data=None
        )
        
    except Exception as e:
        logger.exception(f'删除定时任务失败: {str(e)}')
        return BaseResponse(
            succ=False,
            msg=f"删除定时任务失败: {str(e)}",
            data=None
        )


class DeleteAllJobsData(BaseModel):
    """删除所有任务的结果数据"""
    deleted_count: int = 0
    failed_jobs: typing.List[str] = []


@fastapi_router.delete("/delete_all_timing_jobs", response_model=BaseResponse[DeleteAllJobsData])
def delete_all_timing_jobs(
    queue_name: typing.Optional[str] = None,
    job_store_kind: str = 'redis'
):
    """
    删除所有定时任务
    
    参数:
        queue_name: 队列名称（可选，如果不提供则删除所有队列的所有任务）
        job_store_kind: 任务存储方式，'redis' 或 'memory'
    
    返回:
        deleted_count: 成功删除的任务数量
        failed_jobs: 删除失败的任务ID列表
    """
    try:
        deleted_count = 0
        failed_jobs = []
        
        if queue_name:
            # 删除指定队列的所有任务
            try:

                job_adder = gen_aps_job_adder(queue_name, job_store_kind)
                jobs = job_adder.aps_obj.get_jobs()
                
                for job in jobs:
                    try:
                        job_adder.aps_obj.remove_job(job.id)
                        deleted_count += 1
                    except Exception as e:
                        failed_jobs.append(f"{job.id}: {str(e)}")
            except Exception as e:
                return BaseResponse[DeleteAllJobsData](
                    succ=False,
                    msg=f"删除队列 {queue_name} 的任务失败: {str(e)}",
                    data=DeleteAllJobsData(
                        deleted_count=deleted_count,
                        failed_jobs=failed_jobs
                    )
                )
        else:
            # 删除所有队列的所有任务
            all_queues = list(QueuesConusmerParamsGetter().get_all_queue_names())
            for q_name in all_queues:
                try:

                    job_adder = gen_aps_job_adder(q_name, job_store_kind)
                    jobs = job_adder.aps_obj.get_jobs()
                    
                    for job in jobs:
                        try:
                            job_adder.aps_obj.remove_job(job.id)
                            deleted_count += 1
                        except Exception as e:
                            failed_jobs.append(f"{q_name}/{job.id}: {str(e)}")
                except Exception as e:
                    logger.exception(f'删除队列 {q_name} 的任务失败: {str(e)}')
                    # 队列没有任务或出错，继续处理下一个队列
                    pass
        
        return BaseResponse[DeleteAllJobsData](
            succ=True,
            msg=f"成功删除 {deleted_count} 个定时任务",
            data=DeleteAllJobsData(
                deleted_count=deleted_count,
                failed_jobs=failed_jobs
            )
        )
        
    except Exception as e:
        logger.exception(f'删除所有定时任务失败: {str(e)}')
        return BaseResponse[DeleteAllJobsData](
            succ=False,
            msg=f"删除所有定时任务失败: {str(e)}",
            data=DeleteAllJobsData(
                deleted_count=0,
                failed_jobs=[]
            )
        )


@fastapi_router.post("/pause_timing_job", response_model=BaseResponse)
def pause_timing_job(
    job_id: str,
    queue_name: str,
    job_store_kind: str = 'redis'
):
    """
    暂停定时任务
    
    参数:
        job_id: 任务ID
        queue_name: 队列名称
        job_store_kind: 任务存储方式，'redis' 或 'memory'
    """
    try:
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.pause_job(job_id)
        
        return BaseResponse(
            succ=True,
            msg=f"定时任务 {job_id} 已暂停",
            data=None
        )
        
    except Exception as e:
        logger.exception(f'暂停定时任务失败: {str(e)}')
        return BaseResponse(
            succ=False,
            msg=f"暂停定时任务失败: {str(e)}",
            data=None
        )


@fastapi_router.post("/resume_timing_job", response_model=BaseResponse)
def resume_timing_job(
    job_id: str,
    queue_name: str,
    job_store_kind: str = 'redis'
):
    """
    恢复定时任务
    
    参数:
        job_id: 任务ID
        queue_name: 队列名称
        job_store_kind: 任务存储方式，'redis' 或 'memory'
    """
    try:
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.resume_job(job_id)
        
        return BaseResponse(
            succ=True,
            msg=f"定时任务 {job_id} 已恢复",
            data=None
        )
        
    except Exception as e:
        logger.exception(f'恢复定时任务失败: {str(e)}')
        return BaseResponse(
            succ=False,
            msg=f"恢复定时任务失败: {str(e)}",
            data=None
        )


@fastapi_router.delete("/deprecate_queue", response_model=BaseResponse[DeprecateQueueData])
@handle_funboost_exceptions
async def deprecate_queue(request: DeprecateQueueRequest):
    """
    废弃队列 - 从 Redis 的 funboost_all_queue_names set 中移除队列名
    
    Args:
        request: 包含要废弃的队列名称
        
    Returns:
        BaseResponse[DeprecateQueueData]: 包含废弃结果
        
    使用场景:
        当队列改名或不再使用时，可以调用此接口将其从队列列表中移除
    """
    queue_name = request.queue_name
    
    # 调用 SingleQueueConusmerParamsGetter 的 deprecate_queue 方法
    SingleQueueConusmerParamsGetter(queue_name).deprecate_queue()
    
    logger.info(f'成功废弃队列: {queue_name}')
    return BaseResponse(
        succ=True,
        msg=f"成功废弃队列: {queue_name}",
        data=DeprecateQueueData(
            queue_name=queue_name,
            removed=True
        )
    )


# ==================== Scheduler Control Endpoints ====================

class SchedulerStatusData(BaseModel):
    queue_name: str
    status_code: int
    status_str: str

class SchedulerControlData(BaseModel):
    queue_name: str
    status_str: str

@fastapi_router.get("/get_scheduler_status", response_model=BaseResponse[SchedulerStatusData])
@handle_funboost_exceptions
def get_scheduler_status(
    queue_name: str = Query(..., description="队列名称"),
    job_store_kind: str = Query("redis", description="任务存储方式，'redis' 或 'memory'，默认 'redis'")
):
    """
    获取定时器调度器状态
    """
    
    job_adder = gen_aps_job_adder(queue_name, job_store_kind)
    
    state_map = {0: 'stopped', 1: 'running', 2: 'paused'}
    state = job_adder.aps_obj.state
    
    return BaseResponse(
        succ=True,
        msg="Retrieved successfully",
        data=SchedulerStatusData(
            queue_name=queue_name,
            status_code=state,
            status_str=state_map.get(state, 'unknown')
        )
    )


@fastapi_router.post("/pause_scheduler", response_model=BaseResponse[SchedulerControlData])
@handle_funboost_exceptions
def pause_scheduler(
    queue_name: str = Query(..., description="队列名称"),
    job_store_kind: str = Query("redis", description="任务存储方式，'redis' 或 'memory'，默认 'redis'")
):
    """
    暂停定时器调度器
    注意：这只会暂停当前进程中的调度器实例。如果部署了多实例，可能需要单独控制。
    """
    job_adder = gen_aps_job_adder(queue_name, job_store_kind)
    job_adder.aps_obj.pause()
    
    return BaseResponse(
        succ=True,
        msg=f"调度器已暂停 ({queue_name})",
        data=SchedulerControlData(
            queue_name=queue_name,
            status_str="paused"
        )
    )


@fastapi_router.post("/resume_scheduler", response_model=BaseResponse[SchedulerControlData])
@handle_funboost_exceptions
def resume_scheduler(
    queue_name: str = Query(..., description="队列名称"),
    job_store_kind: str = Query("redis", description="任务存储方式，'redis' 或 'memory'，默认 'redis'")
):
    """
    恢复运行定时器调度器
    """
    job_adder = gen_aps_job_adder(queue_name, job_store_kind)
    job_adder.aps_obj.resume()
    
    return BaseResponse(
        succ=True,
        msg=f"调度器已恢复运行 ({queue_name})",
        data=SchedulerControlData(
            queue_name=queue_name,
            status_str="running"
        )
    )


# ==================== care_project_name 项目筛选接口 ====================

class CareProjectNameData(BaseModel):
    """care_project_name 响应数据"""
    care_project_name: typing.Optional[str] = None


class SetCareProjectNameRequest(BaseModel):
    """设置 care_project_name 请求模型"""
    care_project_name: str = ""  # 空字符串表示不限制


class AllProjectNamesData(BaseModel):
    """所有项目名称响应数据"""
    project_names: typing.List[str] = []
    count: int = 0


@fastapi_router.get("/get_care_project_name", response_model=BaseResponse[CareProjectNameData])
@handle_funboost_exceptions
def get_care_project_name():
    """
    获取当前的 care_project_name 设置
    
    返回:
        care_project_name: 当前设置的项目名称，None 表示不限制（显示全部）
    """
    care_project_name = CareProjectNameEnv.get()
    
    return BaseResponse(
        succ=True,
        msg="Retrieved successfully",
        data=CareProjectNameData(
            care_project_name=care_project_name
        )
    )


@fastapi_router.post("/set_care_project_name", response_model=BaseResponse[CareProjectNameData])
@handle_funboost_exceptions
def set_care_project_name(request: SetCareProjectNameRequest):
    """
    设置 care_project_name
    
    请求体:
        care_project_name: 项目名称，空字符串表示不限制（显示全部项目）
    
    说明:
        设置后会影响本次会话的所有页面（队列操作、消费者信息等）
    """
    care_project_name = request.care_project_name
    
    # 空字符串表示清除限制
    CareProjectNameEnv.set(care_project_name)
    
    # 如果设置为空字符串，返回时显示为 None
    display_value = care_project_name if care_project_name else None
    
    logger.info(f'设置 care_project_name 为: {display_value}')
    return BaseResponse(
        succ=True,
        msg=f"设置成功: {display_value if display_value else '不限制（显示全部）'}",
        data=CareProjectNameData(
            care_project_name=display_value
        )
    )


@fastapi_router.get("/get_all_project_names", response_model=BaseResponse[AllProjectNamesData])
@handle_funboost_exceptions
def get_all_project_names():
    """
    获取所有已注册的项目名称列表
    
    返回:
        project_names: 项目名称列表（按字母排序）
        count: 项目数量
    """
    # 使用 QueuesConusmerParamsGetter 获取所有项目名称
    project_names = QueuesConusmerParamsGetter().get_all_project_names()
    
    return BaseResponse(
        succ=True,
        msg="Retrieved successfully",
        data=AllProjectNamesData(
            project_names=sorted(project_names) if project_names else [],
            count=len(project_names) if project_names else 0
        )
    )


# 运行应用 (仅在作为主脚本运行时创建 app)
if __name__ == "__main__":
    import uvicorn

    CareProjectNameEnv.set('test_project1')

    # 这是一个示例，展示用户如何将 funboost router 集成到自己的 app 中
    app = FastAPI()
    app.include_router(fastapi_router)
    # 注意：funboost router 的异常处理使用装饰器 @handle_funboost_exceptions，无需全局注册


    print("启动 Funboost API 服务...")
    print("接口文档: http://127.0.0.1:16666/docs")
    uvicorn.run(app, host="0.0.0.0", port=16666, )
