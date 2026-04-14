# -*- coding: utf-8 -*-
# @Author  : ydf

from funboost import BoostersManager, PublisherParams, BrokerEnum, TaskOptions
import time
from typing import Dict, Any, List

BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING
EXCHANGE_NAME = 'headers_notification_exchange'


if __name__ == '__main__':
    # Create a headers publisher to route messages based on message header attributes
    headers_publisher = BoostersManager.get_cross_project_publisher(PublisherParams(
        queue_name='headers_publisher_instance',
        broker_kind=BROKER_KIND_FOR_TEST,
        broker_exclusive_config={
            'exchange_name': EXCHANGE_NAME,
            'exchange_type': 'headers',
            # headers mode does not use routing keys; routing is completely based on message header attributes
        }
    ))

    print("Starting to publish various types of notification messages...")
    print("=" * 70)

    # Define different types of notification messages and their header attributes
    notifications: List[Dict[str, Any]] = [
        {
            'message': {
                'user_id': 'admin_001',
                'title': 'Critical system failure alert',
                'content': 'Database connection pool exhausted, immediate action required',
                'timestamp': '2025-09-30 13:10:00'
            },
            'headers': {
                'priority': 'high',
                'urgent': 'true',
                'category': 'system',
                'role': 'admin',
                'has_user_id': 'true'
            },
            'description': 'Urgent system admin notification'
        },
        {
            'message': {
                'user_id': 'user_123',
                'title': 'Order payment successful',
                'content': 'Your order #12345 has been paid successfully, amount $299.00',
                'timestamp': '2025-09-30 13:11:00'
            },
            'headers': {
                'priority': 'high',
                'category': 'order',
                'platform': 'mobile',
                'has_user_id': 'true'
            },
            'description': 'High-priority mobile notification'
        },
        {
            'message': {
                'user_id': 'user_456',
                'title': 'New feature launch notification',
                'content': 'We launched a brand new points redemption feature, come and try it!',
                'timestamp': '2025-09-30 13:12:00'
            },
            'headers': {
                'priority': 'low',
                'category': 'marketing',
                'platform': 'web',
                'has_user_id': 'true'
            },
            'description': 'Marketing promotion notification'
        },
        {
            'message': {
                'user_id': 'user_789',
                'title': 'Account security reminder',
                'content': 'Your account was logged in from a new device, please confirm if it was you',
                'timestamp': '2025-09-30 13:13:00'
            },
            'headers': {
                'priority': 'high',
                'urgent': 'true',
                'category': 'security',
                'device_type': 'phone',
                'has_user_id': 'true'
            },
            'description': 'Urgent security notification'
        },
        {
            'message': {
                'user_id': 'admin_002',
                'title': 'System maintenance notice',
                'content': 'System will undergo maintenance upgrade tonight from 23:00-01:00',
                'timestamp': '2025-09-30 13:14:00'
            },
            'headers': {
                'priority': 'medium',
                'category': 'system',
                'role': 'admin',
                'platform': 'web',
                'has_user_id': 'true'
            },
            'description': 'System admin notification'
        },
        {
            'message': {
                'user_id': 'user_101',
                'title': 'Coupon expiry reminder',
                'content': 'You have 3 coupons expiring tomorrow, please use them in time',
                'timestamp': '2025-09-30 13:15:00'
            },
            'headers': {
                'priority': 'low',
                'category': 'marketing',
                'platform': 'mobile',
                'device_type': 'phone',
                'has_user_id': 'true'
            },
            'description': 'Marketing mobile notification'
        },
        {
            'message': {
                'user_id': 'user_202',
                'title': 'Membership level upgrade',
                'content': 'Congratulations on upgrading to Gold membership, enjoy more exclusive benefits',
                'timestamp': '2025-09-30 13:16:00'
            },
            'headers': {
                'priority': 'medium',
                'category': 'membership',
                'platform': 'web',
                'has_user_id': 'true'
            },
            'description': 'Membership-related notification'
        },
        {
            'message': {
                'user_id': 'admin_003',
                'title': 'User report processing',
                'content': 'Content reported by user_999 needs review and processing',
                'timestamp': '2025-09-30 13:17:00'
            },
            'headers': {
                'priority': 'high',
                'category': 'system',
                'role': 'admin',
                'urgent': 'false',
                'has_user_id': 'true'
            },
            'description': 'High-priority system admin notification'
        }
    ]

    for i, notification in enumerate(notifications, 1):
        print(f"[{i}] Publishing notification: {notification['description']}")
        print(f"    User: {notification['message']['user_id']}")  # type: ignore
        print(f"    Title: {notification['message']['title']}")  # type: ignore
        print(f"    Message headers: {notification['headers']}")

        # Use headers for message routing
        headers_publisher.publish(
            notification['message'],  # type: ignore
            task_options=TaskOptions(
                other_extra_params={
                    'headers_for_publish': notification['headers']  # type: ignore
                }
            )
        )

        print("    Message routed based on header attributes")
        print()

        # Short delay to make it easier to observe the consumer processing
        time.sleep(1.5)

    print("=" * 70)
    print("All notification messages published!")
    print("\nHeaders routing match description:")
    print("  Message 1 (critical system failure): priority=high + urgent=true + category=system + role=admin")
    print("     -> Matches: Urgent notifications + High priority + System admin + Audit records")
    print()
    print("  Message 2 (order payment successful): priority=high + platform=mobile")
    print("     -> Matches: High priority + Mobile + Audit records")
    print()
    print("  Message 3 (new feature launch): priority=low + category=marketing")
    print("     -> Matches: Marketing notifications + Audit records")
    print()
    print("  Message 4 (account security): priority=high + urgent=true + device_type=phone")
    print("     -> Matches: Urgent notifications + High priority + Mobile + Audit records")
    print()
    print("Headers routing rules:")
    print("  - Based on message header attributes, routing key not used")
    print("  - 'all' match: must satisfy all specified header attributes")
    print("  - 'any' match: satisfying any one specified header attribute is enough")
    print("  - Supports complex business logic routing conditions")
