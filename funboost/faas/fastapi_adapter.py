
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
            msg=f"Queue {request.queue_name} paused successfully",
            data=QueueControlData(
                queue_name=request.queue_name,
                success=True
            )
        )
    except Exception as e:
        logger.exception(f'Failed to pause queue consumption: {str(e)}')
        return BaseResponse[QueueControlData](
            succ=False,
            msg=f"Failed to pause queue {request.queue_name}: {str(e)}",
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
            msg=f"Queue {request.queue_name} resumed successfully",
            data=QueueControlData(
                queue_name=request.queue_name,
                success=True
            )
        )
    except Exception as e:
        logger.exception(f'Failed to resume queue consumption: {str(e)}')
        return BaseResponse[QueueControlData](
            succ=False,
            msg=f"Failed to resume queue {request.queue_name}: {str(e)}",
            data=QueueControlData(
                queue_name=request.queue_name,
                success=False
            )
        )



@fastapi_router.get("/get_msg_count", response_model=BaseResponse[CountData])
@handle_funboost_exceptions  # Use decorator for unified exception handling, does not affect the user's app
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

    

# Active consumer detailed model
class ActiveConsumerRunInfo(BaseAllowExtraModel):
    """
    Detailed information for a single active consumer.
    This data is obtained from the heartbeat information stored in Redis.
    """
    # Basic info
    queue_name: str  # Queue name
    computer_name: str  # Computer name
    computer_ip: str  # Computer IP address
    process_id: int  # Process ID
    consumer_id: int  # Consumer ID
    consumer_uuid: str  # Consumer UUID

    # Start and heartbeat time
    start_datetime_str: str  # Start time string, format: YYYY-MM-DD HH:MM:SS
    start_timestamp: float  # Start timestamp
    hearbeat_datetime_str: str  # Latest heartbeat time string
    hearbeat_timestamp: float  # Latest heartbeat timestamp

    # Consumer function info
    consuming_function: str  # Consumer function name
    code_filename: str  # Code file path

    # Time unit configuration
    unit_time_for_count: int  # Time unit for statistics (seconds)

    # Recent X seconds execution statistics
    last_x_s_execute_count: int  # Execution count in the last X seconds
    last_x_s_execute_count_fail: int  # Failure count in the last X seconds
    last_execute_task_time: float  # Timestamp of the last task execution
    last_x_s_avarage_function_spend_time: typing.Optional[float]   # Average duration in the last X seconds (seconds)
    last_x_s_total_cost_time: typing.Optional[float]  # Total duration in the last X seconds (seconds)

    # Message queue status
    msg_num_in_broker: int  # Number of messages in the broker
    current_time_for_execute_task_times_every_unit_time: float  # Start timestamp of the current statistics period
    last_timestamp_when_has_task_in_queue: float  # Timestamp of the last time there was a task in the queue

    # Statistics since start
    total_consume_count_from_start: int  # Total execution count since start
    total_consume_count_from_start_fail: int  # Total failure count since start
    total_cost_time_from_start: float  # Total duration since start (seconds)
    avarage_function_spend_time_from_start: typing.Optional[float]  # Average duration since start (seconds)


# Queue run info data model
class QueueParamsAndActiveConsumersData(BaseModel):
    """Queue parameters and active consumers data"""
    queue_params: QueueParams  # Full booster input parameters for the queue
    active_consumers: typing.List[ActiveConsumerRunInfo]   # List of all active consumers for the queue
    pause_flag: int  # Pause flag
    msg_num_in_broker: int   # Number of messages in the broker
    history_run_count: typing.Optional[int]   # Historical run count
    history_run_fail_count: typing.Optional[int]   # Historical failure count
    all_consumers_last_x_s_execute_count: int   # Execution count of all consumers in all consumer processes in the last X seconds
    all_consumers_last_x_s_execute_count_fail: int   # Failure count of all consumers in all consumer processes in the last X seconds
    all_consumers_last_x_s_avarage_function_spend_time: typing.Optional[float]   # Average duration of all consumer processes in the last X seconds
    all_consumers_avarage_function_spend_time_from_start: typing.Optional[float]   # Average duration of all consumer processes since start
    all_consumers_total_consume_count_from_start: int   # Total consumption count of all consumer processes since start
    all_consumers_total_consume_count_from_start_fail: int   # Total failure count of all consumer processes since start
    all_consumers_last_execute_task_time: typing.Optional[float]   # Timestamp of the last task executed across all consumer processes


class QueueConfigData(BaseModel):
    """Queue configuration data"""
    queues_config: typing.Dict[str, QueueParams] = {}
    count: int = 0


@fastapi_router.get("/get_queues_config", response_model=BaseResponse[QueueConfigData])
def get_queues_config():
    """
    Get configuration info for all queues.

    Returns detailed configuration parameters for all registered queues, including:
    - Queue name
    - Broker type
    - Concurrency count
    - QPS limit
    - Whether RPC mode is enabled
    - IMPORTANT: the consumer function's input parameter name list is in auto_generate_info.final_func_input_params_info,
      used to validate input parameters when publishing messages — if the message format is incorrect, the error is returned
      immediately from the endpoint.
      The frontend or cross-department teams can first fetch all queue names and their configs to know which queue_names
      can be passed to the rpc publish endpoint and what fields each corresponding message should contain.
      auto_generate_info.final_func_input_params_info is funboost's way of automatically generating interface documentation
      fields for consumer functions based on their def definitions, similar to how FastAPI auto-generates docs from function
      parameters, avoiding the need to manually edit interface documentation fields one by one.
    - And all other parameters of the @boost decorator

    Mainly used for frontend visualization and management.
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
        logger.exception(f'Failed to get queue config: {str(e)}')
        return BaseResponse[QueueConfigData](
            succ=False,
            msg=f"Failed to get queue config: {str(e)}",
            data=QueueConfigData(
                queues_config={},
                count=0
            )
        )


@fastapi_router.get("/get_one_queue_config", response_model=BaseResponse[QueueParams])
@handle_funboost_exceptions
def get_one_queue_config(queue_name: str):
    """
    Get configuration info for a single queue.

    Parameters:
        queue_name: Queue name (required)

    Returns:
        Queue configuration info, including function input parameter info (auto_generate_info.final_func_input_params_info)
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
    Get run info for a single queue.

    Parameters:
        queue_name: Queue name (required)

    Returns:
        Detailed run info for the queue, including:
        - queue_params: Queue configuration parameters
        - active_consumers: List of active consumers
        - pause_flag: Pause flag (-1 or 0 means not paused, 1 means paused)
        - msg_num_in_broker: Number of messages in the broker (real-time)
        - history_run_count: Total historical run count
        - history_run_fail_count: Total historical failure count
        - all_consumers_last_x_s_execute_count: Execution count of all consumers across all consumer processes in the last X seconds
        - all_consumers_last_x_s_execute_count_fail: Failure count of all consumers across all consumer processes in the last X seconds
        - all_consumers_last_x_s_avarage_function_spend_time: Average function duration across all consumer processes in the last X seconds
        - all_consumers_avarage_function_spend_time_from_start: Average function duration across all consumer processes since start
        - all_consumers_total_consume_count_from_start: Total consumption count across all consumer processes since start
        - all_consumers_total_consume_count_from_start_fail: Total failure count across all consumer processes since start
        - all_consumers_last_execute_task_time: Timestamp of the last task executed across all consumer processes
    """
    try:
        # Get run info for a single queue
        queue_info = SingleQueueConusmerParamsGetter(queue_name).get_one_queue_params_and_active_consumers()

        return BaseResponse[QueueParamsAndActiveConsumersData](
            succ=True,
            msg="Retrieved successfully",
            data=QueueParamsAndActiveConsumersData(**queue_info)
        )

    except Exception as e:
        logger.exception(f'Failed to get queue run info: {str(e)}')
        return BaseResponse[QueueParamsAndActiveConsumersData](
            succ=False,
            msg=f"Failed to get queue run info: {str(e)}",
            data=None
        )


# All queues run info data model
class AllQueuesRunInfoData(BaseModel):
    """Run info for all queues"""
    queues: typing.Dict[str, QueueParamsAndActiveConsumersData]  # Mapping from queue name to queue run info
    total_count: int  # Total number of queues


@fastapi_router.get("/get_all_queue_run_info", response_model=BaseResponse[AllQueuesRunInfoData])
def get_all_queue_run_info():
    """
    Get run info for all queues.

    Returns:
        Detailed run info for all queues, including for each queue:
        - queue_params: Queue configuration parameters
        - active_consumers: List of active consumers
        - pause_flag: Pause flag
        - msg_num_in_broker: Number of messages in the broker
        - history_run_count: Total historical run count
        - history_run_fail_count: Total historical failure count
        - And various other statistics
    """
    try:
        # Get run info for all queues
        all_queues_info = QueuesConusmerParamsGetter().get_queues_params_and_active_consumers()
        print(all_queues_info)

        # Convert to Pydantic models
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
        logger.exception(f'Failed to get all queue run info: {str(e)}')
        return BaseResponse[AllQueuesRunInfoData](
            succ=False,
            msg=f"Failed to get all queue run info: {str(e)}",
            data=None
        )

# ==================== Scheduled Task Management Endpoints ====================


# Scheduled task related data models
class TimingJobRequest(BaseModel):
    """Add scheduled task request"""
    queue_name: str  # Queue name
    trigger: str  # Trigger type: 'date', 'interval', 'cron'
    job_id: typing.Optional[str] = None  # Job ID; auto-generated if not provided
    job_store_kind: str = 'redis'  # Job store type: 'redis' or 'memory'
    replace_existing: bool = False  # Whether to replace an existing job with the same ID

    # Job parameters
    args: typing.Optional[typing.List] = None  # Positional arguments
    kwargs: typing.Optional[typing.Dict] = None  # Keyword arguments

    # date trigger parameters
    run_date: typing.Optional[str] = None  # Run time, format: 'YYYY-MM-DD HH:MM:SS'

    # interval trigger parameters
    weeks: typing.Optional[int] = None
    days: typing.Optional[int] = None
    hours: typing.Optional[int] = None
    minutes: typing.Optional[int] = None
    seconds: typing.Optional[int] = None

    # cron trigger parameters
    year: typing.Optional[str] = None
    month: typing.Optional[str] = None
    day: typing.Optional[str] = None
    week: typing.Optional[str] = None
    day_of_week: typing.Optional[str] = None
    hour: typing.Optional[str] = None
    minute: typing.Optional[str] = None
    second: typing.Optional[str] = None


class TimingJobData(BaseModel):
    """Scheduled task data"""
    job_id: str
    queue_name: typing.Optional[str] = None
    trigger: typing.Optional[str] = None
    next_run_time: typing.Optional[str] = None
    status: typing.Optional[str] = None  # "running" or "paused"
    kwargs: typing.Optional[typing.Dict] = None  # Job kwargs parameters


class TimingJobListData(BaseModel):
    """Scheduled task list data"""
    jobs_by_queue: typing.Dict[str, typing.List[TimingJobData]] = {}  # Tasks grouped by queue
    total_count: int = 0





@fastapi_router.post("/add_timing_job", response_model=BaseResponse[TimingJobData])
def add_timing_job(job_request: TimingJobRequest):
    """
    Add a scheduled task.

    Supports three trigger types:
    1. date: Execute once at a specified date and time
       - Required: run_date
       - Example: {"trigger": "date", "run_date": "2025-12-03 15:00:00"}

    2. interval: Execute at a fixed time interval
       - Required: at least one of weeks, days, hours, minutes, seconds
       - Example: {"trigger": "interval", "seconds": 10}

    3. cron: Execute according to a cron expression
       - Required: at least one of year, month, day, week, day_of_week, hour, minute, second
       - Example: {"trigger": "cron", "hour": "*/2", "minute": "30"}
    """
    try:
        # Get job_adder
        job_adder = gen_aps_job_adder(job_request.queue_name, job_request.job_store_kind)

        # Build trigger arguments
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
        
        # Add the job
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
            msg="Scheduled task added successfully",
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
        logger.exception(f'Failed to add scheduled task: {str(e)}')
        return BaseResponse[TimingJobData](
            succ=False,
            msg=f"Failed to add scheduled task: {str(e)}\n{traceback.format_exc()}",
            data=None
        )


@fastapi_router.get("/get_timing_jobs", response_model=BaseResponse[TimingJobListData])
def get_timing_jobs(
    queue_name: typing.Optional[str] = None,
    job_store_kind: str = 'redis'
):
    """
    Get the list of scheduled tasks.

    Parameters:
        queue_name: Queue name (optional; if not provided, returns tasks for all queues)
        job_store_kind: Job store type, 'redis' or 'memory'

    Return format:
        jobs_by_queue: {queue_name: [jobs]}, tasks grouped by queue
        total_count: Total number of tasks
    """
    try:
        # Store in dict format: {queue_name: [jobs]}
        jobs_by_queue: typing.Dict[str, typing.List[TimingJobData]] = {}
        total_count = 0

        if queue_name:
            # Get tasks for the specified queue
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
                logger.exception(f'Failed to get scheduled task list: {str(e)}')
                pass  # Queue does not exist or has no tasks; keep empty array
        else:
            # Get tasks for all queues
            all_queues = list(QueuesConusmerParamsGetter().get_all_queue_names())
            for q_name in all_queues:
                jobs_by_queue[q_name] = []  # Initialize as empty array
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
                    logger.exception(f'Failed to get scheduled task list: {str(e)}')
                    pass  # Queue has no tasks or error; keep empty array
        
        return BaseResponse[TimingJobListData](
            succ=True,
            msg="Retrieved successfully",
            data=TimingJobListData(
                jobs_by_queue=jobs_by_queue,
                total_count=total_count
            )
        )
        
    except Exception as e:
        logger.exception(f'Failed to get scheduled task list: {str(e)}')
        return BaseResponse[TimingJobListData](
            succ=False,
            msg=f"Failed to get scheduled task list: {str(e)}",
            data=TimingJobListData(jobs_by_queue={}, total_count=0)
        )


@fastapi_router.get("/get_timing_job", response_model=BaseResponse[TimingJobData])
def get_timing_job(
    job_id: str,
    queue_name: str,
    job_store_kind: str = 'redis'
):
    """
    Get detailed information for a single scheduled task.

    Parameters:
        job_id: Job ID (required)
        queue_name: Queue name (required)
        job_store_kind: Job store type, 'redis' or 'memory'

    Returns:
        Detailed info for the task, including job ID, queue name, trigger type, next run time, etc.
    """
    try:
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)

        # Get the specified job
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
                msg=f"Job {job_id} does not exist",
                data=None
            )

    except Exception as e:
        logger.exception(f'Failed to get scheduled task: {str(e)}')
        return BaseResponse[TimingJobData](
            succ=False,
            msg=f"Failed to get scheduled task: {str(e)}",
            data=None
        )


@fastapi_router.delete("/delete_timing_job", response_model=BaseResponse)
def delete_timing_job(
    job_id: str,
    queue_name: str,
    job_store_kind: str = 'redis'
):
    """
    Delete a scheduled task.

    Parameters:
        job_id: Job ID
        queue_name: Queue name
        job_store_kind: Job store type, 'redis' or 'memory'
    """
    try:
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.remove_job(job_id)
        
        return BaseResponse(
            succ=True,
            msg=f"Scheduled task {job_id} deleted successfully",
            data=None
        )

    except Exception as e:
        logger.exception(f'Failed to delete scheduled task: {str(e)}')
        return BaseResponse(
            succ=False,
            msg=f"Failed to delete scheduled task: {str(e)}",
            data=None
        )


class DeleteAllJobsData(BaseModel):
    """Result data for deleting all tasks"""
    deleted_count: int = 0
    failed_jobs: typing.List[str] = []


@fastapi_router.delete("/delete_all_timing_jobs", response_model=BaseResponse[DeleteAllJobsData])
def delete_all_timing_jobs(
    queue_name: typing.Optional[str] = None,
    job_store_kind: str = 'redis'
):
    """
    Delete all scheduled tasks.

    Parameters:
        queue_name: Queue name (optional; if not provided, deletes all tasks for all queues)
        job_store_kind: Job store type, 'redis' or 'memory'

    Returns:
        deleted_count: Number of tasks successfully deleted
        failed_jobs: List of job IDs that failed to delete
    """
    try:
        deleted_count = 0
        failed_jobs = []

        if queue_name:
            # Delete all tasks for the specified queue
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
                    msg=f"Failed to delete tasks for queue {queue_name}: {str(e)}",
                    data=DeleteAllJobsData(
                        deleted_count=deleted_count,
                        failed_jobs=failed_jobs
                    )
                )
        else:
            # Delete all tasks for all queues
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
                    logger.exception(f'Failed to delete tasks for queue {q_name}: {str(e)}')
                    # Queue has no tasks or error; continue to next queue
                    pass

        return BaseResponse[DeleteAllJobsData](
            succ=True,
            msg=f"Successfully deleted {deleted_count} scheduled tasks",
            data=DeleteAllJobsData(
                deleted_count=deleted_count,
                failed_jobs=failed_jobs
            )
        )
        
    except Exception as e:
        logger.exception(f'Failed to delete all scheduled tasks: {str(e)}')
        return BaseResponse[DeleteAllJobsData](
            succ=False,
            msg=f"Failed to delete all scheduled tasks: {str(e)}",
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
    Pause a scheduled task.

    Parameters:
        job_id: Job ID
        queue_name: Queue name
        job_store_kind: Job store type, 'redis' or 'memory'
    """
    try:
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.pause_job(job_id)

        return BaseResponse(
            succ=True,
            msg=f"Scheduled task {job_id} paused",
            data=None
        )

    except Exception as e:
        logger.exception(f'Failed to pause scheduled task: {str(e)}')
        return BaseResponse(
            succ=False,
            msg=f"Failed to pause scheduled task: {str(e)}",
            data=None
        )


@fastapi_router.post("/resume_timing_job", response_model=BaseResponse)
def resume_timing_job(
    job_id: str,
    queue_name: str,
    job_store_kind: str = 'redis'
):
    """
    Resume a scheduled task.

    Parameters:
        job_id: Job ID
        queue_name: Queue name
        job_store_kind: Job store type, 'redis' or 'memory'
    """
    try:
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.resume_job(job_id)

        return BaseResponse(
            succ=True,
            msg=f"Scheduled task {job_id} resumed",
            data=None
        )

    except Exception as e:
        logger.exception(f'Failed to resume scheduled task: {str(e)}')
        return BaseResponse(
            succ=False,
            msg=f"Failed to resume scheduled task: {str(e)}",
            data=None
        )


@fastapi_router.delete("/deprecate_queue", response_model=BaseResponse[DeprecateQueueData])
@handle_funboost_exceptions
async def deprecate_queue(request: DeprecateQueueRequest):
    """
    Deprecate a queue - removes the queue name from the funboost_all_queue_names set in Redis.

    Args:
        request: Contains the queue name to deprecate

    Returns:
        BaseResponse[DeprecateQueueData]: Contains the deprecation result

    Use case:
        When a queue is renamed or no longer in use, call this endpoint to remove it from the queue list.
    """
    queue_name = request.queue_name

    # Call the deprecate_queue method of SingleQueueConusmerParamsGetter
    SingleQueueConusmerParamsGetter(queue_name).deprecate_queue()

    logger.info(f'Successfully deprecated queue: {queue_name}')
    return BaseResponse(
        succ=True,
        msg=f"Successfully deprecated queue: {queue_name}",
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
    queue_name: str = Query(..., description="Queue name"),
    job_store_kind: str = Query("redis", description="Job store type, 'redis' or 'memory', default 'redis'")
):
    """
    Get the scheduler status.
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
    queue_name: str = Query(..., description="Queue name"),
    job_store_kind: str = Query("redis", description="Job store type, 'redis' or 'memory', default 'redis'")
):
    """
    Pause the scheduler.
    Note: This only pauses the scheduler instance in the current process. If multiple instances are deployed, each may need to be controlled separately.
    """
    job_adder = gen_aps_job_adder(queue_name, job_store_kind)
    job_adder.aps_obj.pause()

    return BaseResponse(
        succ=True,
        msg=f"Scheduler paused ({queue_name})",
        data=SchedulerControlData(
            queue_name=queue_name,
            status_str="paused"
        )
    )


@fastapi_router.post("/resume_scheduler", response_model=BaseResponse[SchedulerControlData])
@handle_funboost_exceptions
def resume_scheduler(
    queue_name: str = Query(..., description="Queue name"),
    job_store_kind: str = Query("redis", description="Job store type, 'redis' or 'memory', default 'redis'")
):
    """
    Resume the scheduler.
    """
    job_adder = gen_aps_job_adder(queue_name, job_store_kind)
    job_adder.aps_obj.resume()

    return BaseResponse(
        succ=True,
        msg=f"Scheduler resumed ({queue_name})",
        data=SchedulerControlData(
            queue_name=queue_name,
            status_str="running"
        )
    )


# ==================== care_project_name Project Filter Endpoints ====================

class CareProjectNameData(BaseModel):
    """care_project_name response data"""
    care_project_name: typing.Optional[str] = None


class SetCareProjectNameRequest(BaseModel):
    """Set care_project_name request model"""
    care_project_name: str = ""  # Empty string means no restriction


class AllProjectNamesData(BaseModel):
    """All project names response data"""
    project_names: typing.List[str] = []
    count: int = 0


@fastapi_router.get("/get_care_project_name", response_model=BaseResponse[CareProjectNameData])
@handle_funboost_exceptions
def get_care_project_name():
    """
    Get the current care_project_name setting.

    Returns:
        care_project_name: The currently configured project name; None means no restriction (show all).
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
    Set care_project_name.

    Request body:
        care_project_name: Project name; empty string means no restriction (show all projects).

    Notes:
        After setting, this affects all pages in the current session (queue operations, consumer info, etc.).
    """
    care_project_name = request.care_project_name

    # Empty string means clear the restriction
    CareProjectNameEnv.set(care_project_name)

    # If set to empty string, display as None when returning
    display_value = care_project_name if care_project_name else None

    logger.info(f'Set care_project_name to: {display_value}')
    return BaseResponse(
        succ=True,
        msg=f"Set successfully: {display_value if display_value else 'No restriction (show all)'}",
        data=CareProjectNameData(
            care_project_name=display_value
        )
    )


@fastapi_router.get("/get_all_project_names", response_model=BaseResponse[AllProjectNamesData])
@handle_funboost_exceptions
def get_all_project_names():
    """
    Get the list of all registered project names.

    Returns:
        project_names: List of project names (sorted alphabetically)
        count: Number of projects
    """
    # Use QueuesConusmerParamsGetter to get all project names
    project_names = QueuesConusmerParamsGetter().get_all_project_names()
    
    return BaseResponse(
        succ=True,
        msg="Retrieved successfully",
        data=AllProjectNamesData(
            project_names=sorted(project_names) if project_names else [],
            count=len(project_names) if project_names else 0
        )
    )


# Run the application (only create the app when run as the main script)
if __name__ == "__main__":
    import uvicorn

    CareProjectNameEnv.set('test_project1')

    # This is an example showing how users can integrate the funboost router into their own app
    app = FastAPI()
    app.include_router(fastapi_router)
    # Note: exception handling for the funboost router uses the @handle_funboost_exceptions decorator; no global registration needed


    print("Starting Funboost API service...")
    print("API docs: http://127.0.0.1:16666/docs")
    uvicorn.run(app, host="0.0.0.0", port=16666, )
