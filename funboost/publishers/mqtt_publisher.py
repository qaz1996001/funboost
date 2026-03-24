# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
from funboost.core.lazy_impoter import PahoMqttImporter
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.funboost_config_deafult import BrokerConnConfig

"""
First install the mqtt module:


pip install paho-mqtt
Write a publish client pub.py:

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect('127.0.0.1', 1883, 600) # 600 is the keepalive interval
client.publish('fifa', payload='amazing', qos=0)






Then write a subscriber client sub.py:

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect('127.0.0.1', 1883, 600) # 600 is the keepalive interval
client.subscribe('fifa', qos=0)
client.loop_forever() # keep connection alive

Author: Red Fortress Full
Link: https://www.jianshu.com/p/0ed4e59b1e8f
Source: Jianshu
Copyright belongs to the author. For commercial use, please contact the author for authorization; for non-commercial use, please cite the source.
"""

# import paho.mqtt.client as mqtt


# def on_connect(client, userdata, flags, rc):
#     print("Connected with result code: " + str(rc))
#
#
# def on_message(client, userdata, msg):
#     print(msg.topic + " " + str(msg.payload))


class MqttPublisher(AbstractPublisher, ):
    """
    Uses EMQ as the broker.
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        client = PahoMqttImporter().mqtt.Client()
        # client.username_pw_set('admin', password='public')
        client.on_connect = self._on_connect
        client.on_socket_close = self._on_socket_close
        # client.on_message = on_message
        # print(frame_config.MQTT_HOST)
        client.connect(BrokerConnConfig.MQTT_HOST, BrokerConnConfig.MQTT_TCP_PORT, 600)  # 600 is the keepalive interval
        self._client = client

    def _on_socket_close(self, client, userdata, socket):
        self.logger.critical(f'{client, userdata, socket}')
        self.custom_init()

    def _on_connect(self, client, userdata, flags, rc):
        self.logger.info(f'Successfully connected to MQTT server, {client, userdata, flags, rc}')

    def _publish_impl(self, msg):
        self._client.publish(self._queue_name, payload=msg, qos=0, retain=False)

    def clear(self):
        pass
        self.logger.warning(f'Successfully cleared messages in queue {self._queue_name}')

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass
