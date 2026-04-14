# RabbitMQ Headers Routing Mode Example

This example demonstrates how to implement RabbitMQ's Headers routing mode using the funboost framework.

## Headers Routing Mode Characteristics

Headers routing is the most flexible routing method in RabbitMQ and has the following characteristics:

- 🏷️ **Based on message header attributes**: Routing is determined entirely by the header attributes of the message, ignoring the routing key
- 🎯 **Flexible matching rules**: Supports both `all` (full match) and `any` (any match) strategies
- 🔧 **Complex conditional routing**: Can implement complex business logic routing conditions
- 📊 **Multi-dimensional matching**: Supports combined matching of multiple header attributes

## File Descriptions

- `t_headers_consume.py`: Consumer example, showing different header attribute binding rules
- `t_headers_pub.py`: Publisher example, showing how to publish messages with dynamic message headers

## Business Scenario Example

This example simulates an intelligent notification system that routes notifications to the appropriate handling service based on different message attributes:

### Consumer Services and Binding Rules

1. **🚨 Urgent Notification Service** (`q_urgent_notifications`)
   - Binding condition: `priority=high` **AND** `urgent=true`
   - Match strategy: `all` (must satisfy all conditions simultaneously)
   - Handles: highest priority urgent notifications

2. **⚡ High-Priority Notification Service** (`q_high_priority_notifications`)
   - Binding condition: `priority=high`
   - Match strategy: `all`
   - Handles: all high-priority notifications

3. **📱 Mobile Notification Service** (`q_mobile_notifications`)
   - Binding condition: `platform=mobile` **OR** `device_type=phone`
   - Match strategy: `any` (satisfying any one condition is sufficient)
   - Handles: mobile-related notifications

4. **🔧 System Admin Notification Service** (`q_system_admin_notifications`)
   - Binding condition: `category=system` **AND** `role=admin`
   - Match strategy: `all`
   - Handles: notifications exclusive to system administrators

5. **📢 Marketing Notification Service** (`q_marketing_notifications`)
   - Binding condition: `category=marketing` **OR** `priority=low`
   - Match strategy: `any`
   - Handles: marketing and promotional notifications

6. **📋 Audit Notification Service** (`q_audit_all_notifications`)
   - Binding condition: `has_user_id=true`
   - Match strategy: `all`
   - Handles: all notification records that require auditing

## Running the Example

### 1. Start the Consumers

```bash
cd test_frame/test_broker_rabbitmq/test_rabbitmq_complex_routing/t_headers
python t_headers_consume.py
```

### 2. Publish Messages

In another terminal, run:

```bash
cd test_frame/test_broker_rabbitmq/test_rabbitmq_complex_routing/t_headers
python t_headers_pub.py
```

## Message Routing Example

| Message Type | Message Header Attributes | Matching Consumers |
|---------|-----------|-------------|
| Critical System Failure | `priority=high, urgent=true, category=system, role=admin` | 🚨Urgent + ⚡High Priority + 🔧System Admin + 📋Audit |
| Order Payment Success | `priority=high, platform=mobile` | ⚡High Priority + 📱Mobile + 📋Audit |
| New Feature Launch | `priority=low, category=marketing` | 📢Marketing + 📋Audit |
| Account Security Alert | `priority=high, urgent=true, device_type=phone` | 🚨Urgent + ⚡High Priority + 📱Mobile + 📋Audit |
| System Maintenance Notice | `category=system, role=admin, priority=medium` | 🔧System Admin + 📋Audit |

## Core Configuration Notes

### Consumer Configuration

```python
@BoosterParams(
    queue_name='queue_name',
    broker_kind=BrokerEnum.RABBITMQ_COMPLEX_ROUTING,
    broker_exclusive_config={
        'exchange_name': 'headers_notification_exchange',
        'exchange_type': 'headers',
        'headers_for_bind': {
            'priority': 'high',      # header attribute matching condition
            'urgent': 'true'         # multiple conditions can be set
        },
        'x_match_for_bind': 'all',   # 'all' or 'any'
    })
def consumer_function(user_id: str, title: str, content: str, timestamp: str):
    # The parameter names of the consumer function must exactly match the published dictionary keys
    pass
```

### Publisher Configuration

```python
headers_publisher = BoostersManager.get_cross_project_publisher(PublisherParams(
    queue_name='publisher_instance_name',
    broker_kind=BrokerEnum.RABBITMQ_COMPLEX_ROUTING,
    broker_exclusive_config={
        'exchange_name': 'headers_notification_exchange',
        'exchange_type': 'headers',
        # headers mode does not use routing keys
    }
))

# Publish a message with specified header attributes
headers_publisher.publish(
    {'user_id': 'user001', 'title': 'Title', 'content': 'Content', 'timestamp': 'Timestamp'},
    task_options=TaskOptions(
        other_extra_params={
            'headers_for_publish': {
                'priority': 'high',
                'urgent': 'true',
                'category': 'system'
            }
        }
    )
)
```

## Match Strategy Explanation

### `x_match_for_bind: 'all'` (Full Match)
- The message headers must include **all** specified attributes with exact value matches
- Suitable for scenarios requiring strict condition control

### `x_match_for_bind: 'any'` (Any Match)
- The message headers only need to match **any one** of the specified attributes
- Suitable for scenarios where multiple conditions can each trigger routing

## Use Cases

Headers routing mode is especially suited for the following scenarios:

1. **Intelligent notification systems**: Route based on priority, platform, user role, and other dimensions
2. **Multi-tenant systems**: Route based on tenant ID, permission level, and other attributes
3. **Content distribution systems**: Route based on content type, region, language, and other attributes
4. **Monitoring and alerting systems**: Route based on alert level, service type, responsible party, and other attributes
5. **Workflow systems**: Route based on task type, handler, priority, and other attributes
6. **API gateways**: Route based on request origin, authentication level, API version, and other attributes

## Comparison with Other Routing Modes

| Routing Mode | Routing Basis | Flexibility | Complexity | Use Cases |
|---------|---------|--------|--------|---------|
| **Headers** | Message header attributes | Highest | Most complex | Complex multi-dimensional routing |
| **Topic** | Wildcard routing key | High | Medium | Hierarchical message classification |
| **Direct** | Exact routing key | Medium | Simple | Point-to-point or simple grouping |
| **Fanout** | Unconditional broadcast | Lowest | Simplest | Broadcast notifications |

## Important Notes

1. **Parameter matching rule**: The dictionary keys published by the publisher must exactly match the parameter names of the consumer function
   - Published: `{'user_id': '...', 'title': '...', 'content': '...', 'timestamp': '...'}`
   - Consumed: `def consumer(user_id: str, title: str, content: str, timestamp: str):`

2. **Header attribute types**: All header attribute values are strings; be mindful of type conversion

3. **Performance consideration**: Headers routing is slightly slower than other modes because multiple header attributes must be checked

4. **Routing key ignored**: Headers mode completely ignores the routing key and routes solely based on header attributes

5. **Match strategy selection**:
   - When using `all`, ensure the message headers contain all required attributes
   - When using `any`, be aware of potential unexpected matches

6. **Debugging tip**: It is recommended to add an audit queue during development to observe the routing of all messages
