# -*- coding: utf-8 -*-
# @Author  : ydf

import time
from funboost import BoosterParams, BrokerEnum, ctrl_c_recv

# Use RABBITMQ_COMPLEX_ROUTING broker that supports complex routing
BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING

# Define exchange name
EXCHANGE_NAME = 'headers_notification_exchange'


@BoosterParams(
    queue_name='q_urgent_notifications',  # Queue 1: urgent notifications
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'headers',
        # headers mode binding condition: priority=high AND urgent=true
        'headers_for_bind': {
            'priority': 'high',
            'urgent': 'true'
        },
        'x_match_for_bind': 'all',  # Must match all specified header attributes
    })
def urgent_notifications_consumer(user_id: str, title: str, content: str, timestamp: str):
    """Urgent notification consumer - only handles high-priority and urgent notifications"""
    print(f'[URGENT NOTIFICATION] User {user_id} | {timestamp}')
    print(f'   Title: {title}')
    print(f'   Content: {content}')
    time.sleep(0.3)


@BoosterParams(
    queue_name='q_high_priority_notifications',  # Queue 2: high-priority notifications
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'headers',
        # headers mode binding condition: only requires priority=high
        'headers_for_bind': {
            'priority': 'high'
        },
        'x_match_for_bind': 'all',  # Match all specified header attributes
    })
def high_priority_notifications_consumer(user_id: str, title: str, content: str, timestamp: str):
    """High-priority notification consumer - handles all high-priority notifications"""
    print(f'[HIGH PRIORITY] User {user_id} | {timestamp}')
    print(f'   Title: {title}')
    print(f'   Content: {content}')
    time.sleep(0.5)


@BoosterParams(
    queue_name='q_mobile_notifications',  # Queue 3: mobile notifications
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'headers',
        # headers mode binding condition: platform=mobile OR device_type=phone
        'headers_for_bind': {
            'platform': 'mobile',
            'device_type': 'phone'
        },
        'x_match_for_bind': 'any',  # Match any one of the specified header attributes
    })
def mobile_notifications_consumer(user_id: str, title: str, content: str, timestamp: str):
    """Mobile notification consumer - handles mobile-related notifications"""
    print(f'[MOBILE NOTIFICATION] User {user_id} | {timestamp}')
    print(f'   Title: {title}')
    print(f'   Content: {content}')
    time.sleep(0.4)


@BoosterParams(
    queue_name='q_system_admin_notifications',  # Queue 4: system admin notifications
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'headers',
        # headers mode binding condition: category=system AND role=admin
        'headers_for_bind': {
            'category': 'system',
            'role': 'admin'
        },
        'x_match_for_bind': 'all',  # Must match all specified header attributes
    })
def system_admin_notifications_consumer(user_id: str, title: str, content: str, timestamp: str):
    """System admin notification consumer - only handles system management related notifications"""
    print(f'[SYSTEM ADMIN] User {user_id} | {timestamp}')
    print(f'   Title: {title}')
    print(f'   Content: {content}')
    time.sleep(0.6)


@BoosterParams(
    queue_name='q_marketing_notifications',  # Queue 5: marketing notifications
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'headers',
        # headers mode binding condition: category=marketing OR priority is not high
        'headers_for_bind': {
            'category': 'marketing',
            'priority': 'low'
        },
        'x_match_for_bind': 'any',  # Match any one (demonstrates different matching strategies)
    })
def marketing_notifications_consumer(user_id: str, title: str, content: str, timestamp: str):
    """Marketing notification consumer - handles marketing related notifications"""
    print(f'[MARKETING NOTIFICATION] User {user_id} | {timestamp}')
    print(f'   Title: {title}')
    print(f'   Content: {content}')
    time.sleep(0.7)


@BoosterParams(
    queue_name='q_audit_all_notifications',  # Queue 6: audit all notifications
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'headers',
        # headers mode binding condition: requires has_user_id header attribute (for auditing)
        'headers_for_bind': {
            'has_user_id': 'true'  # Custom audit marker
        },
        'x_match_for_bind': 'all',
    })
def audit_all_notifications_consumer(user_id: str, title: str, content: str, timestamp: str):
    """Audit notification consumer - records all notifications for auditing"""
    print(f'[AUDIT RECORD] User {user_id} | {timestamp}')
    print(f'   Title: {title}')
    print(f'   Type: Notification audit record')
    time.sleep(0.2)


if __name__ == '__main__':
    # Clear previous messages (optional)
    # urgent_notifications_consumer.clear()
    # high_priority_notifications_consumer.clear()
    # mobile_notifications_consumer.clear()
    # system_admin_notifications_consumer.clear()
    # marketing_notifications_consumer.clear()
    # audit_all_notifications_consumer.clear()

    # Start all consumers
    print("Starting all notification service consumers...")
    urgent_notifications_consumer.consume()
    high_priority_notifications_consumer.consume()
    mobile_notifications_consumer.consume()
    system_admin_notifications_consumer.consume()
    marketing_notifications_consumer.consume()
    audit_all_notifications_consumer.consume()

    print("All notification service consumers started, waiting for messages...")
    print("Headers routing mode characteristics:")
    print("  - Routes based on message header attributes: matches based on headers in messages")
    print("  - Flexible matching rules: supports 'all' (full match) and 'any' (partial match)")
    print("  - Routing key ignored: completely based on header attributes, routing key not used")
    print("  - Complex condition routing: can implement complex business logic routing")
    print()
    print("Consumer binding rules:")
    print("  - Urgent notifications: priority=high AND urgent=true")
    print("  - High priority: priority=high")
    print("  - Mobile: platform=mobile OR device_type=phone")
    print("  - System admin: category=system AND role=admin")
    print("  - Marketing: category=marketing OR priority=low")
    print("  - Audit records: has_user_id=true")
    print("Press Ctrl+C to stop consuming...")

    # Block the main thread so consumers can keep running
    ctrl_c_recv()
