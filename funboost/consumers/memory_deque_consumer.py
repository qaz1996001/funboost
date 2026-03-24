# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:36
import json
from collections import deque

from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers import meomory_deque_publisher


class LocalPythonQueueConsumer(AbstractConsumer):
    """
    Uses Python's built-in deque object as message queue. This requires publishing and consuming to run within the same Python interpreter, does not support distributed mode.
    """

    @property
    def local_python_queue(self) -> deque:
        return meomory_deque_publisher.deque_queue_name__deque_obj_map[self._queue_name]

    def _dispatch_task(self):
        while True:
            task = self.local_python_queue.popleft()
            # self.logger.debug(f'Message fetched from internal Python interpreter queue [{self._queue_name}]:  {json.dumps(task)}  ')
            kw = {'body': task}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self.local_python_queue.append(kw['body'])
