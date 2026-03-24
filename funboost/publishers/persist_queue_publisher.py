# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:05
import json
import sqlite3

import persistqueue
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher
# from funboost.utils import LogManager
from funboost.core.loggers import get_funboost_file_logger

get_funboost_file_logger('persistqueue')


# noinspection PyProtectedMember
class PersistQueuePublisher(AbstractPublisher):
    """
    Local persistent queue implemented using persistqueue.
    This is locally persistent, supporting multiple running Python scripts sharing queue tasks. Unlike LocalPythonQueuePublisher, tasks won't be lost when the Python interpreter exits.
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        # noinspection PyShadowingNames
        def _my_new_db_connection(self, path, multithreading, timeout):  # Mainly changed sqlite file extension for easier recognition and opening in PyCharm.
            # noinspection PyUnusedLocal
            conn = None
            if path == self._MEMORY:
                conn = sqlite3.connect(path,
                                       check_same_thread=not multithreading)
            else:
                conn = sqlite3.connect('{}/data.sqlite'.format(path),
                                       timeout=timeout,
                                       check_same_thread=not multithreading)
            conn.execute('PRAGMA journal_mode=WAL;')
            return conn

        persistqueue.SQLiteAckQueue._new_db_connection = _my_new_db_connection  # Monkey patching.
        # NOTE: Official tests show that SQLite-based local persistence is 3x faster than pure file-based persistence on the same SSD and OS, so SQLite is chosen here.

        self.queue = persistqueue.SQLiteAckQueue(path=BrokerConnConfig.SQLLITE_QUEUES_PATH, name=self._queue_name, auto_commit=True, serializer=json, multithreading=True)

    def _publish_impl(self, msg):
        # noinspection PyTypeChecker
        self.queue.put(msg)

    def clear(self):
        sql = f'{"DELETE"}  {"FROM"} ack_queue_{self._queue_name}'
        self.logger.info(sql)
        self.queue._getter.execute(sql)
        self.queue._getter.commit()
        self.logger.warning(f'Successfully cleared messages in local persistent queue {self._queue_name}')

    def get_message_count(self):
        return self.queue._count()
        # return self.queue.qsize()

    def close(self):
        pass
