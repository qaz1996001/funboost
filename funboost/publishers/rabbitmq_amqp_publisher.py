# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2026/1/11
"""
High-performance RabbitMQ Publisher implemented using the amqp package.
amqp is the underlying AMQP client used by Celery/Kombu, with better performance than pika.

Install: pip install amqp (usually already installed with celery/kombu)
"""

import amqp
from amqp import Message
from funboost.publishers.base_publisher import AbstractPublisher, deco_mq_conn_error
from funboost.funboost_config_deafult import BrokerConnConfig


class RabbitmqAmqpPublisher(AbstractPublisher):
    """
    Implemented using the amqp package, a high-performance AMQP client.
    amqp is an underlying dependency of Celery/Kombu, with better performance than pika.
    """

    # Type hints for IDE auto-completion
    connection: amqp.Connection
    channel: amqp.Channel

    def custom_init(self):
        self._queue_durable = self.publisher_params.broker_exclusive_config['queue_durable']
        arguments = {}
        if self.publisher_params.broker_exclusive_config['x-max-priority']:
            arguments['x-max-priority'] = self.publisher_params.broker_exclusive_config['x-max-priority']
        self._arguments = arguments if arguments else None

    def init_broker(self):
        self.logger.warning('Connecting to RabbitMQ using amqp package')
        # In the amqp package, empty string represents a vhost with empty name, needs to be converted to '/'
        virtual_host = BrokerConnConfig.RABBITMQ_VIRTUAL_HOST or '/'
        self.connection = amqp.Connection(
            host=f'{BrokerConnConfig.RABBITMQ_HOST}:{BrokerConnConfig.RABBITMQ_PORT}',
            userid=BrokerConnConfig.RABBITMQ_USER,
            password=BrokerConnConfig.RABBITMQ_PASS,
            virtual_host=virtual_host,
            heartbeat=60 * 10,
        )
        self.connection.connect()
        self.channel = self.connection.channel()
        self.channel.queue_declare(
            queue=self._queue_name,
            durable=self._queue_durable,
            auto_delete=False,  # Queue persists permanently, won't be deleted when no consumers exist
            arguments=self._arguments,
        )

    @deco_mq_conn_error
    def _publish_impl(self, msg: str):
        message = Message(
            body=msg,
            delivery_mode=2,  # persistent message
        )
        self.channel.basic_publish(
            msg=message,
            exchange='',
            routing_key=self._queue_name,
        )

    @deco_mq_conn_error
    def clear(self):
        self.channel.queue_purge(self._queue_name)
        self.logger.warning(f'Successfully cleared messages in queue {self._queue_name}')

    @deco_mq_conn_error
    def get_message_count(self):
        # amqp's queue_declare returns (queue_name, message_count, consumer_count)
        # Not using passive=True, so the queue will be auto-created if it doesn't exist instead of raising an error
        try:
            result = self.channel.queue_declare(
                queue=self._queue_name,
                durable=self._queue_durable,
                auto_delete=False,
                arguments=self._arguments,
            )
            if hasattr(result, 'message_count'):
                return result.message_count
            return -1
        except Exception as e:
            self.logger.warning(f'get_message_count failed: {e}')
            return -1

    def close(self):
        self.channel.close()
        self.connection.close()
        self.logger.warning('Closing amqp connection')
