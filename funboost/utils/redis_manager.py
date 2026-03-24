# coding=utf8

import copy
import os
import threading
# import redis2 as redis
# import redis3
import redis5
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.utils import decorators

# from aioredis.client import Redis as AioRedis



def get_redis_conn_kwargs():
    return {'host': BrokerConnConfig.REDIS_HOST, 'port': BrokerConnConfig.REDIS_PORT,
            'username': BrokerConnConfig.REDIS_USERNAME,'ssl' : BrokerConnConfig.REDIS_SSL,
            'password': BrokerConnConfig.REDIS_PASSWORD, 'db': BrokerConnConfig.REDIS_DB,
            
            # Enhance redis stability, especially for remote/public redis
            'health_check_interval' :30,
            'socket_keepalive' :True,
            # 'socket_timeout':120,  # Do not set socket_timeout, rpc blpop wait can be set to very long durations, which conflicts with this

            }


def _get_redis_conn_kwargs_by_db(db):
    conn_kwargs = copy.copy(get_redis_conn_kwargs())
    conn_kwargs['db'] = db
    return conn_kwargs


class RedisManager(object):
    _redis_db__conn_map = {}
    _lock = threading.Lock()

    def __init__(self, host='127.0.0.1', port=6379, db=0, username='', password='',
                ssl=False,health_check_interval=0,socket_keepalive=None,):
        pid = os.getpid()
        self._key = (host, port, db, username, password,ssl,pid)
        if self._key not in self.__class__._redis_db__conn_map:
            with self.__class__._lock:
                 if self._key not in self.__class__._redis_db__conn_map:
                     self.__class__._redis_db__conn_map[self._key] = redis5.Redis(host=host, port=port, db=db, username=username,
                                                                            password=password, max_connections=100,
                                                                            ssl=ssl,
                                                                            decode_responses=True)
        self.redis = self.__class__._redis_db__conn_map[self._key]

    def get_redis(self) -> redis5.Redis:
        """
        :rtype :redis5.Redis
        """
        return self.redis


# class AioRedisManager(object):
#     _redis_db__conn_map = {}
#
#     def __init__(self, host='127.0.0.1', port=6379, db=0, username='', password=''):
#         self._key = (host, port, db, username, password,)
#         if self._key not in self.__class__._redis_db__conn_map:
#             self.__class__._redis_db__conn_map[self._key] = AioRedis(host=host, port=port, db=db, username=username,
#                                                                      password=password, max_connections=1000, decode_responses=True)
#         self.redis = self.__class__._redis_db__conn_map[self._key]
#
#     def get_redis(self) -> AioRedis:
#         """
#         :rtype :redis5.Redis
#         """
#         return self.redis


# noinspection PyArgumentEqualDefault
class RedisMixin(object):
    """
    Can be used as a universal mixin for inheritance, or instantiated directly.
    """

    def redis_db_n(self, db):
        return RedisManager(**_get_redis_conn_kwargs_by_db(db)).get_redis()

    @property
    @decorators.cached_method_result
    def redis_db_frame(self):
        return RedisManager(**get_redis_conn_kwargs()).get_redis()

    @property
    @decorators.cached_method_result
    def redis_db_filter_and_rpc_result(self):
        return RedisManager(**_get_redis_conn_kwargs_by_db(BrokerConnConfig.REDIS_DB_FILTER_AND_RPC_RESULT)).get_redis()

    def timestamp(self):
        """For distributed rate limiting or consumption acknowledgment across multiple machines, using each machine's own time can cause issues if timestamps are inconsistent. Changed to uniformly use time from the Redis server, in seconds (timestamp)."""
        time_tuple = self.redis_db_frame.time()
        # print(time_tuple)
        return time_tuple[0] + time_tuple[1] / 1000000


class AioRedisMixin(object):
    @property
    @decorators.cached_method_result
    def aioredis_db_filter_and_rpc_result(self):
        # aioredis package is no longer maintained, recommend using asyncio classes from the redis package
        # return AioRedisManager(**_get_redis_conn_kwargs_by_db(BrokerConnConfig.REDIS_DB_FILTER_AND_RPC_RESULT)).get_redis()
        return redis5.asyncio.Redis(**_get_redis_conn_kwargs_by_db(BrokerConnConfig.REDIS_DB_FILTER_AND_RPC_RESULT),decode_responses=True)
