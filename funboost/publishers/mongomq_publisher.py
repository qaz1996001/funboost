# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:23
import os

import json
from funboost.constant import MongoDbName
from funboost.utils.dependency_packages.mongomq import MongoQueue
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.utils import time_util
from funboost.utils.mongo_util import MongoMixin


class MongoMqPublisher(AbstractPublisher, MongoMixin):
    # MongoDB-based queue implemented using the mongo-queue package. Each queue is a collection, automatically stored in the consume_queues database.
    # noinspection PyAttributeOutsideInit

    pid__queue_map = {}

    def custom_init(self):
        pass

    @property
    def queue(self):
        '''Cannot instantiate in advance; mongo is not fork-safe, so the queue is dynamically generated.'''
        pid = os.getpid()
        key = (pid, MongoDbName.MONGOMQ_DB, self._queue_name)
        if key not in MongoMqPublisher.pid__queue_map:
            queuex = MongoQueue(
                self.get_mongo_collection(MongoDbName.MONGOMQ_DB, self._queue_name),
                consumer_id=f"consumer-{time_util.DatetimeConverter().datetime_str}",
                timeout=600,
                max_attempts=3,
                ttl=24 * 3600 * 365)
            MongoMqPublisher.pid__queue_map[key] = queuex
        return MongoMqPublisher.pid__queue_map[key]


    def _publish_impl(self, msg):
        # noinspection PyTypeChecker
        self.queue.put(json.loads(msg))

    def clear(self):
        self.queue.clear()
        self.logger.warning(f'Successfully cleared messages in mongo queue {self._queue_name}')

    def get_message_count(self):
        # return self.queue.size()
        return self.queue.collection.count_documents({'status': 'queued'})

    def close(self):
        pass
