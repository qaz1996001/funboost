#!/usr/bin/env python3
"""
KafkaManyThreadsConsumer quick start example

Prerequisites:
1. pip install kafka-python
2. Start Kafka server (localhost:9092)
3. Create test topic: kafka-topics.sh --create --topic test-topic --partitions 2 --bootstrap-server localhost:9092

How to run:
python quick_start.py
"""

import time
import random
from kafka_many_threads_consumer import KafkaManyThreadsConsumer


def simple_message_handler(message):
    """
    Simple message handler function
    Demonstrates how to process Kafka messages
    """
    # Simulate business processing time
    processing_time = random.uniform(0.1, 2.0)
    time.sleep(processing_time)

    print(f"✅ Processing complete: partition={message.partition}, offset={message.offset}, "
          f"time_taken={processing_time:.2f}s")

    # Simulate occasional processing failure (5% chance)
    if random.random() < 0.05:
        print(f"❌ Simulated processing failure: partition={message.partition}, offset={message.offset}")
        raise Exception("Simulated business processing failure")


def main():
    print("🚀 Starting KafkaManyThreadsConsumer demo")
    print("=" * 50)

    # Create consumer instance
    consumer = KafkaManyThreadsConsumer(
        kafka_broker_address="localhost:9092",  # Kafka address
        topic="test-topic",                     # Topic name
        group_id="demo-group",                  # Consumer group
        num_threads=20,                         # Thread count (can far exceed partition count)
        callback_func=simple_message_handler   # Message handler function
    )

    try:
        # Start consumer
        print("📡 Starting consumer...")
        consumer.start()
        print("✅ Consumer started successfully!")
        print()

        # Run for 60 seconds, print statistics every 10 seconds
        for i in range(6):
            time.sleep(10)

            stats = consumer.get_stats()
            print(f"📊 Statistics ({(i+1)*10}s):")
            print(f"   Messages consumed: {stats['consumed_count']}")
            print(f"   Processing successes: {stats['processed_count']}")
            print(f"   Processing failures: {stats['failed_count']}")
            print(f"   Committed count: {stats['committed_count']}")

            # Show detailed offset status
            offset_status = stats['offset_manager_status']
            if offset_status['pending_count']:
                print(f"   Pending queue: {offset_status['pending_count']}")
            if offset_status['committable_offsets']:
                print(f"   Committable offsets: {offset_status['committable_offsets']}")
            print()

    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal, stopping gracefully...")

    finally:
        # Stop consumer
        print("⏹️  Stopping consumer...")
        consumer.stop()
        print("✅ Consumer stopped")

        # Show final statistics
        final_stats = consumer.get_stats()
        print("\n📈 Final statistics:")
        print(f"   Total consumed: {final_stats['consumed_count']}")
        print(f"   Total processing successes: {final_stats['processed_count']}")
        print(f"   Total processing failures: {final_stats['failed_count']}")
        print(f"   Total committed: {final_stats['committed_count']}")


if __name__ == "__main__":
    # Check dependencies
    try:
        import kafka
        print(f"✅ kafka-python version: {kafka.__version__}")
    except ImportError:
        print("❌ Please install kafka-python first: pip install kafka-python")
        exit(1)

    print("🔧 Configuration check:")
    print("   Kafka address: localhost:9092")
    print("   Topic: test-topic")
    print("   Consumer group: demo-group")
    print("   Thread count: 20")
    print()

    input("Press Enter to start the demo... (ensure Kafka server is running and test-topic is created)")

    main()

    print("\n🎉 Demo complete!")
    print("💡 Tips:")
    print("   - This implementation ensures no message loss")
    print("   - Supports kill -9 restart and continues consuming")
    print("   - Thread count can far exceed partition count")
    print("   - Automatically manages offset commit order")
