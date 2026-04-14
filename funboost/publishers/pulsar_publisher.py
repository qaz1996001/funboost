'''

import pulsar

client = pulsar.Client('pulsar://localhost:6650')

producer = client.create_producer('my-topic36')

for i in range(10):
    producer.send(('Hello-%d' % i).encode('utf-8'))

client.close()

'''

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import os

from pulsar.schema import schema

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.funboost_config_deafult import BrokerConnConfig


class PulsarPublisher(AbstractPublisher, ):
    """
    Uses Pulsar as the broker.
    """

    def custom_init(self):
        import pulsar
        self._client = pulsar.Client(BrokerConnConfig.PULSAR_URL, )
        self._producer = self._client.create_producer(self._queue_name, schema=schema.StringSchema(), producer_name=f'funboost_publisher_{os.getpid()}')

    def _publish_impl(self, msg):
        self._producer.send(msg)

    def clear(self):
        """Users can re-consume by changing the subscription_name, no need to clear messages"""
        pass


    def get_message_count(self):
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        self._client.close()
