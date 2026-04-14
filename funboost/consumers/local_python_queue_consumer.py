# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:36
from queue import Queue
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.queues.memory_queues_map import PythonQueues


class LocalPythonQueueConsumer(AbstractConsumer):
    """
    Uses Python's built-in queue object as message queue. This requires publishing and consuming to run within the same Python interpreter, does not support distributed mode.
    But it is SSS-level important, high performance, no worry about objects that cannot be pickle-serialized.
    """

    @property
    def local_python_queue(self) -> Queue:
        maxsize = self.consumer_params.broker_exclusive_config['maxsize']
        return PythonQueues.get_queue(self._queue_name, maxsize=maxsize)

    def _dispatch_task(self):
        while True:
            task = self.local_python_queue.get()
            kw = {'body': task}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self.local_python_queue.put(kw['body'])

    def _set_rpc_result(self, task_id, kw, current_function_result_status, current_retry_times, **kwargs):
        """
        Override parent's _set_rpc_result, first checking if the message body carries a _memory_call_future (injected by publisher.call method).
        If present, directly set the FunctionResultStatus back via Future.set_result, without relying on Redis.
        If absent, fall back to parent's Redis RPC logic (for is_using_rpc_mode=True scenarios).
        """
        future = kw['body']['extra'].pop('_memory_call_future', None)
        if future is not None:
            future.set_result(current_function_result_status)
            return
        super()._set_rpc_result(task_id, kw, current_function_result_status, current_retry_times, **kwargs)


