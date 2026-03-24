# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2021/4/3 0008 13:32
from funboost.publishers.base_publisher import AbstractPublisher

from funboost.utils.redis_manager import RedisMixin


class RedisStreamPublisher(AbstractPublisher,RedisMixin):
    """
    Implemented using Redis stream data structure as the broker. Requires Redis 5.0+. Redis stream is Redis's message queue, with far more features than the list structure.
    """

    _has__check_redis_version = False

    def _check_redis_version(self):
        redis_server_info_dict = self.redis_db_frame.info()
        if float(redis_server_info_dict['redis_version'][0]) < 5:
            raise EnvironmentError('Redis server version 5.0+ is required to support the stream data structure. '
                                   'Please upgrade the server, or use REDIS_ACK_ABLE mode with Redis list structure.')
        if self.redis_db_frame.type(self._queue_name) == 'list':
            raise EnvironmentError(f'Detected that key {self._queue_name} already exists and its type is list. '
                                   f'You must use a different queue name or delete this list-type key. '
                                   f'RedisStreamConsumer uses the stream data structure.')
        self._has__check_redis_version = True

    def _publish_impl(self, msg):
        # Redis server must be 5.0+, and ensure the key type is stream, not list data structure.
        if not self._has__check_redis_version:
            self._check_redis_version()
        self.redis_db_frame.xadd(self._queue_name, {"": msg})

    def clear(self):
        self.redis_db_frame.delete(self._queue_name)
        self.logger.warning(f'Successfully cleared messages in queue {self._queue_name}')

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return self.redis_db_frame.xlen(self._queue_name)

    def close(self):
        pass
