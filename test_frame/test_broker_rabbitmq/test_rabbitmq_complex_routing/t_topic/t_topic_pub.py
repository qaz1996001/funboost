# -*- coding: utf-8 -*-
# @Author  : ydf

from funboost import BoostersManager, PublisherParams, BrokerEnum, TaskOptions
import time

BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING
EXCHANGE_NAME = 'topic_log_exchange'


if __name__ == '__main__':
    # Create a generic publisher for publishing messages to the topic exchange.
    # queue_name here is only used to generate the publisher instance; actual routing is determined by routing_key.
    topic_publisher = BoostersManager.get_cross_project_publisher(PublisherParams(
        queue_name='topic_publisher_instance',
        broker_kind=BROKER_KIND_FOR_TEST,
        broker_exclusive_config={
            'exchange_name': EXCHANGE_NAME,
            'exchange_type': 'topic',
            # Do not set a default routing_key_for_publish; specify dynamically each time when publishing
        }
    ))

    print("Starting to publish various types of log messages...")
    print("=" * 60)

    # Publish messages with different routing keys to demonstrate topic routing flexibility
    messages_to_publish = [
        # System-related logs
        ('system.info', 'System startup complete'),
        ('system.warning', 'System memory usage is high'),
        ('system.error', 'System disk space insufficient'),

        # Application-related logs
        ('app.user.info', 'User login successful'),
        ('app.order.warning', 'Order processing delayed'),
        ('app.payment.error', 'Payment API call failed'),
        ('app.auth.critical', 'Abnormal login attempt detected'),

        # Database-related logs
        ('db.connection.info', 'Database connection pool initialized'),
        ('db.query.warning', 'Slow query detected'),
        ('db.backup.error', 'Database backup failed'),

        # Network-related logs
        ('network.api.info', 'API call successful'),
        ('network.cdn.error', 'CDN node anomaly'),

        # Other log formats
        ('critical.system.failure', 'Critical system failure'),
        ('info', 'Simple info log'),
    ]

    for i, (routing_key, message_content) in enumerate(messages_to_publish, 1):
        print(f"[{i:2d}] Publishing message - routing key: '{routing_key}' - content: {message_content}")

        # Publish message using dynamic routing key
        topic_publisher.publish(
            {'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'), 'content': message_content},
            task_options=TaskOptions(
                other_extra_params={'routing_key_for_publish': routing_key}
            )
        )

        # Short delay to make it easier to observe the consumer processing
        time.sleep(0.2)

    print("=" * 60)
    print("Message publishing complete!")
    print("\nRouting match description:")
    print("  - 'system.info' will be received by: all logs consumer + system logs consumer")
    print("  - 'system.error' will be received by: all logs consumer + system logs consumer + error logs consumer")
    print("  - 'app.auth.critical' will be received by: all logs consumer + app critical logs consumer")
    print("  - 'app.payment.error' will be received by: all logs consumer + error logs consumer")
    print("  - 'db.backup.error' will be received by: all logs consumer + error logs consumer")
    print("  - 'info' will be received by: all logs consumer")
    print("\nTopic routing rules:")
    print("  - '#': matches zero or more words")
    print("  - '*': matches exactly one word")
    print("  - Words are separated by '.'")
