# RabbitMQ Fanout Routing Mode Example

This example demonstrates how to implement RabbitMQ's Fanout routing mode using the funboost framework.

## Fanout Routing Mode Characteristics

Fanout routing is the simplest routing method in RabbitMQ and has the following characteristics:

- 📢 **Broadcast mode**: Messages are delivered to all queues bound to the exchange
- 🚫 **Routing key ignored**: No matter what routing key is used when publishing, it is always ignored
- ⚡ **Efficient and simple**: No complex routing rule matching required
- 🔄 **One-to-many**: A single message can be processed simultaneously by multiple different services

## File Descriptions

- `t_fanout_consume.py`: Consumer example, showing multiple services receiving broadcast messages simultaneously
- `t_fanout_pub.py`: Publisher example, showing how to publish broadcast messages

## Business Scenario Example

This example simulates a user-action event notification system, including the following services:

### Consumer Services

1. **📧 Email Service** (`q_email_service`)
   - Handles all user events that require sending email notifications
   - e.g.: registration welcome email, order confirmation email, security alert email

2. **📱 SMS Service** (`q_sms_service`)
   - Handles all user events that require sending SMS notifications
   - e.g.: verification code SMS, important operation reminder SMS

3. **🔔 Push Notification Service** (`q_push_service`)
   - Handles all user events that require push notifications
   - e.g.: app push notifications, browser push notifications

4. **📝 Audit Service** (`q_audit_service`)
   - Records all user operation logs for security auditing
   - e.g.: login records, sensitive operation records

5. **📊 Data Analytics Service** (`q_analytics_service`)
   - Collects user behavior data for data analysis
   - e.g.: user behavior statistics, business metric calculations

## Running the Example

### 1. Start the Consumers

```bash
cd test_frame/test_broker_rabbitmq/test_rabbitmq_complex_routing/t_fanout
python t_fanout_consume.py
```

### 2. Publish Messages

In another terminal, run:

```bash
cd test_frame/test_broker_rabbitmq/test_rabbitmq_complex_routing/t_fanout
python t_fanout_pub.py
```

## Message Broadcast Example

When a single user event message is published, **all 5 services receive the same message**:

| User Event | Receiving Services |
|---------|-----------|
| User Registration | 📧Email + 📱SMS + 🔔Push + 📝Audit + 📊Analytics |
| Order Payment | 📧Email + 📱SMS + 🔔Push + 📝Audit + 📊Analytics |
| Password Change | 📧Email + 📱SMS + 🔔Push + 📝Audit + 📊Analytics |
| Membership Upgrade | 📧Email + 📱SMS + 🔔Push + 📝Audit + 📊Analytics |

## Core Configuration Notes

### Consumer Configuration

```python
@BoosterParams(
    queue_name='service_queue_name',
    broker_kind=BrokerEnum.RABBITMQ_COMPLEX_ROUTING,
    broker_exclusive_config={
        'exchange_name': 'fanout_broadcast_exchange',
        'exchange_type': 'fanout',
        # fanout mode does not require specifying routing_key_for_bind
        # The system will automatically use an empty string as the binding key
    })
def service_consumer(user_id: str, action: str, message: str):
    # The parameter names of the consumer function must exactly match the published dictionary keys
    pass
```

### Publisher Configuration

```python
fanout_publisher = BoostersManager.get_cross_project_publisher(PublisherParams(
    queue_name='publisher_instance_name',
    broker_kind=BrokerEnum.RABBITMQ_COMPLEX_ROUTING,
    broker_exclusive_config={
        'exchange_name': 'fanout_broadcast_exchange',
        'exchange_type': 'fanout',
        # fanout mode does not require setting routing_key_for_publish
    }
))

# Publish a message
fanout_publisher.publish(
    {'user_id': 'user001', 'action': 'user_registration', 'message': 'Welcome new user'},
    task_options=TaskOptions(
        # Even if a routing key is set, fanout mode will ignore it
        other_extra_params={'routing_key_for_publish': 'ignored_key'}
    )
)
```

## Use Cases

Fanout routing mode is especially suited for the following scenarios:

1. **Notification systems**: A user action needs to trigger multiple notification channels (email, SMS, push)
2. **Log collection**: A single log entry needs to be processed by multiple log-handling services
3. **Data synchronization**: Data changes need to be synchronized to multiple systems
4. **Event-driven**: A single event needs to trigger multiple business workflows
5. **Monitoring and alerting**: Alert information needs to be sent to multiple monitoring systems
6. **Cache invalidation**: A data update needs to clear multiple caching systems

## Comparison with Other Routing Modes

| Routing Mode | Routing Rule | Message Distribution | Use Cases |
|---------|---------|---------|---------|
| **Fanout** | Ignores routing key, broadcasts to all queues | One-to-many (broadcast) | Notification systems, log collection |
| **Direct** | Exact routing key match | One-to-one or one-to-many | Task dispatching, point-to-point communication |
| **Topic** | Wildcard routing key match | Flexible one-to-many | Complex message classification |
| **Headers** | Match based on message header attributes | Attribute-based routing | Complex conditional routing |

## Important Notes

1. **Parameter matching rule**: The dictionary keys published by the publisher must exactly match the parameter names of the consumer function
   - Published: `{'user_id': '...', 'action': '...', 'message': '...'}`
   - Consumed: `def consumer(user_id: str, action: str, message: str):`

2. **Routing key ignored**: No matter what routing key is set when publishing, fanout mode will always ignore it

3. **Performance consideration**: Since it is broadcast mode, messages are copied to all queues; consider message volume and processing capacity

4. **Queue management**: All queues bound to the fanout exchange will receive the message; pay attention to queue lifecycle management

5. **Message order**: The processing order of messages in different queues may vary; do not rely on processing order
