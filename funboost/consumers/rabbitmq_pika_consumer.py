# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:27
import os
import functools
import json
from threading import Lock

from deprecated import deprecated
# # from nb_log import LogManager, get_logger
# from funboost.constant import BrokerEnum
# from funboost.publishers.base_publisher import deco_mq_conn_error
from funboost.core.loggers import get_funboost_file_logger
import pikav1.exceptions
from pikav1.exceptions import AMQPError
import pikav1
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.funboost_config_deafult import BrokerConnConfig

get_funboost_file_logger('pikav1', log_level_int=20)

@deprecated('This middleware mode is not recommended. Please use BrokerEnum.RABBITMQ_AMQPSTORM to operate rabbitmq')
class RabbitmqConsumer(AbstractConsumer):
    """
    Implemented using the pika package.
    With pika, using a channel in a child thread for ack causes cross-thread channel operation errors, which is troublesome.
    """


    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._lock_for_pika = Lock()
        self.logger.critical('pika has issues operating the same channel across multiple threads. If using rabbitmq, it is recommended to set middleware to BrokerEnum.RABBITMQ_AMQPSTORM')
        os._exit(444) # noqa

    def _dispatch_task(self):
        # channel = RabbitMqFactory(is_use_rabbitpy=0).get_rabbit_cleint().creat_a_channel()
        # channel.queue_declare(queue=self._queue_name, durable=True)
        # channel.basic_qos(prefetch_count=self.consumer_params.concurrent_num)
        def callback(ch, method, properties, body):
            body = body.decode()
            # self.logger.debug(f'从rabbitmq的 [{self._queue_name}] 队列中 取出的消息是：  {body}')
            kw = {'ch': ch, 'method': method, 'properties': properties, 'body': body}
            self._submit_task(kw)

        while True:
            # 文档例子  https://github.com/pika/pika
            try:
                self.logger.warning(f'Connecting to mq using pika')
                # self.rabbit_client = RabbitMqFactory(is_use_rabbitpy=0).get_rabbit_cleint()
                # self.channel = self.rabbit_client.creat_a_channel()

                credentials = pikav1.PlainCredentials(BrokerConnConfig.RABBITMQ_USER, BrokerConnConfig.RABBITMQ_PASS)
                self.connection = pikav1.BlockingConnection(pikav1.ConnectionParameters(
                    BrokerConnConfig.RABBITMQ_HOST, BrokerConnConfig.RABBITMQ_PORT, BrokerConnConfig.RABBITMQ_VIRTUAL_HOST, credentials, heartbeat=600))
                self.channel = self.connection.channel()
                self.rabbitmq_queue = self.channel.queue_declare(queue=self._queue_name, durable=True)
                self.channel.basic_consume(on_message_callback = callback,
                                           queue=self._queue_name,
                                           # no_ack=True
                                           )
                self.channel.start_consuming()
            # Don't recover if connection was closed by broker
            # except pikav0.exceptions.ConnectionClosedByBroker:
            #     break
            # Don't recover on channel errors
            except pikav1.exceptions.AMQPChannelError as e:
                # break
                self.logger.error(e)
                continue
                # Recover on all other connection errors
            except pikav1.exceptions.AMQPConnectionError as e:
                self.logger.error(e)
                continue

    def _confirm_consume000(self, kw):
        with self._lock_for_pika:
            try:
                kw['ch'].basic_ack(delivery_tag=kw['method'].delivery_tag)  # Confirm consumption
            except AMQPError as e:
                self.logger.error(f'pika confirm consumption failed  {e}')

    def _confirm_consume(self, kw):
        # with self._lock_for_pika:
        #     self.__ack_message_pika(kw['ch'], kw['method'].delivery_tag)
        kw['ch'].connection.add_callback_threadsafe(functools.partial(self.__ack_message_pika, kw['ch'], kw['method'].delivery_tag))

    def _requeue(self, kw):
        kw['ch'].connection.add_callback_threadsafe(functools.partial(self.__nack_message_pika, kw['ch'], kw['method'].delivery_tag))
        # with self._lock_for_pika:
        # return kw['ch'].basic_nack(delivery_tag=kw['method'].delivery_tag)  # 立即重新入队。
        # with self._lock_for_pika:
        #     self.__nack_message_pika(kw['ch'], kw['method'].delivery_tag)

    def __nack_message_pika(self, channelx, delivery_tagx):
        """Note that `channel` must be the same pika channel instance via which
        the message being ACKed was retrieved (AMQP protocol constraint).
        """
        if channelx.is_open:
            channelx.basic_nack(delivery_tagx)
        else:
            # Channel is already closed, so we can't ACK this message;
            # log and/or do something that makes sense for your app in this case.
            self.logger.error(channelx.is_open)
            pass

    def __ack_message_pika(self, channelx, delivery_tagx):
        """Note that `channel` must be the same pika channel instance via which
        the message being ACKed was retrieved (AMQP protocol constraint).
        """
        if channelx.is_open:
            channelx.basic_ack(delivery_tagx)
        else:
            # Channel is already closed, so we can't ACK this message;
            # log and/or do something that makes sense for your app in this case.
            self.logger.error(channelx.is_open)
            pass
