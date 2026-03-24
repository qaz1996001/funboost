"""
Django out-of-the-box usage.




Usage instructions:
Django-Ninja out-of-the-box Router
Requirements:
1. pip install django-ninja
2. Django >= 3.1 (supports async)

How to use:
In your Django project's api.py (or urls.py):

from ninja import NinjaAPI

api = NinjaAPI()
api.add_router("/funboost", django_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Mount NinjaAPI
    path("api/", api.urls),
]



"""

# -*- coding: utf-8 -*-
import traceback
import typing
from ninja import Router, Schema
from pydantic import Field
from funboost import AioAsyncResult, TaskOptions
from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter, QueuesConusmerParamsGetter
from funboost.core.loggers import get_funboost_file_logger


logger = get_funboost_file_logger(__name__)


# Create Router instance
django_router = Router(tags=["Funboost Distributed Tasks"])

# --- Schemas (Data Models) ---

class MsgItemSchema(Schema):
    queue_name: str = Field(..., description="Target queue name")
    msg_body: dict = Field(..., description="Task parameter dictionary")
    need_result: bool = Field(False, description="Whether to wait and return result (RPC mode)")
    timeout: int = Field(60, description="Timeout for waiting in RPC mode (seconds)")


# Unified response format data structure
class PublishData(Schema):
    task_id: typing.Optional[str] = None
    status_and_result: typing.Optional[dict] = None


class CountData(Schema):
    queue_name: str
    count: int = -1


class AllQueuesData(Schema):
    queues: typing.List[str] = []
    count: int = 0


# Unified response model
class BaseResponse(Schema):
    succ: bool
    msg: str


class PublishResponse(BaseResponse):
    data: typing.Optional[PublishData] = None


class CountResponse(BaseResponse):
    data: typing.Optional[CountData] = None


class AllQueuesResponse(BaseResponse):
    data: typing.Optional[AllQueuesData] = None


# --- Endpoints ---

@django_router.post("/publish", response=PublishResponse, summary="Publish message")
async def publish_msg(request, payload: MsgItemSchema):
    """
    Publish a message to a Funboost queue.
    If need_result=True, it will suspend and wait for the task to complete and return the result.
    """
    status_and_result = None
    task_id = None
    
    try:
        # Core: dynamically get or create Publisher object through config in redis
        publisher = SingleQueueConusmerParamsGetter(payload.queue_name).gen_publisher_for_faas()
        booster_params_by_redis = SingleQueueConusmerParamsGetter(payload.queue_name).get_one_queue_params_use_cache()

        if payload.need_result:
            # Check if RPC mode is enabled
            if booster_params_by_redis['is_using_rpc_mode'] is False:
                raise ValueError(f'need_result is True, but queue {payload.queue_name} does not have is_using_rpc_mode enabled')
            
            # Async publish message (with RPC config)
            async_result = await publisher.aio_publish(
                payload.msg_body,
                task_options=TaskOptions(is_using_rpc_mode=True)
            )
            task_id = async_result.task_id
            
            # Async wait for result (AioAsyncResult is non-blocking)
            status_and_result = await AioAsyncResult(task_id, timeout=payload.timeout).status_and_result
        else:
            # Normal async publish (Fire and forget)
            async_result = await publisher.aio_publish(payload.msg_body)
            task_id = async_result.task_id

        return {
            "succ": True,
            "msg": f"Message published successfully to queue {payload.queue_name}",
            "data": {
                "task_id": task_id,
                "status_and_result": status_and_result
            }
        }

    except Exception as e:
        # Catch all exceptions, return 200 status code but mark failure in body (could also choose to return 500)
        return {
            "succ": False,
            "msg": f"Publish failed: {str(e)} - {traceback.format_exc()}",
            "data": {
                "task_id": task_id,
                "status_and_result": None
            }
        }


@django_router.get("/get_result", response=PublishResponse, summary="Get task result")
async def get_result(request, task_id: str, timeout: int = 5):
    """
    Actively poll for task execution result by Task ID
    """
    try:
        status_and_result = await AioAsyncResult(task_id, timeout=timeout).status_and_result

        if status_and_result:
            return {
                "succ": True,
                "msg": "Retrieved successfully",
                "data": {
                    "task_id": task_id,
                    "status_and_result": status_and_result
                }
            }
        else:
            return {
                "succ": False,
                "msg": "No result retrieved (possibly running, expired, or timed out)",
                "data": {
                    "task_id": task_id,
                    "status_and_result": None
                }
            }
            
    except Exception as e:
        return {
            "succ": False,
            "msg": f"Error retrieving: {str(e)}",
            "data": {
                "task_id": task_id,
                "status_and_result": None
            }
        }


@django_router.get("/get_msg_count", response=CountResponse, summary="Get queue message count")
def get_msg_count(request, queue_name: str):
    """
    Get the current number of pending messages in the specified queue (synchronous endpoint)
    """
    try:

        publisher = SingleQueueConusmerParamsGetter(queue_name).gen_publisher_for_faas()
        # Getting count is usually fast, no need for async
        count = publisher.get_message_count()
        return {
            "succ": True,
            "msg": "Retrieved successfully",
            "data": {
                "queue_name": queue_name,
                "count": count
            }
        }
    except Exception as e:
        return {
            "succ": False,
            "msg": f"Failed to retrieve: {str(e)}",
            "data": {
                "queue_name": queue_name,
                "count": -1
            }
        }


@django_router.get("/get_all_queues", response=AllQueuesResponse, summary="Get all queue names")
def get_all_queues(request):
    """
    Get all registered queue names

    Returns a list of all queue names registered via the @boost decorator
    """
    try:
        # Get all queue names
        all_queues = QueuesConusmerParamsGetter().get_all_queue_names()
        
        return {
            "succ": True,
            "msg": "Retrieved successfully",
            "data": {
                "queues": all_queues,
                "count": len(all_queues)
            }
        }
    except Exception as e:
        return {
            "succ": False,
            "msg": f"Failed to get all queues: {str(e)}",
            "data": {
                "queues": [],
                "count": 0
            }
        }