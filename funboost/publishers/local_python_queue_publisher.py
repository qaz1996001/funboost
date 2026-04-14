# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:07
from collections import deque
from concurrent.futures import Future
from queue import Queue, SimpleQueue
import asyncio

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.queues.memory_queues_map import PythonQueues

local_pyhton_queue_name__local_pyhton_queue_obj_map = dict()  # Use the same pattern as other brokers, using a mapping to save queue names so consumers and publishers can find queue objects by name.


class LocalPythonQueuePublisher(AbstractPublisher):
    """
    Uses Python's built-in queue object as the broker.
    Memory queues are very important: high performance, no worries about objects that can't be pickle-serialized.
    Can use get_future and get_aio_future methods to get results via RPC without relying on Redis.
    """

    # noinspection PyAttributeOutsideInit

    @property
    def local_python_queue(self) -> Queue:
        maxsize = self.publisher_params.broker_exclusive_config['maxsize']
        return PythonQueues.get_queue(self._queue_name, maxsize=maxsize)

    def _publish_impl(self, msg):
        # noinspection PyTypeChecker
        pass
        self.local_python_queue.put(msg)

   
    def clear(self):
        # noinspection PyUnresolvedReferences
        self.local_python_queue.queue.clear()
        self.logger.warning(f'Successfully cleared messages in local queue')

    def get_message_count(self):
        return self.local_python_queue.qsize()

    def close(self):
        pass


    # Memory queue exclusive method, get results directly via future.result(), without relying on Redis for RPC
    def get_future(self, *func_args, **func_kwargs) -> Future:
        """
        Memory queue exclusive method. Publishes a message and returns a concurrent.futures.Future object, without relying on Redis as RPC.

        Takes advantage of memory queues not serializing, directly putting the Future object into the message body's extra field to flow with the message.
        After the consumer executes the function, it sets the FunctionResultStatus back via future.set_result().
        Completely zero external dependencies, pure in-process communication.

        Usage:
            future = task_fun.publisher.get_future(1, y=2)
            function_result_status = future.result(timeout=10)   # Block and wait for result
            print(function_result_status.result)    # Get function return value
            print(function_result_status.success)   # Whether successful
        """
        future = Future()
        # Build msg_dict
        msg_dict = dict(func_kwargs)
        for index, arg in enumerate(func_args):
            msg_dict[self.publish_params_checker.all_arg_name_list[index]] = arg
        # Put Future object directly into message's extra field; memory queue doesn't serialize, so Future objects can be passed directly
        msg_dict['extra'] = {'_memory_call_future': future}
        self.publish(msg_dict)
        return future
    
    # Memory queue exclusive method, get results directly via await future, without relying on Redis for RPC
    def get_aio_future(self, *func_args, **func_kwargs) -> asyncio.Future:
        """
        Memory queue exclusive method. Publishes a message and returns an asyncio.Future object, without relying on Redis as RPC.

        Note: This method itself is synchronous; the return value is asyncio.Future, which needs to be awaited in an async context.
        Internally calls get_future() to get a concurrent.futures.Future,
        then bridges it to asyncio.Future via asyncio.wrap_future().

        Usage (in async context):
            # Get the future first, await later (recommended, allows concurrent tasks)
            future = task_fun.publisher.get_aio_future(1, y=2)
            # ... do other things ...
            result_status = await future
            print(result_status.result)    # Get function return value
            print(result_status.success)   # Whether successful
        """
        sync_future = self.get_future(*func_args, **func_kwargs)
        loop = asyncio.get_running_loop()
        return asyncio.wrap_future(sync_future, loop=loop)



