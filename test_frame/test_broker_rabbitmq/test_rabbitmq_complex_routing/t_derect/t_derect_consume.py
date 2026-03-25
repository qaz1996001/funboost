
# -*- coding: utf-8 -*-
# @Author  : ydf

import time
from funboost import BoosterParams, BrokerEnum, TaskOptions, ctrl_c_recv, BoostersManager, PublisherParams

# Assume RABBITMQ_COMPLEX_ROUTING is your custom amqpstorm broker that supports complex routing.
# If not, replace with funboost's built-in BrokerEnum.RABBITMQ_AMQPSTORM
BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING

# Define exchange name
EXCHANGE_NAME = 'direct_log_exchange'


@BoosterParams(
    queue_name='q_info5',  # Name of queue 1
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'direct',
        'routing_key_for_bind': 'info',  # Key: this queue is only bound to the exchange via the 'info' routing key
    })
def info_fun(msg: str):
    """This consumer only handles info-level logs"""
    print(f'[INFO CONSUMER] Received message: {msg}')
    time.sleep(1)


@BoosterParams(
    queue_name='q_error5',  # Name of queue 2
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'direct',
        'routing_key_for_bind': 'error',  # Key: this queue is only bound to the exchange via the 'error' routing key
    })
def error_fun(msg: str):
    """This consumer only handles error-level logs"""
    print(f'!!!!!!!!!!  [ERROR CONSUMER] Received message: {msg} !!!!!!!!!!')
    time.sleep(1)


if __name__ == '__main__':
    # Clear previous messages
    # info_fun.clear()
    # error_fun.clear()


    # time.sleep(5)
    # print(info_fun.get_message_count())
    # print(error_fun.get_message_count())

    # # Start consuming
    # info_fun.consume()
    # error_fun.consume()

    # Block the main thread so consumers can keep running
    ctrl_c_recv()
