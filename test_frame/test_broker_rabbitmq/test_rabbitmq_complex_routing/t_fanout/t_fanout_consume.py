# -*- coding: utf-8 -*-
# @Author  : ydf

import time
from funboost import BoosterParams, BrokerEnum, ctrl_c_recv

# Use RABBITMQ_COMPLEX_ROUTING broker that supports complex routing
BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING

# Define exchange name
EXCHANGE_NAME = 'fanout_broadcast_exchange'


@BoosterParams(
    queue_name='q_email_service',  # Queue 1: email service
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'fanout',
        # fanout mode does not need to specify routing_key_for_bind; empty string is used automatically
    })
def email_service_consumer(user_id: str, action: str, message: str):
    """Email service consumer - handles all events that need to send email notifications"""
    print(f'[Email Service] User {user_id} performed action {action}, sending email notification: {message}')
    time.sleep(0.5)


@BoosterParams(
    queue_name='q_sms_service',  # Queue 2: SMS service
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'fanout',
        # fanout mode ignores routing keys; all messages are broadcast
    })
def sms_service_consumer(user_id: str, action: str, message: str):
    """SMS service consumer - handles all events that need to send SMS notifications"""
    print(f'[SMS Service] User {user_id} performed action {action}, sending SMS notification: {message}')
    time.sleep(0.8)


@BoosterParams(
    queue_name='q_push_service',  # Queue 3: push notification service
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'fanout',
    })
def push_service_consumer(user_id: str, action: str, message: str):
    """Push notification service consumer - handles all events that need to send push notifications"""
    print(f'[Push Service] User {user_id} performed action {action}, sending push notification: {message}')
    time.sleep(0.3)


@BoosterParams(
    queue_name='q_audit_service',  # Queue 4: audit service
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'fanout',
    })
def audit_service_consumer(user_id: str, action: str, message: str):
    """Audit service consumer - records all user operation logs"""
    print(f'[Audit Service] Recording user {user_id} action {action}: {message}')
    time.sleep(0.2)


@BoosterParams(
    queue_name='q_analytics_service',  # Queue 5: data analytics service
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'fanout',
    })
def analytics_service_consumer(user_id: str, action: str, message: str):
    """Data analytics service consumer - collects user behavior data"""
    print(f'[Data Analytics] Collecting behavior data for user {user_id}: {action} - {message}')
    time.sleep(0.4)


if __name__ == '__main__':
    # Clear previous messages (optional)
    # email_service_consumer.clear()
    # sms_service_consumer.clear()
    # push_service_consumer.clear()
    # audit_service_consumer.clear()
    # analytics_service_consumer.clear()

    # View message counts (optional)
    # print(f"Email service queue message count: {email_service_consumer.get_message_count()}")
    # print(f"SMS service queue message count: {sms_service_consumer.get_message_count()}")
    # print(f"Push service queue message count: {push_service_consumer.get_message_count()}")
    # print(f"Audit service queue message count: {audit_service_consumer.get_message_count()}")
    # print(f"Data analytics queue message count: {analytics_service_consumer.get_message_count()}")

    # Start all consumers
    print("Starting all service consumers...")
    email_service_consumer.consume()
    sms_service_consumer.consume()
    push_service_consumer.consume()
    audit_service_consumer.consume()
    analytics_service_consumer.consume()

    print("All service consumers started, waiting for messages...")
    print("Fanout routing mode characteristics:")
    print("  - Broadcast mode: all queues bound to the exchange receive the same message")
    print("  - Routing key ignored: regardless of the routing key used when publishing, all queues receive the message")
    print("  - Use cases: notification systems, log collection, data synchronization, and scenarios requiring multiple services to process simultaneously")
    print("Press Ctrl+C to stop consuming...")

    # Block the main thread so consumers can keep running
    ctrl_c_recv()
