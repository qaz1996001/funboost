# KafkaManyThreadsConsumer

## Introduction

This is a Kafka consumer class built from scratch, specifically designed to solve the problem
of message loss in multi-threaded environments.

## Core Features

✅ **Supports very high thread counts**: The number of threads can far exceed the number of
partitions (e.g., 100 threads processing 2 partitions)

✅ **No message loss**: Ensures that messages are never lost or skipped even after a `kill -9`
restart

✅ **Ordered offset commits**: Only commits offsets for consecutively completed messages,
avoiding gaps in offset progression

✅ **Automatic retry mechanism**: Messages that fail processing will be re-consumed after a restart

✅ **Comprehensive monitoring**: Provides detailed statistics and status monitoring

## Problem Being Solved

### The Problem with Traditional Approaches
```
Message processing times: msg1(100s) -> msg2(30s) -> msg3(10s)
If offsets are committed by completion order: msg3 finishes first and commits its offset
Sudden restart -> msg1 and msg2 are lost ❌
```

### Our Solution
```
Ordered offset manager:
- Only commits offsets for consecutively completed messages
- msg3 completes but does not commit; waits for msg1 and msg2
- Ensures restart resumes from the correct position ✅
```

## Installation

```bash
pip install kafka-python
```

## Basic Usage

```python
from kafka_many_threads_consumer import KafkaManyThreadsConsumer

def my_callback(message):
    """Your message processing logic"""
    print(f"Processing message: {message.value}")
    # Your business logic...

# Create consumer
consumer = KafkaManyThreadsConsumer(
    kafka_broker_address="localhost:9092",
    topic="my-topic",
    group_id="my-group",
    num_threads=100,  # Supports many threads
    callback_func=my_callback
)

# Start consumer
consumer.start()

# Monitor status
stats = consumer.get_stats()
print(f"Stats: {stats}")

# Stop consumer
consumer.stop()
```

## Advanced Configuration

### 1. Handling Failed Retries
```python
def reliable_callback(message):
    try:
        # Your business logic
        process_business_logic(message)
    except RetryableError as e:
        # Raise the exception; the message will be re-consumed after a restart
        raise e
    except NonRetryableError as e:
        # Do not raise; the message will be skipped
        logging.error(f"Unrecoverable error: {e}")
```

### 2. Database Transaction Scenario
```python
def database_callback(message):
    with database.transaction():
        try:
            # Parse the message
            data = json.loads(message.value)
            
            # Database operation
            save_to_database(data)
            
            # Success: do not raise an exception; the offset will be committed
            
        except DatabaseError:
            # Failure: raise the exception; reprocess after restart
            raise
```

### 3. Multiple Consumer Instances
```python
# Deploy multiple instances with automatic load balancing
for i in range(3):
    consumer = KafkaManyThreadsConsumer(
        kafka_broker_address="localhost:9092",
        topic="high-throughput-topic",
        group_id="same-group",  # Same group_id
        num_threads=50,
        callback_func=my_callback
    )
    consumer.start()
```

## Architecture Design

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Kafka Consumer  │────│  OffsetManager   │────│  Offset Commit  │
│     Thread       │    │  Ordered Manager │    │     Thread      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│   ThreadPool    │    │  Message State   │
│  (N worker      │    │   Tracking       │
│   threads)      │    │  - Pending queue │
└─────────────────┘    │  - Done markers  │
                       │  - Continuity    │
                       │    check         │
                       └──────────────────┘
```

## Core Components

### 1. OffsetManager
- **Function**: Manages the processing state of messages for each partition
- **Behavior**: Only commits offsets for consecutively completed messages
- **Thread safety**: Uses RLock to ensure concurrent safety

### 2. MessageTask
- **Function**: Encapsulates a message processing task
- **Contains**: Message record, status, error information, etc.
- **Lifecycle**: Created -> Processing -> Completed -> Cleaned up

### 3. Consumption Loop
- **Main thread**: Responsible for polling messages from Kafka
- **Worker thread pool**: Processes messages in parallel
- **Commit thread**: Periodically commits offsets that are safe to commit

## Monitoring and Debugging

### Getting Statistics
```python
stats = consumer.get_stats()
print(json.dumps(stats, indent=2, ensure_ascii=False))

# Example output:
{
  "consumed_count": 1000,      # Number of messages consumed
  "processed_count": 995,      # Number successfully processed
  "failed_count": 5,           # Number of processing failures
  "committed_count": 990,      # Number of committed offsets
  "offset_manager_status": {
    "pending_count": {         # Pending count per partition
      "0": 3,
      "1": 2
    },
    "committable_offsets": {   # Committable offsets
      "0": 500,
      "1": 450
    }
  }
}
```

### Log Level Configuration
```python
import logging
logging.getLogger('KafkaConsumer-your-group').setLevel(logging.DEBUG)
```

## Performance Optimization Tips

### 1. Thread Count Configuration
```python
# CPU-bound tasks
num_threads = cpu_count() * 2

# I/O-bound tasks (database, network)
num_threads = cpu_count() * 4 to 8

# Mixed tasks
num_threads = cpu_count() * 3
```

### 2. Kafka Configuration Optimization
```python
consumer = KafkaConsumer(
    max_poll_records=500,        # Batch size
    session_timeout_ms=30000,    # Session timeout
    heartbeat_interval_ms=3000,  # Heartbeat interval
    fetch_min_bytes=1024,        # Minimum fetch bytes
    fetch_max_wait_ms=500        # Maximum wait time
)
```

### 3. Memory Management
- Clean up completed tasks promptly
- Monitor the size of the pending queue
- Set an appropriate poll timeout

## Test Scenarios

Run the test examples:
```bash
# Basic functionality test
python test_kafka_consumer_example.py basic

# High-concurrency test
python test_kafka_consumer_example.py high_concurrency

# Reliability test (simulates kill -9)
python test_kafka_consumer_example.py reliability

# Multiple consumer test
python test_kafka_consumer_example.py multiple
```

## Troubleshooting

### 1. Slow Message Processing
- Check the execution time of `callback_func`
- Increase the thread count
- Optimize business logic

### 2. Offset Commit Delay
- Check whether any messages have been pending for a long time
- Review the `pending_count` statistics
- Confirm there are no deadlocks or infinite loops

### 3. Duplicate Consumption
- Ensure the message processing logic is idempotent
- Check for uncaught exceptions
- Verify that offset commits are working correctly

### 4. Memory Leak
- Monitor the size of the `pending_messages` queue
- Ensure exception handling is correct
- Periodically restart long-running instances

## Best Practices

1. **Idempotency**: Ensure the message processing logic is idempotent
2. **Exception handling**: Distinguish between retryable and non-retryable errors
3. **Monitoring**: Regularly check statistics and queue status
4. **Testing**: Thoroughly test exception scenarios and restart recovery
5. **Deployment**: Use container orchestration tools to manage multiple instances

## Limitations and Considerations

1. **Memory usage**: A large number of threads increases memory consumption
2. **Kafka version**: Kafka 0.10+ is recommended
3. **Network**: Ensure stable network connectivity to the Kafka cluster
4. **Disk space**: Kafka log retention policies should be set appropriately

## Contributing

Issues and Pull Requests to improve this implementation are welcome!
