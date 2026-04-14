"""
KafkaManyThreadsConsumer usage examples and tests
Demonstrates how to use the multi-threaded Kafka consumer with ordered offset commits
"""

import time
import random
import threading
import json
from kafka_many_threads_consumer import KafkaManyThreadsConsumer


def simple_callback(message):
    """Simple message processing callback"""
    print(f"Processing message: partition={message.partition}, offset={message.offset}, "
          f"value={message.value[:100] if message.value else None}...")


def complex_callback(message):
    """Complex message processing callback - simulates a real business scenario"""
    import random

    # Simulate different processing times (0.1s to 5s)
    processing_time = random.uniform(0.1, 5.0)

    print(f"Start processing message: partition={message.partition}, offset={message.offset}, "
          f"estimated_time={processing_time:.2f}s")

    # Simulate processing
    time.sleep(processing_time)

    # Simulate occasional processing failure
    if random.random() < 0.03:  # 3% failure rate
        raise Exception(f"Simulated processing failure: partition={message.partition}, offset={message.offset}")

    print(f"Finished processing message: partition={message.partition}, offset={message.offset}, "
          f"actual_time={processing_time:.2f}s")


def database_callback(message):
    """Simulate a database write scenario"""
    try:
        # Parse message content
        if message.value:
            data = json.loads(message.value)
        else:
            data = {"empty": True}

        # Simulate database operation
        time.sleep(random.uniform(0.2, 1.0))

        # Simulate occasional database connection failure
        if random.random() < 0.02:  # 2% failure rate
            raise Exception("Database connection failed")

        print(f"Data saved to database: partition={message.partition}, offset={message.offset}")

    except json.JSONDecodeError:
        print(f"Message format error: partition={message.partition}, offset={message.offset}")
        # For format errors, we choose to skip (do not raise exception)
    except Exception as e:
        print(f"Database operation failed: {e}")
        raise  # Re-raise exception so the message is marked as failed


def run_basic_example():
    """Basic usage example"""
    print("=== Basic Usage Example ===")

    consumer = KafkaManyThreadsConsumer(
        kafka_broker_address="localhost:9092",
        topic="test-topic",
        group_id="basic-group",
        num_threads=10,
        callback_func=simple_callback
    )

    try:
        consumer.start()

        # Run for 30 seconds
        for i in range(6):
            time.sleep(5)
            stats = consumer.get_stats()
            print(f"Statistics [{i+1}/6]: consumed={stats['consumed_count']}, "
                  f"processed={stats['processed_count']}, failed={stats['failed_count']}, "
                  f"committed={stats['committed_count']}")

    except KeyboardInterrupt:
        print("Received interrupt signal")
    finally:
        consumer.stop()


def run_high_concurrency_example():
    """High concurrency scenario example"""
    print("=== High Concurrency Scenario Example ===")

    consumer = KafkaManyThreadsConsumer(
        kafka_broker_address="localhost:9092",
        topic="high-throughput-topic",
        group_id="high-concurrency-group",
        num_threads=100,  # 100 threads
        callback_func=complex_callback
    )

    try:
        consumer.start()

        # Run for 60 seconds, observe performance under high concurrency
        for i in range(12):
            time.sleep(5)
            stats = consumer.get_stats()
            offset_status = stats['offset_manager_status']

            print(f"High concurrency statistics [{i+1}/12]:")
            print(f"  Consumed: {stats['consumed_count']}")
            print(f"  Processing successes: {stats['processed_count']}")
            print(f"  Processing failures: {stats['failed_count']}")
            print(f"  Committed: {stats['committed_count']}")
            print(f"  Pending queue: {offset_status['pending_count']}")
            print(f"  Committable offsets: {offset_status['committable_offsets']}")
            print("---")

    except KeyboardInterrupt:
        print("Received interrupt signal")
    finally:
        consumer.stop()


def run_reliability_test():
    """Reliability test - simulate kill -9 scenario"""
    print("=== Reliability Test ===")
    print("This test will automatically stop after 30 seconds, simulating a sudden interruption")

    consumer = KafkaManyThreadsConsumer(
        kafka_broker_address="localhost:9092",
        topic="reliability-topic",
        group_id="reliability-group",
        num_threads=50,
        callback_func=database_callback
    )

    def auto_stop():
        """Auto-stop after 30 seconds"""
        time.sleep(30)
        print("30 seconds elapsed, simulating sudden stop...")
        consumer.stop()

    try:
        consumer.start()

        # Start auto-stop thread
        stop_thread = threading.Thread(target=auto_stop, daemon=True)
        stop_thread.start()

        # Monitor status
        start_time = time.time()
        while consumer.running:
            time.sleep(2)
            elapsed = time.time() - start_time
            stats = consumer.get_stats()

            print(f"Runtime: {elapsed:.1f}s, consumed: {stats['consumed_count']}, "
                  f"processed: {stats['processed_count']}, failed: {stats['failed_count']}")

            if elapsed > 35:  # Safety exit
                break

        print("Reliability test complete")

    except KeyboardInterrupt:
        print("Received interrupt signal")
    finally:
        if consumer.running:
            consumer.stop()


def run_multiple_consumers():
    """Multiple consumer instance test"""
    print("=== Multiple Consumer Instance Test ===")
    print("Starting 3 consumer instances to test load balancing")

    consumers = []

    for i in range(3):
        consumer = KafkaManyThreadsConsumer(
            kafka_broker_address="localhost:9092",
            topic="multi-consumer-topic",
            group_id="multi-consumer-group",  # Same group
            num_threads=20,
            callback_func=lambda msg, idx=i: print(f"Consumer {idx}: partition={msg.partition}, offset={msg.offset}")
        )
        consumers.append(consumer)

    try:
        # Start all consumers
        for i, consumer in enumerate(consumers):
            consumer.start()
            print(f"Consumer {i} started")
            time.sleep(1)  # Stagger start times

        # Run for 40 seconds
        for second in range(40):
            time.sleep(1)
            if second % 10 == 9:  # Print statistics every 10 seconds
                print(f"\n=== {second+1}s statistics ===")
                for i, consumer in enumerate(consumers):
                    stats = consumer.get_stats()
                    print(f"Consumer {i}: consumed={stats['consumed_count']}, "
                          f"processed={stats['processed_count']}")

    except KeyboardInterrupt:
        print("Received interrupt signal")
    finally:
        for i, consumer in enumerate(consumers):
            print(f"Stopping consumer {i}...")
            consumer.stop()


if __name__ == "__main__":
    import sys

    print("KafkaManyThreadsConsumer test program")
    print("Please ensure Kafka server is running at localhost:9092")
    print("and the corresponding topics have been created")
    print()

    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        print("Available test types:")
        print("1. basic - Basic usage example")
        print("2. high_concurrency - High concurrency scenario")
        print("3. reliability - Reliability test")
        print("4. multiple - Multiple consumer test")
        test_type = input("Please select test type (1-4): ").strip()

    test_mapping = {
        "1": run_basic_example,
        "basic": run_basic_example,
        "2": run_high_concurrency_example,
        "high_concurrency": run_high_concurrency_example,
        "3": run_reliability_test,
        "reliability": run_reliability_test,
        "4": run_multiple_consumers,
        "multiple": run_multiple_consumers
    }

    test_func = test_mapping.get(test_type)
    if test_func:
        test_func()
    else:
        print(f"Unknown test type: {test_type}")
        sys.exit(1)
