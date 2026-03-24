# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/9/17 0017 15:26
import functools
import os
import pymongo
from pymongo.collection import Collection
from funboost.constant import MongoDbName
from funboost.utils import decorators


@functools.lru_cache()
def _get_mongo_url():
    from funboost.funboost_config_deafult import BrokerConnConfig
    return BrokerConnConfig.MONGO_CONNECT_URL




class MongoMixin:
    """
    Mixin class that can be inherited or directly instantiated.

    This is the modified version that no longer errors when using f.multi_process_consume() + Linux + saving results to MongoDB + pymongo.

    On Linux, even with connect=False, if you operate on a collection in the main process, it breaks connect=False,
    and continuing to use that collection global variable in child processes will cause errors.
    Designed with multi-process+fork to always call get_mongo_collection() for maximum safety.
    """
    processid__client_map = {}
    processid__db_map = {}
    processid__col_map = {}

    @property
    def mongo_client(self) -> pymongo.MongoClient:
        pid = os.getpid()
        key = pid
        if key not in MongoMixin.processid__client_map:
            MongoMixin.processid__client_map[key] = pymongo.MongoClient(_get_mongo_url(),
                                                                        connect=False, maxIdleTimeMS=60 * 1000, minPoolSize=3, maxPoolSize=20)
        return MongoMixin.processid__client_map[key]

    @property
    def mongo_db_task_status(self):
        pid = os.getpid()
        key = (pid, MongoDbName.TASK_STATUS_DB)
        if key not in MongoMixin.processid__db_map:
            MongoMixin.processid__db_map[key] = self.mongo_client.get_database(MongoDbName.TASK_STATUS_DB)
        return MongoMixin.processid__db_map[key]

    def get_mongo_collection(self, database_name, colleciton_name) -> pymongo.collection.Collection:
        pid = os.getpid()
        key = (pid, database_name, colleciton_name)
        if key not in MongoMixin.processid__col_map:
            MongoMixin.processid__col_map[key] = self.mongo_client.get_database(database_name).get_collection(colleciton_name)
        return MongoMixin.processid__col_map[key]


if __name__ == '__main__':
    print(MongoMixin().get_mongo_collection('db2', 'col2'))
    print(MongoMixin().get_mongo_collection('db2', 'col3'))
