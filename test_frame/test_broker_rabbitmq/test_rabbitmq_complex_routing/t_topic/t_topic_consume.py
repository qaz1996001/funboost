# -*- coding: utf-8 -*-
# @Author  : ydf

import time
from funboost import BoosterParams, BrokerEnum, ctrl_c_recv

# Use RABBITMQ_COMPLEX_ROUTING broker that supports complex routing
BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING

# Define exchange name
EXCHANGE_NAME = 'topic_log_exchange'


@BoosterParams(
    queue_name='q_all_logs',  # Queue 1: receives all logs
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'topic',
        'routing_key_for_bind': '#',  # Key: # matches all routing keys, receives all messages
    })
def all_logs_consumer(timestamp: str, content: str):
    """This consumer receives logs of all levels"""
    print(f'[ALL LOGS CONSUMER] {timestamp} received message: {content}')
    time.sleep(0.5)


@BoosterParams(
    queue_name='q_error_logs',  # Queue 2: only receives error logs
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'topic',
        'routing_key_for_bind': '*.error',  # Key: *.error matches all routing keys ending in .error
    })
def error_logs_consumer(timestamp: str, content: str):
    """This consumer only handles error-level logs"""
    print(f'!!!!!!!!!!  [ERROR LOG CONSUMER] {timestamp} received message: {content} !!!!!!!!!!')
    time.sleep(1)


@BoosterParams(
    queue_name='q_system_logs',  # Queue 3: only receives system-related logs
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'topic',
        'routing_key_for_bind': 'system.*',  # Key: system.* matches all routing keys starting with system.
    })
def system_logs_consumer(timestamp: str, content: str):
    """This consumer only handles system-related logs"""
    print(f'[SYSTEM LOG CONSUMER] {timestamp} received message: {content}')
    time.sleep(0.8)


@BoosterParams(
    queue_name='q_app_critical_logs',  # Queue 4: only receives critical application logs
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'topic',
        'routing_key_for_bind': 'app.*.critical',  # Key: app.*.critical matches routing keys in the format app.<any_word>.critical
    })
def app_critical_logs_consumer(timestamp: str, content: str):
    """This consumer only handles critical application logs"""
    print(f'[APP CRITICAL LOG CONSUMER] {timestamp} received message: {content}')
    time.sleep(1.2)


if __name__ == '__main__':
    # Clear previous messages (optional)
    # all_logs_consumer.clear()
    # error_logs_consumer.clear()
    # system_logs_consumer.clear()
    # app_critical_logs_consumer.clear()

    # View message counts (optional)
    # print(f"All logs queue message count: {all_logs_consumer.get_message_count()}")
    # print(f"Error logs queue message count: {error_logs_consumer.get_message_count()}")
    # print(f"System logs queue message count: {system_logs_consumer.get_message_count()}")
    # print(f"App critical logs queue message count: {app_critical_logs_consumer.get_message_count()}")

    # Start consumers
    print("Starting all consumers...")
    all_logs_consumer.consume()
    error_logs_consumer.consume()
    system_logs_consumer.consume()
    app_critical_logs_consumer.consume()

    print("Consumers started, waiting for messages...")
    print("Routing key match rules:")
    print("  - All logs consumer: '#' (matches all)")
    print("  - Error logs consumer: '*.error' (matches any.error)")
    print("  - System logs consumer: 'system.*' (matches system.any)")
    print("  - App critical logs consumer: 'app.*.critical' (matches app.any.critical)")
    print("Press Ctrl+C to stop consuming...")

    # Block the main thread so consumers can keep running
    ctrl_c_recv()
