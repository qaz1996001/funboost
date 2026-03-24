# coding=utf8
"""
@author:Administrator
@file: bulk_operation.py
@time: 2018/08/27

Simpler batch operations for major databases. Automatically aggregates discrete tasks within a time interval into batch tasks, eliminating the hassle of manual array slicing.
"""
import atexit
import re
import os
# from elasticsearch import helpers
from threading import Thread
from typing import Union
import abc
import time
from queue import Queue, Empty
import unittest
# noinspection PyUnresolvedReferences
from pymongo import UpdateOne, InsertOne, UpdateMany, collection, MongoClient
import redis

from funboost.core.lazy_impoter import ElasticsearchImporter
from funboost.utils.redis_manager import RedisMixin
from funboost.utils.time_util import DatetimeConverter
from funboost.utils import LoggerMixin, decorators


class RedisOperation:
    """Redis operation. This class mainly serves to standardize the format."""

    def __init__(self, operation_name: str, key: str, value: str):
        """
        :param operation_name: Redis operation name, e.g. sadd, lpush, etc.
        :param key: Redis key
        :param value: Redis key's value
        """
        self.operation_name = operation_name
        self.key = key
        self.value = value


class BaseBulkHelper(LoggerMixin, metaclass=abc.ABCMeta):
    """Abstract base class for bulk operations"""
    bulk_helper_map = {}

    def __new__(cls, base_object, *args, **kwargs):
        cls_key = f'{str(base_object)}-{os.getpid()}'
        if cls_key not in cls.bulk_helper_map:  # Using str because some type instances cannot be hashed as dict keys
            self = super().__new__(cls)
            return self
        else:
            return cls.bulk_helper_map[cls_key]

    def __init__(self, base_object: Union[collection.Collection, redis.Redis], threshold: int = 100, max_time_interval=10, is_print_log: bool = True):
        cls_key = f'{str(base_object)}-{os.getpid()}'
        if cls_key not in self.bulk_helper_map:
            self._custom_init(base_object, threshold, max_time_interval, is_print_log)
            self.bulk_helper_map[cls_key] = self

    def _custom_init(self, base_object, threshold, max_time_interval, is_print_log):
        self.base_object = base_object
        self._threshold = threshold
        self._max_time_interval = max_time_interval
        self._is_print_log = is_print_log
        self._to_be_request_queue = Queue(threshold * 2)
        self._current_time = time.time()
        self._last_has_task_time = time.time()
        atexit.register(self.__do_something_before_exit)  # Execute registered function before program exits
        self._main_thread_has_exit = False
        # Thread(target=self.__excute_bulk_operation_in_other_thread).start()
        # Thread(target=self.__check_queue_size).start()
        self.__excute_bulk_operation_in_other_thread()
        self.__check_queue_size()
        self.logger.debug(f'{self.__class__} has been instantiated')

    def add_task(self, base_operation: Union[UpdateOne, InsertOne, RedisOperation, tuple, dict]):
        """Add a single operation to be executed; the program automatically aggregates them into batch operations"""
        self._to_be_request_queue.put(base_operation)
        # self.logger.debug(base_operation)

    # @decorators.tomorrow_threads(100)
    @decorators.keep_circulating(1, block=False, daemon=True)  # Automatically recover from redis or network exceptions.
    def __excute_bulk_operation_in_other_thread(self):
        while True:
            if self._to_be_request_queue.qsize() >= self._threshold or time.time() > self._current_time + self._max_time_interval:
                self._do_bulk_operation()
            if self._main_thread_has_exit and self._to_be_request_queue.qsize() == 0:
                pass
                # break
            time.sleep(10 ** -1)

    @decorators.keep_circulating(60, block=False, daemon=True)
    def __check_queue_size(self):
        if self._to_be_request_queue.qsize() > 0:
            self._last_has_task_time = time.time()
        if time.time() - self._last_has_task_time > 60:
            self.logger.info(f'{self.base_object} last had tasks at: {DatetimeConverter(self._last_has_task_time)}')

    @abc.abstractmethod
    def _do_bulk_operation(self):
        raise NotImplementedError

    def __do_something_before_exit(self):
        self._main_thread_has_exit = True
        self.logger.critical(f'Executing remaining tasks for [{str(self.base_object)}] before program exits')


class MongoBulkWriteHelper(BaseBulkHelper):
    """
    A simpler bulk insert helper. You can submit operations one by one, and they are automatically aggregated into batches before insertion, improving speed by N times.
    """

    def _do_bulk_operation(self):
        if self._to_be_request_queue.qsize() > 0:
            t_start = time.time()
            count = 0
            request_list = []
            for _ in range(0, self._threshold):
                try:
                    request = self._to_be_request_queue.get_nowait()
                    # print(request)
                    count += 1
                    request_list.append(request)
                except Empty:
                    pass
                    break
            if request_list:
                # print(request_list)
                self.base_object.bulk_write(request_list, ordered=False)
            if self._is_print_log:
                mongo_col_str = re.sub(r"document_class=dict, tz_aware=False, connect=True\),", "", str(self.base_object))
                self.logger.info(f'[{mongo_col_str}]  Bulk insert task count: {count}, time consumed: {round(time.time() - t_start, 6)}')
            self._current_time = time.time()


class ElasticBulkHelper(BaseBulkHelper):
    """
    Elasticsearch bulk insert helper.
    """

    def _do_bulk_operation(self):
        if self._to_be_request_queue.qsize() > 0:
            t_start = time.time()
            count = 0
            request_list = []
            for _ in range(self._threshold):
                try:
                    request = self._to_be_request_queue.get_nowait()
                    count += 1
                    request_list.append(request)
                except Empty:
                    pass
                    break
            if request_list:
                # self.base_object.bulk_write(request_list, ordered=False)
                ElasticsearchImporter().helpers.bulk(self.base_object, request_list)
            if self._is_print_log:
                self.logger.info(f'[{self.base_object}]  Bulk insert task count: {count}, time consumed: {round(time.time() - t_start, 6)}')
            self._current_time = time.time()


class RedisBulkWriteHelper(BaseBulkHelper):
    """Redis bulk insert helper, more convenient than the built-in pipeline for non-evenly-divisible batches"""

    def _do_bulk_operation(self):
        if self._to_be_request_queue.qsize() > 0:
            t_start = time.time()
            count = 0
            pipeline = self.base_object.pipeline()  # type: redis.client.Pipeline
            for _ in range(self._threshold):
                try:
                    request = self._to_be_request_queue.get_nowait()
                    count += 1
                except Empty:
                    break
                    pass
                else:
                    getattr(pipeline, request.operation_name)(request.key, request.value)
            pipeline.execute()
            pipeline.reset()
            if self._is_print_log:
                self.logger.info(f'[{str(self.base_object)}]  Bulk insert task count: {count}, time consumed: {round(time.time() - t_start, 6)}')
            self._current_time = time.time()

    def _do_bulk_operation2(self):
        if self._to_be_request_queue.qsize() > 0:
            t_start = time.time()
            count = 0
            with self.base_object.pipeline() as pipeline:  # type: redis.client.Pipeline
                for _ in range(self._threshold):
                    try:
                        request = self._to_be_request_queue.get_nowait()
                        count += 1
                    except Empty:
                        pass
                    else:
                        getattr(pipeline, request.operation_name)(request.key, request.value)
                pipeline.execute()
            if self._is_print_log:
                self.logger.info(f'[{str(self.base_object)}]  Bulk insert task count: {count}, time consumed: {round(time.time() - t_start, 6)}')
            self._current_time = time.time()


# noinspection SpellCheckingInspection,PyMethodMayBeStatic
class _Test(unittest.TestCase, LoggerMixin):
    # @unittest.skip
    def test_mongo_bulk_write(self):
        # col = MongoMixin().mongo_16_client.get_database('test').get_collection('ydf_test2')
        col = MongoClient('mongodb://myUserAdmin:XXXXXXX@192.168.199.202:27016/admin').get_database('test').get_collection('ydf_test3')
        with decorators.TimerContextManager():
            for i in range(5000 + 13):
                # time.sleep(0.01)
                item = {'_id': i, 'field1': i * 2}
                mongo_helper = MongoBulkWriteHelper(col, 100, is_print_log=True)
                # mongo_helper.add_task(UpdateOne({'_id': item['_id']}, {'$set': item}, upsert=True))
                mongo_helper.add_task(InsertOne({'_id': item['_id']}))

    @unittest.skip
    def test_redis_bulk_write(self):

        with decorators.TimerContextManager():
            # r = redis.Redis(password='123456')
            r = RedisMixin().redis_db0
            redis_helper = RedisBulkWriteHelper(r, 200)
            # redis_helper = RedisBulkWriteHelper(r, 100)  # 放在外面可以
            for i in range(1003):
                # time.sleep(0.2)
                # Can also instantiate infinitely here
                redis_helper.add_task(RedisOperation('sadd', 'key1', str(i)))


if __name__ == '__main__':
    unittest.main()
