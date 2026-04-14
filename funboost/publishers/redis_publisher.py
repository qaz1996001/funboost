# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import os
import time
# noinspection PyUnresolvedReferences
from queue import Queue, Empty
from threading import Lock

from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.publishers.redis_queue_flush_mixin import FlushRedisQueueMixin
from funboost.utils import decorators
from funboost.utils.redis_manager import RedisMixin


class RedisPublisher(FlushRedisQueueMixin, AbstractPublisher, RedisMixin, ):
    """
    Uses redis as the broker. This is the heavily optimized version for publishing speed.

    This is the complex version with batch pushing; the simple version is in funboost/publishers/redis_publisher_simple.py
    """
    _push_method = 'rpush'

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._temp_msg_queue = Queue()
        self._temp_msg_list = list()
        self._lock_for_bulk_push = Lock()
        self._last_push_time = time.time()
        decorators.keep_circulating(time_sleep=0.1, is_display_detail_exception=True, block=False,
                                    daemon=True)(self._initiative_bulk_push_to_broker, )()

    def __bulk_push_and_init(self):
        if len(self._temp_msg_list) > 0:
            getattr(self.redis_db_frame, self._push_method)(self._queue_name, *self._temp_msg_list)
            self._temp_msg_list = []

    def _initiative_bulk_push_to_broker(self):  # Proactively triggered. Prevents the case where the last message doesn't reach the batch threshold but sleeps for a long time, unable to trigger at_exit.
        with self._lock_for_bulk_push:
            self.__bulk_push_and_init()

    def _publish_impl(self, msg):
        # print(getattr(frame_config,'has_start_a_consumer_flag',0))
        # The has_start_a_consumer_flag is just a flag variable set by the framework at runtime; do not write this variable into the module.
        # if getattr(funboost_config_deafult, 'has_start_a_consumer_flag', 0) == 0:  # Speed up pushing, otherwise only 4000 pushes per second. For standalone script pushing, use batch push; for publishing tasks within consumers, use single push to maintain atomicity.
        if self.publisher_params.broker_exclusive_config.get('redis_bulk_push', 0) == 1:  # RedisConsumer passes this, RedisAckAble does not
            # self._temp_msg_queue.put(msg)
            with self._lock_for_bulk_push:
                self._temp_msg_list.append(msg)
                if len(self._temp_msg_list) >= 1000:
                    # print(len(self._temp_msg_list))
                    self.__bulk_push_and_init()
        else:
            getattr(self.redis_db_frame, self._push_method)(self._queue_name, msg)
            # print(msg)

    def get_message_count(self):
        # print(self.redis_db7,self._queue_name)
        return self.redis_db_frame.llen(self._queue_name)

    def close(self):
        pass

    def _at_exit(self):
        # time.sleep(2) # not needed
        # self._real_bulk_push_to_broker()
        with self._lock_for_bulk_push:
            self.__bulk_push_and_init()
        super()._at_exit()
