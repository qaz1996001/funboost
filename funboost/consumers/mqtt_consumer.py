# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
# import time
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.lazy_impoter import PahoMqttImporter
from funboost.funboost_config_deafult import BrokerConnConfig
# import paho.mqtt.client as mqtt


class MqttConsumer(AbstractConsumer):
    """
    Consumer implemented using EMQ as middleware, using shared subscriptions.
    """


    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        # fsdf stands for funboost. Equivalent to kafka's consumer group functionality.
        # This is a shared subscription, see https://blog.csdn.net/emqx_broker/article/details/103027813
        self._topic_shared = f'$share/fsdf/{self._queue_name}'

    # noinspection DuplicatedCode
    def _dispatch_task(self):
        client = PahoMqttImporter().mqtt.Client()
        # client.username_pw_set('admin', password='public')
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_socket_close
        client.on_socket_close = self._on_socket_close
        client.connect(BrokerConnConfig.MQTT_HOST, BrokerConnConfig.MQTT_TCP_PORT, 600)  # 600 is the keepalive interval
        client.subscribe(self._topic_shared, qos=0)  # on_message asynchronously puts messages into thread pool, itself cannot fail.
        client.loop_forever(retry_first_connection=True)  # Maintain connection

    def _on_socket_close(self, client, userdata, socket):
        self.logger.critical(f'{client, userdata, socket}')
        self._dispatch_task()

    # noinspection PyPep8Naming
    def _on_disconnect(self, client, userdata, reasonCode, properties):
        self.logger.critical(f'{client, userdata, reasonCode, properties}')

    def _on_connect(self, client, userdata, flags, rc):
        self.logger.info(f'Successfully connected to mqtt server, {client, userdata, flags, rc}')

    # noinspection PyUnusedLocal
    def _on_message(self, client, userdata, msg):
        # print(msg.topic + " " + str(msg.payload))
        kw = {'body': msg.payload}
        self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        pass
