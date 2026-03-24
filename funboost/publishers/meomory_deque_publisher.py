# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:07
from collections import deque

from funboost.publishers.base_publisher import AbstractPublisher

deque_queue_name__deque_obj_map = dict()  # Use the same pattern as other brokers, using a mapping to save queue names so consumers and publishers can find queue objects by name.


class DequePublisher(AbstractPublisher):
    """
    Uses Python's built-in deque object as the broker. Convenient for testing; each broker's consumer class uses duck typing and can be interchangeably substituted via polymorphism.
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        if self._queue_name not in deque_queue_name__deque_obj_map:
            deque_queue_name__deque_obj_map[self._queue_name] = deque()
        self.queue = deque_queue_name__deque_obj_map[self._queue_name]  # type: deque

    def _publish_impl(self, msg):
        # noinspection PyTypeChecker
        self.queue.append(msg)

    def clear(self):
        pass
        # noinspection PyUnresolvedReferences
        self.queue.clear()
        self.logger.warning(f'Successfully cleared messages in local queue')

    def get_message_count(self):
        return len(self.queue)

    def close(self):
        pass
