import asyncio
import threading
import time

import typing
import json

from funboost.constant import MongoDbName, StrConst
from funboost.core.exceptions import FunboostWaitRpcResultTimeout, FunboostRpcResultError, HasNotAsyncResult
from funboost.utils.mongo_util import MongoMixin

from funboost.concurrent_pool import CustomThreadPoolExecutor
from funboost.concurrent_pool.flexible_thread_pool import FlexibleThreadPoolMinWorkers0
from funboost.utils.redis_manager import RedisMixin
from funboost.utils.redis_manager import AioRedisMixin
from funboost.core.serialization import Serialization

from funboost.core.function_result_status_saver import FunctionResultStatus






# LazyAsyncResult has been removed: AsyncResult itself is lazy-loaded.
# RedisMixin's redis_db_filter_and_rpc_result uses @cached_method_result,
# so the Redis connection is only established when accessing properties like status_and_result.


def _judge_rpc_function_result_status_obj(status_and_result_obj:FunctionResultStatus,raise_exception:bool):
    if status_and_result_obj is None:
        raise FunboostWaitRpcResultTimeout(f'wait rpc data timeout for task_id:{status_and_result_obj.task_id}')
    if status_and_result_obj.success is True:
        return status_and_result_obj
    else:
        raw_erorr = status_and_result_obj.exception
        if status_and_result_obj.exception_type == 'FunboostRpcResultError':
            raw_erorr = json.loads(status_and_result_obj.exception_msg) # Make canvas chained error JSON display more readable
        error_msg_dict = {'task_id':status_and_result_obj.task_id,'raw_error':raw_erorr}
        if raise_exception:
            raise FunboostRpcResultError(json.dumps(error_msg_dict,indent=4,ensure_ascii=False))
        else:
            status_and_result_obj.rpc_chain_error_msg_dict = error_msg_dict
            return status_and_result_obj

class AsyncResult(RedisMixin):
    default_callback_run_executor = FlexibleThreadPoolMinWorkers0(200,work_queue_maxsize=50)

    @property
    def callback_run_executor(self, ):
        return self._callback_run_executor or self.default_callback_run_executor
    @callback_run_executor.setter
    def callback_run_executor(self,thread_pool_executor):
        """
        Users can set async_result.callback_run_executor = your own thread pool.
        thread_pool_executor can be FlexibleThreadPool, ThreadPoolExecutorShrinkAble, or the official concurrent.futures.ThreadPoolExecutor; any thread pool that implements the submit method works.
        :param thread_pool_executor:
        :return:
        """
        self._callback_run_executor = thread_pool_executor

    def __init__(self, task_id, timeout=1800):
        self.task_id = task_id
        self.timeout = timeout
        self._has_pop = False
        self._status_and_result = None
        self._callback_run_executor = None

    def set_timeout(self, timeout=1800):
        self.timeout = timeout
        return self

    def is_pending(self):
        return not self.redis_db_filter_and_rpc_result.exists(self.task_id)

    @property
    def status_and_result(self):
        if not self._has_pop:
            # print(f'{self.task_id} waiting for result')
            redis_value = self.redis_db_filter_and_rpc_result.blpop(self.task_id, self.timeout)
            self._has_pop = True
            if redis_value is not None:
                status_and_result_str = redis_value[1]
                self._status_and_result = Serialization.to_dict(status_and_result_str)
                self.redis_db_filter_and_rpc_result.lpush(self.task_id, status_and_result_str)
                self.redis_db_filter_and_rpc_result.expire(self.task_id, self._status_and_result['rpc_result_expire_seconds'])
                return self._status_and_result
            return None
        return self._status_and_result
    
    @property
    def status_and_result_obj(self) -> FunctionResultStatus:
        """This provides better IDE code completion compared to a plain dictionary."""
        if self.status_and_result is not None:
            return FunctionResultStatus.parse_status_and_result_to_obj(self.status_and_result)

    rpc_data =status_and_result_obj

    def get(self):
        # print(self.status_and_result)
        if self.status_and_result is not None:
            return self.status_and_result['result']
        else:
            raise HasNotAsyncResult

    @property
    def result(self):
        return self.get()

    def is_success(self):
        if self.status_and_result is not None:
            return self.status_and_result['success']
        else:
            raise HasNotAsyncResult

    def _run_callback_func(self, callback_func):
        callback_func(self.status_and_result)

    def set_callback(self, callback_func: typing.Callable):
        """
        :param callback_func: Function result callback, makes the callback run concurrently in a thread pool.
        :return:
        """

        ''' Usage example:
        from test_frame.test_rpc.test_consume import add
        def show_result(status_and_result: dict):
            """
            :param status_and_result: A dictionary containing the function input params, result, whether it succeeded, and exception type.
            """
            print(status_and_result)

        for i in range(100):
            async_result = add.push(i, i * 2)
            # print(async_result.result)   # Accessing .result fetches the function's return value, blocking the current thread until the function completes.
            async_result.set_callback(show_result) # Use a callback to run function results concurrently in a thread pool.
        '''
        self.callback_run_executor.submit(self._run_callback_func, callback_func)
    
    def wait_rpc_data_or_raise(self,raise_exception:bool=True)->FunctionResultStatus:
        return _judge_rpc_function_result_status_obj(self.status_and_result_obj,raise_exception)
    
    @classmethod
    def batch_wait_rpc_data_or_raise(cls,r_list:typing.List['AsyncResult'],raise_exception:bool=True)->typing.List[FunctionResultStatus]:
        return [ _judge_rpc_function_result_status_obj(r.status_and_result_obj,raise_exception) 
                for r in r_list]


class AioAsyncResult(AioRedisMixin):
    """ This can be used in asyncio syntax environments."""
    '''
    Usage example:
import asyncio

from funboost import AioAsyncResult
from test_frame.test_rpc.test_consume import add


async def process_result(status_and_result: dict):
    """
    :param status_and_result: A dictionary containing function input params, result, whether it succeeded, and exception type.
    """
    await asyncio.sleep(1)
    print(status_and_result)


async def test_get_result(i):
    async_result = add.push(i, i * 2)
    aio_async_result = AioAsyncResult(task_id=async_result.task_id) # Use the asyncio-compatible class here for better integration with the asyncio ecosystem.
    print(await aio_async_result.result) # Note the await here; without it, a coroutine object is printed instead of the actual result. This is basic asyncio syntax — users need to be familiar with it.
    print(await aio_async_result.status_and_result)
    await aio_async_result.set_callback(process_result)  # You can also schedule tasks into the loop.


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    for j in range(100):
        loop.create_task(test_get_result(j))
    loop.run_forever()

    '''

    def __init__(self, task_id, timeout=1800):
        self.task_id = task_id
        self.timeout = timeout
        self._has_pop = False
        self._status_and_result = None

    def set_timeout(self, timeout=1800):
        self.timeout = timeout
        return self

    async def is_pending(self):
        is_exists = await self.aioredis_db_filter_and_rpc_result.exists(self.task_id)
        return not is_exists

    @property
    async def status_and_result(self):
        if not self._has_pop:
            t1 = time.time()
            redis_value = await self.aioredis_db_filter_and_rpc_result.blpop(self.task_id, self.timeout)
            self._has_pop = True
            if redis_value is not None:
                status_and_result_str = redis_value[1]
                self._status_and_result = Serialization.to_dict(status_and_result_str)
                await self.aioredis_db_filter_and_rpc_result.lpush(self.task_id, status_and_result_str)
                await self.aioredis_db_filter_and_rpc_result.expire(self.task_id, self._status_and_result['rpc_result_expire_seconds'])
                return self._status_and_result
            return None
        return self._status_and_result

    @property
    async def status_and_result_obj(self) -> FunctionResultStatus:
        """This provides better IDE code completion compared to a plain dictionary."""
        sr = await self.status_and_result
        if sr is not None:
            return FunctionResultStatus.parse_status_and_result_to_obj(sr)

    rpc_data =status_and_result_obj
    async def get(self):
        # print(self.status_and_result)
        if (await self.status_and_result) is not None:
            return (await self.status_and_result)['result']
        else:
            raise HasNotAsyncResult

    @property
    async def result(self):
        return await self.get()

    async def is_success(self):
        if (await self.status_and_result) is not None:
            return (await self.status_and_result)['success']
        else:
            raise HasNotAsyncResult

    async def _run_callback_func(self, callback_func):
        await callback_func(await self.status_and_result)

    async def set_callback(self, aio_callback_func: typing.Callable):
        asyncio.create_task(self._run_callback_func(callback_func=aio_callback_func))

    async def wait_rpc_data_or_raise(self,raise_exception:bool=True)->FunctionResultStatus:
        return _judge_rpc_function_result_status_obj(await self.status_and_result_obj,raise_exception)

    @classmethod
    async def batch_wait_rpc_data_or_raise(cls,r_list:typing.List['AioAsyncResult'],raise_exception:bool=True)->typing.List[FunctionResultStatus]:
        return [ _judge_rpc_function_result_status_obj(await r.status_and_result_obj,raise_exception) 
                for r in r_list]
    



class ResultFromMongo(MongoMixin):
    """
    Retrieve the result by task_id from funboost's status/result persistence MongoDB database in a non-blocking manner.

    async_result = add.push(i, i * 2)
    task_id=async_result.task_id
    print(ResultFromMongo(task_id).get_status_and_result())


    print(ResultFromMongo('test_queue77h6_result:764a1ba2-14eb-49e2-9209-ac83fc5db1e8').get_status_and_result())
    print(ResultFromMongo('test_queue77h6_result:5cdb4386-44cc-452f-97f4-9e5d2882a7c1').get_result())
    """

    def __init__(self, task_id: str, mongo_col_name: str):
        self.task_id = task_id
        # self.col_name = task_id.split('_result:')[0]
        self.col_name = mongo_col_name
        self.mongo_row = None
        self._has_query = False

    def query_result(self):
        col = self.get_mongo_collection(MongoDbName.TASK_STATUS_DB, self.col_name)
        self.mongo_row = col.find_one({'_id': self.task_id})
        self._has_query = True

    def get_status_and_result(self):
        self.query_result()
        return self.mongo_row or StrConst.NO_RESULT

    def get_result(self):
        """Retrieve the result by task_id from funboost's status/result persistence MongoDB database in a non-blocking manner."""
        self.query_result()
        return (self.mongo_row or {}).get('result', StrConst.NO_RESULT)


class FutureStatusResult:
    """
    Used for result waiting and notification in sync_call mode.
    Uses threading.Event for synchronous waiting.
    """
    def __init__(self, call_type: str):
        self.execute_finish_event = threading.Event()
        self.staus_result_obj: FunctionResultStatus = None
        self.call_type = call_type  # sync_call or publish

    def set_finish(self):
        """Mark the task as finished."""
        self.execute_finish_event.set()

    def wait_finish(self, rpc_timeout):
        """Wait for the task to finish, with a timeout."""
        return self.execute_finish_event.wait(rpc_timeout)

    def set_staus_result_obj(self, staus_result_obj: FunctionResultStatus):
        """Set the task execution result."""
        self.staus_result_obj = staus_result_obj

    def get_staus_result_obj(self):
        """Get the task execution result."""
        return self.staus_result_obj

if __name__ == '__main__':
    print(ResultFromMongo('764a1ba2-14eb-49e2-9209-ac83fc5db1e8','col1').get_status_and_result())
    print(ResultFromMongo('5cdb4386-44cc-452f-97f4-9e5d2882a7c1','col2').get_result())
