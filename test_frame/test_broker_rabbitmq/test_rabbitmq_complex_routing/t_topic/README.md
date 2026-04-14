# RabbitMQ Topic Routing Mode Example

This example demonstrates how to implement RabbitMQ's Topic routing mode using the funboost framework.

## Topic Routing Mode Characteristics

Topic routing is the most flexible routing method in RabbitMQ, allowing the use of wildcards for message routing:

- `*` (asterisk): matches exactly one word
- `#` (hash): matches zero or more words
- Words in routing keys are separated by `.` (period)

## File Descriptions

- `t_topic_consume.py`: Consumer example, showing different routing key binding patterns
- `t_topic_pub.py`: Publisher example, showing how to publish messages with dynamic routing keys

## Routing Key Binding Rules

### Consumer Binding Rules

1. **All-logs consumer** (`q_all_logs`)
   - Binding key: `#`
   - Description: Receives all messages

2. **Error-log consumer** (`q_error_logs`)
   - Binding key: `*.error`
   - Description: Receives all messages ending with `.error`
   - Matching examples: `system.error`, `app.error`, `db.error`

3. **System-log consumer** (`q_system_logs`)
   - Binding key: `system.*`
   - Description: Receives all messages starting with `system.`
   - Matching examples: `system.info`, `system.warning`, `system.error`

4. **Application-critical-log consumer** (`q_app_critical_logs`)
   - Binding key: `app.*.critical`
   - Description: Receives messages in the format `app.<any single word>.critical`
   - Matching examples: `app.auth.critical`, `app.payment.critical`

## Running the Example

### 1. Start the Consumers

```bash
cd test_frame/test_broker_rabbitmq/test_rabbitmq_complex_routing/t_topic
python t_topic_consume.py
```

### 2. Publish Messages

In another terminal, run:

```bash
cd test_frame/test_broker_rabbitmq/test_rabbitmq_complex_routing/t_topic
python t_topic_pub.py
```

## Message Routing Example

| Routing Key | Matching Consumers |
|--------|-------------|
| `system.info` | All-logs consumer + System-log consumer |
| `system.error` | All-logs consumer + System-log consumer + Error-log consumer |
| `app.auth.critical` | All-logs consumer + Application-critical-log consumer |
| `app.payment.error` | All-logs consumer + Error-log consumer |
| `db.backup.error` | All-logs consumer + Error-log consumer |
| `info` | All-logs consumer only |

## Core Configuration Notes

### Consumer Configuration

```python
@BoosterParams(
    queue_name='queue_name',
    broker_kind=BrokerEnum.RABBITMQ_COMPLEX_ROUTING,
    broker_exclusive_config={
        'exchange_name': 'topic_log_exchange',
        'exchange_type': 'topic',
        'routing_key_for_bind': 'binding_key_pattern',  # supports wildcards
    })
def consumer_function(timestamp: str, content: str):
    # The parameter names of the consumer function must exactly match the published dictionary keys
    pass
```

### Publisher Configuration

```python
topic_publisher = BoostersManager.get_cross_project_publisher(PublisherParams(
    queue_name='publisher_instance_name',
    broker_kind=BrokerEnum.RABBITMQ_COMPLEX_ROUTING,
    broker_exclusive_config={
        'exchange_name': 'topic_log_exchange',
        'exchange_type': 'topic',
    }
))

# Publish a message with a dynamically specified routing key
topic_publisher.publish(
    {'timestamp': '2025-09-30 12:47:56', 'content': 'message content'},  # dictionary keys must match consumer function parameter names
    task_options=TaskOptions(
        other_extra_params={'routing_key_for_publish': 'dynamic_routing_key'}
    )
)
```

## Use Cases

Topic routing mode is especially suited for the following scenarios:

1. **Logging systems**: Classify and process logs based on log level and source
2. **Event systems**: Route based on event type and business module
3. **Monitoring systems**: Distribute based on monitor metric type and importance
4. **Microservice communication**: Route messages based on service name and operation type

## Important Notes

1. **Parameter matching rule**: The dictionary keys published by the publisher must exactly match the parameter names of the consumer function
   - Published: `{'timestamp': '...', 'content': '...'}`
   - Consumed: `def consumer(timestamp: str, content: str):`
2. Words in routing keys are separated by `.`
3. `*` can only match exactly one word; it cannot match zero or multiple words
4. `#` can match zero, one, or multiple words
5. Routing keys are case-sensitive
6. A single message can be received by multiple queues (if the routing key matches multiple binding patterns)
