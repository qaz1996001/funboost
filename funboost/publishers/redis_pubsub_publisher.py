# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.utils.redis_manager import RedisMixin


class RedisPubSubPublisher(AbstractPublisher, RedisMixin, ):
    """
    Uses redis pub/sub as the broker.
    """

    def _publish_impl(self, msg):
        self.redis_db_frame.publish(self._queue_name, msg)

    def clear(self):
        self.redis_db_frame.delete(self._queue_name)
        self.logger.warning(f'Successfully cleared messages in queue {self._queue_name}')

    def get_message_count(self):
        return -1

    def close(self):
        pass
