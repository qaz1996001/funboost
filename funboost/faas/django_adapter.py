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
        # 核心：通过redis中的配置动态获取或创建 Publisher 对象
        publisher = SingleQueueConusmerParamsGetter(payload.queue_name).gen_publisher_for_faas()
        booster_params_by_redis = SingleQueueConusmerParamsGetter(payload.queue_name).get_one_queue_params_use_cache()

        if payload.need_result:
            # 检查是否开启了 RPC 模式
            if booster_params_by_redis['is_using_rpc_mode'] is False:
                raise ValueError(f'need_result为True, 但队列 {payload.queue_name} 未开启 is_using_rpc_mode')
            
            # 异步发布消息 (带 RPC 配置)
            async_result = await publisher.aio_publish(
                payload.msg_body,
                task_options=TaskOptions(is_using_rpc_mode=True)
            )
            task_id = async_result.task_id
            
            # 异步等待结果 (AioAsyncResult 是非阻塞的)
            status_and_result = await AioAsyncResult(task_id, timeout=payload.timeout).status_and_result
        else:
            # 普通异步发布 (Fire and forget)
            async_result = await publisher.aio_publish(payload.msg_body)
            task_id = async_result.task_id

        return {
            "succ": True,
            "msg": f"{payload.queue_name} 队列消息发布成功",
            "data": {
                "task_id": task_id,
                "status_and_result": status_and_result
            }
        }

    except Exception as e:
        # 捕获所有异常，返回 200 状态码但在 body 中标记失败（也可以选择返回 500）
        return {
            "succ": False,
            "msg": f"发布失败: {str(e)} - {traceback.format_exc()}",
            "data": {
                "task_id": task_id,
                "status_and_result": None
            }
        }


@django_router.get("/get_result", response=PublishResponse, summary="获取任务结果")
async def get_result(request, task_id: str, timeout: int = 5):
    """
    根据 Task ID 主动轮询获取任务执行结果
    """
    try:
        status_and_result = await AioAsyncResult(task_id, timeout=timeout).status_and_result

        if status_and_result:
            return {
                "succ": True,
                "msg": "获取成功",
                "data": {
                    "task_id": task_id,
                    "status_and_result": status_and_result
                }
            }
        else:
            return {
                "succ": False,
                "msg": "未获取到结果(可能运行中、已过期或超时)",
                "data": {
                    "task_id": task_id,
                    "status_and_result": None
                }
            }
            
    except Exception as e:
        return {
            "succ": False,
            "msg": f"获取出错: {str(e)}",
            "data": {
                "task_id": task_id,
                "status_and_result": None
            }
        }


@django_router.get("/get_msg_count", response=CountResponse, summary="获取队列堆积数量")
def get_msg_count(request, queue_name: str):
    """
    获取指定队列当前堆积的消息数量 (同步接口)
    """
    try:

        publisher = SingleQueueConusmerParamsGetter(queue_name).gen_publisher_for_faas()
        # 获取数量通常很快，不需要 async
        count = publisher.get_message_count()
        return {
            "succ": True,
            "msg": "获取成功",
            "data": {
                "queue_name": queue_name,
                "count": count
            }
        }
    except Exception as e:
        return {
            "succ": False,
            "msg": f"获取失败: {str(e)}",
            "data": {
                "queue_name": queue_name,
                "count": -1
            }
        }


@django_router.get("/get_all_queues", response=AllQueuesResponse, summary="获取所有队列名称")
def get_all_queues(request):
    """
    获取所有已注册的队列名称
    
    返回所有通过 @boost 装饰器注册的队列名称列表
    """
    try:
        # 获取所有队列名称
        all_queues = QueuesConusmerParamsGetter().get_all_queue_names()
        
        return {
            "succ": True,
            "msg": "获取成功",
            "data": {
                "queues": all_queues,
                "count": len(all_queues)
            }
        }
    except Exception as e:
        return {
            "succ": False,
            "msg": f"获取所有队列失败: {str(e)}",
            "data": {
                "queues": [],
                "count": 0
            }
        }