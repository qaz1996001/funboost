# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:10
"""
After task consumption is completed, duplicate publications are filtered. Implements both permanent duplicate task filtering and time-limited duplicate task filtering.
Task filtering = function parameter filtering = dictionary filtering = sorted key-value pair JSON string filtering.
"""

import json
import time
from collections import OrderedDict
import typing

from funboost.core.serialization import Serialization
from funboost.utils import  decorators
from funboost.core.loggers import FunboostFileLoggerMixin

from funboost.utils.redis_manager import RedisMixin


class RedisFilter(RedisMixin, FunboostFileLoggerMixin):
    """
    Uses set structure.
    Task filtering based on function parameters. This is permanent filtering unless the key is manually deleted.
    """

    def __init__(self, redis_key_name, redis_filter_task_expire_seconds):
        """
        :param redis_key_name: Task filter key
        :param redis_filter_task_expire_seconds: Task filter expiration time
        """
        self._redis_key_name = redis_key_name
        self._redis_filter_task_expire_seconds = redis_filter_task_expire_seconds

        # @staticmethod
        # def _get_ordered_str(value):
        #     """对json的键值对在redis中进行过滤，需要先把键值对排序，否则过滤会不准确如 {"a":1,"b":2} 和 {"b":2,"a":1}"""
        #     value = Serialization.to_dict(value)
        #     ordered_dict = OrderedDict()
        #     for k in sorted(value):
        #         ordered_dict[k] = value[k]
        #     return json.dumps(ordered_dict)
    
    @staticmethod
    def generate_filter_str(value: typing.Union[str, dict],  filter_str: typing.Optional[str] = None):
        """When filtering JSON key-value pairs in Redis, keys must be sorted first, otherwise filtering will be inaccurate, e.g. {"a":1,"b":2} and {"b":2,"a":1}"""
        if filter_str: # If user specified a filter string, use it; otherwise use the sorted key-value pair string
            return filter_str
        value = Serialization.to_dict(value)
        ordered_dict = OrderedDict()
        for k in sorted(value):
            ordered_dict[k] = value[k]
        # print(ordered_dict,filter_str)
        return json.dumps(ordered_dict)


    def add_a_value(self, value: typing.Union[str, dict], filter_str: typing.Optional[str] = None):
        self.redis_db_filter_and_rpc_result.sadd(self._redis_key_name, self.generate_filter_str(value, filter_str))

    def manual_delete_a_value(self, value: typing.Union[str, dict], filter_str: typing.Optional[str] = None):
        self.redis_db_filter_and_rpc_result.srem(self._redis_key_name, self.generate_filter_str(value, filter_str))

    def check_value_exists(self, value, filter_str: typing.Optional[str] = None):
        return self.redis_db_filter_and_rpc_result.sismember(self._redis_key_name, self.generate_filter_str(value, filter_str))

    def delete_expire_filter_task_cycle(self):
        pass


class RedisImpermanencyFilter(RedisFilter):
    """
    Uses zset structure.
    Task filtering based on function parameters. This is non-permanent filtering, e.g. if the filter expiration time is set to 1800 seconds, a 1 + 2 task published 30 minutes ago will still execute,
    but if this task was published within the last 30 minutes, 1 + 2 will not execute. This logic is now integrated into the framework, commonly used for API caching.
    """

    def add_a_value(self, value: typing.Union[str, dict], filter_str: typing.Optional[str] = None):
        self.redis_db_filter_and_rpc_result.zadd(self._redis_key_name, {self.generate_filter_str(value, filter_str):time.time()})

    def manual_delete_a_value(self, value: typing.Union[str, dict], filter_str: typing.Optional[str] = None):
        self.redis_db_filter_and_rpc_result.zrem(self._redis_key_name, self.generate_filter_str(value, filter_str))

    def check_value_exists(self, value, filter_str: typing.Optional[str] = None):
        # print(self.redis_db_filter_and_rpc_result.zrank(self._redis_key_name, self.generate_filter_str(value, filter_str)))
        is_exists = False if self.redis_db_filter_and_rpc_result.zscore(self._redis_key_name, self.generate_filter_str(value, filter_str)) is None else True
        # print(is_exists,value,filter_str,self.generate_filter_str(value, filter_str))
        return is_exists   

    @decorators.keep_circulating(60, block=False)
    def delete_expire_filter_task_cycle000(self):
        """
        Continuously loops to delete expired filter tasks.
        # REMIND The task filter expiration time should ideally not be less than 60 seconds, otherwise deletion may not be timely, causing newly published tasks to be filtered and not executed. Real-time price API caching of 5 minutes or 30 minutes is generally fine.
        :return:
        """
        time_max = time.time() - self._redis_filter_task_expire_seconds
        for value in self.redis_db_filter_and_rpc_result.zrangebyscore(self._redis_key_name, 0, time_max):
            self.logger.info(f'Deleting filter task {value} from key {self._redis_key_name}')
            self.redis_db_filter_and_rpc_result.zrem(self._redis_key_name, value)

    @decorators.keep_circulating(60, block=False)
    def delete_expire_filter_task_cycle(self):
        """
        Continuously loops to delete expired filter tasks. The task filter expiration time should ideally not be less than 60 seconds, otherwise deletion may not be timely, causing newly published tasks to not trigger execution. Real-time price API caching of 5 minutes or 30 minutes is typical.
        :return:
        """
        time_max = time.time() - self._redis_filter_task_expire_seconds
        delete_num = self.redis_db_filter_and_rpc_result.zremrangebyscore(self._redis_key_name, 0, time_max)
        self.logger.warning(f'Deleted {delete_num} expired filter tasks from key {self._redis_key_name}')
        self.logger.warning(f'Key {self._redis_key_name} has {self.redis_db_filter_and_rpc_result.zcard(self._redis_key_name)} non-expired filter tasks')


class RedisImpermanencyFilterUsingRedisKey(RedisFilter):
    """
    Uses the task directly as a Redis key, leveraging Redis's built-in expiration mechanism to delete expired filter tasks.
    Task filtering based on function parameters. This is non-permanent filtering, e.g. if the filter expiration time is set to 1800 seconds, a 1 + 2 task published 30 minutes ago will still execute,
    but if this task was published within the last 30 minutes, 1 + 2 will not execute. This logic is now integrated into the framework, commonly used for API caching.
    This filtering mode creates too many keys, which looks messy, so it is stored in redis_db_filter_and_rpc_result rather than the message queue's db.
    """

    def __add_dir_prefix(self, value):
        """
        添加一个前缀，以便redis形成一个树形文件夹，方便批量删除和折叠
        :return:
        """
        return f'{self._redis_key_name}:{value.replace(":", "：")}'  # 任务是json，带有：会形成很多树，换成中文冒号。

    def add_a_value(self, value: typing.Union[str, dict], filter_str: typing.Optional[str] = None):
        redis_key = self.__add_dir_prefix(self.generate_filter_str(value, filter_str))
        self.redis_db_filter_and_rpc_result.set(redis_key, 1)
        self.redis_db_filter_and_rpc_result.expire(redis_key, self._redis_filter_task_expire_seconds)

    def manual_delete_a_value(self, value: typing.Union[str, dict], filter_str: typing.Optional[str] = None):
        self.redis_db_filter_and_rpc_result.delete(self.__add_dir_prefix(self.generate_filter_str(value, filter_str)))

    def check_value_exists(self, value, filter_str: typing.Optional[str] = None):
        return True if self.redis_db_filter_and_rpc_result.exists(self.__add_dir_prefix(self.generate_filter_str(value, filter_str))) else True

    def delete_expire_filter_task_cycle(self):
        """
        redis服务端会自动删除过期的过滤任务键。不用在客户端管理。
        :return:
        """
        pass


if __name__ == '__main__':
    # params_filter = RedisFilter('filter_set:abcdefgh2', 120)
    params_filter = RedisImpermanencyFilter('filter_zset:abcdef2', 120)
    # params_filter = RedisImpermanencyFilterUsingRedisKey('filter_dir', 300)
    for i in range(10):
        # params_filter.add_a_value({'x': i, 'y': i * 2},str(i))
        params_filter.add_a_value({'x': i, 'y': i * 2},None)

    # params_filter.manual_delete_a_value({'a': 1, 'b': 2})
    print(params_filter.check_value_exists({'x': 1, 'y': 2}))
    # params_filter.delete_expire_filter_task_cycle()
    # params_filter.add_a_value({'a': 1, 'b': 5})
    # print(params_filter.check_value_exists({'a': 1, 'b': 2}))
    # time.sleep(130)
    # print(params_filter.check_value_exists({'a': 1, 'b': 2}))
