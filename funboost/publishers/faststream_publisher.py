# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/6 0006 12:12

import abc
import asyncio
import json
import time
import typing

from funboost import TaskOptions
from funboost.concurrent_pool.async_helper import get_or_create_event_loop
from funboost.core.serialization import Serialization
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.assist.faststream_helper import app,get_broker
from faststream import FastStream,Context
from faststream.annotations import Logger

class FastStreamPublisher(AbstractPublisher, metaclass=abc.ABCMeta):
    """
    Empty publisher with empty implementation. Should be used with boost's consumer_override_cls and publisher_override_cls parameters, or be inherited.
    """
    def custom_init(self):
        pass
        # asyncio.get_event_loop().run_until_complete(broker.start())
        self.broker = get_broker()
        get_or_create_event_loop().run_until_complete(self.broker.connect())

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                task_options: TaskOptions = None) :
        msg, msg_function_kw, extra_params, task_id = self._convert_msg(msg, task_id, task_options)
        t_start = time.time()
        faststream_result =  get_or_create_event_loop().run_until_complete(self.broker.publish(Serialization.to_json_str(msg), self.queue_name))
        self.logger.debug(f'Pushed message to queue {self._queue_name}, took {round(time.time() - t_start, 4)} seconds  {msg_function_kw}')  # Full msg is too long to display.
        with self._lock_for_count:
            self.count_per_minute += 1
            self.publish_msg_num_total += 1
            if time.time() - self._current_time > 10:
                self.logger.info(
                    f'Pushed {self.count_per_minute} messages in 10 seconds, total {self.publish_msg_num_total} messages pushed to queue {self._queue_name}')
                self._init_count()
        # return AsyncResult(task_id)
        return faststream_result  #

    def _publish_impl(self, msg):
        pass


    def clear(self):
        pass


    def get_message_count(self):
        return -1


    def close(self):
        pass
