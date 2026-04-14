# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:04
import os
import rabbitpy

from funboost.publishers.base_publisher import AbstractPublisher, deco_mq_conn_error
from funboost.utils.rabbitmq_factory import RabbitMqFactory


class RabbitmqPublisherUsingRabbitpy(AbstractPublisher):
    """
    Implemented using the rabbitpy package.
    """

    # noinspection PyAttributeOutsideInit
    def init_broker(self):
        self.logger.warning(f'Connecting to MQ using rabbitpy package')
        self.rabbit_client = RabbitMqFactory(is_use_rabbitpy=1).get_rabbit_cleint()
        self.channel = self.rabbit_client.creat_a_channel()
        self.queue = self.channel.queue_declare(queue=self._queue_name, durable=True)
        self.logger.critical('rabbitpy fast publishing has issues and will lose a large number of tasks. If using rabbitmq, it is recommended to set the broker to BrokerEnum.RABBITMQ_AMQPSTORM')
        os._exit(444) # noqa

    # @decorators.tomorrow_threads(10)
    @deco_mq_conn_error
    def _publish_impl(self, msg):
        # noinspection PyTypeChecker
        import time
        # time.sleep(0.1)
        print(self.channel.basic_publish(
            exchange='',
            routing_key=self._queue_name,
            body=msg,
            properties={'delivery_mode': 2},
        ))


    @deco_mq_conn_error
    def clear(self):
        self.channel.queue_purge(self._queue_name)
        self.logger.warning(f'Successfully cleared messages in queue {self._queue_name}')

    @deco_mq_conn_error
    def get_message_count(self):
        # noinspection PyUnresolvedReferences
        ch_raw_rabbity = self.channel.channel
        return len(rabbitpy.amqp_queue.Queue(ch_raw_rabbity, self._queue_name, durable=True))

    # @deco_mq_conn_error
    def close(self):
        self.channel.close()
        self.rabbit_client.connection.close()
        self.logger.warning('Closing rabbitpy MQ connection')
