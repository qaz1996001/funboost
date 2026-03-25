# -*- coding: utf-8 -*-
# @Author  : ydf

from funboost import BoostersManager, PublisherParams, BrokerEnum, TaskOptions
import time

BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING
EXCHANGE_NAME = 'fanout_broadcast_exchange'


if __name__ == '__main__':
    # Create a fanout publisher to broadcast messages to all bound queues
    fanout_publisher = BoostersManager.get_cross_project_publisher(PublisherParams(
        queue_name='fanout_publisher_instance',
        broker_kind=BROKER_KIND_FOR_TEST,
        broker_exclusive_config={
            'exchange_name': EXCHANGE_NAME,
            'exchange_type': 'fanout',
            # fanout mode does not need routing_key; it will be ignored
        }
    ))

    print("Starting to publish user operation event messages...")
    print("=" * 60)

    # Simulate different user operation events
    user_events = [
        {
            'user_id': 'user_001',
            'action': 'User registration',
            'message': 'New user registered successfully, welcome notification needs to be sent'
        },
        {
            'user_id': 'user_002',
            'action': 'Order payment',
            'message': 'User completed order payment, amount $299.00'
        },
        {
            'user_id': 'user_003',
            'action': 'Password change',
            'message': 'User changed login password, security reminder needed'
        },
        {
            'user_id': 'user_001',
            'action': 'Membership upgrade',
            'message': 'User upgraded to VIP membership, enjoy exclusive services'
        },
        {
            'user_id': 'user_004',
            'action': 'Order refund',
            'message': 'User requested order refund, amount $158.00'
        },
        {
            'user_id': 'user_002',
            'action': 'Product review',
            'message': 'User gave a 5-star review for the product'
        },
        {
            'user_id': 'user_005',
            'action': 'Account anomaly',
            'message': 'Abnormal login detected, security verification needed'
        },
        {
            'user_id': 'user_003',
            'action': 'Points redemption',
            'message': 'User used points to redeem a coupon'
        }
    ]

    for i, event in enumerate(user_events, 1):
        print(f"[{i}] Publishing event: user {event['user_id']} - {event['action']}")
        print(f"    Message content: {event['message']}")

        # Publish message - fanout mode broadcasts to all bound queues
        # Note: even if a routing key is specified, fanout mode will ignore it
        fanout_publisher.publish(
            {
                'user_id': event['user_id'],
                'action': event['action'],
                'message': event['message']
            },
            task_options=TaskOptions(
                # Even if a routing key is set, fanout mode will ignore it and all queues will receive the message
                other_extra_params={'routing_key_for_publish': 'ignored_routing_key'}
            )
        )

        print(f"    Message broadcast to all services (email, SMS, push, audit, data analytics)")
        print()

        # Short delay to make it easier to observe the consumer processing
        time.sleep(1)

    print("=" * 60)
    print("All event messages published!")
    print("\nFanout routing mode description:")
    print("  Each message is broadcast to all 5 services:")
    print("     - Email service: send email notifications")
    print("     - SMS service: send SMS notifications")
    print("     - Push service: send push notifications")
    print("     - Audit service: record operation logs")
    print("     - Data analytics: collect behavior data")
    print("  Routing key is completely ignored; regardless of the value set, messages are broadcast to all queues")
    print("  Suitable for scenarios where multiple services need to handle the same event simultaneously")
