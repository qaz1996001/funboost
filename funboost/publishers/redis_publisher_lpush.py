# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12


from funboost.publishers.redis_publisher import RedisPublisher


class RedisPublisherLpush(RedisPublisher):
    """
    Uses redis as the broker, with lpush method.
    """

    _push_method = 'lpush'


