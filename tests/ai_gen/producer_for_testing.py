#!/usr/bin/env python3
"""
Kafka producer test tool
Used for testing message production for KafkaManyThreadsConsumer

Usage:
python producer_for_testing.py
"""

import time
import json
import random
from datetime import datetime
try:
    from kafka import KafkaProducer
except ImportError:
    print("Please install kafka-python: pip install kafka-python")
    exit(1)


class TestMessageProducer:
    """Test message producer"""

    def __init__(self, kafka_broker="localhost:9092", topic="test-topic"):
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=[kafka_broker],
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
            key_serializer=lambda k: str(k).encode('utf-8') if k else None,
            acks='all',  # Wait for all replicas to confirm
            retries=3,
            batch_size=16384,
            linger_ms=10,
            compression_type='gzip'
        )
        self.message_count = 0

    def generate_test_message(self):
        """Generate a test message"""
        self.message_count += 1

        message_types = [
            "user_action",
            "order_event",
            "system_log",
            "sensor_data",
            "notification"
        ]

        return {
            "id": self.message_count,
            "timestamp": datetime.now().isoformat(),
            "type": random.choice(message_types),
            "user_id": random.randint(1000, 9999),
            "data": {
                "action": random.choice(["click", "view", "purchase", "login", "logout"]),
                "value": random.uniform(1.0, 100.0),
                "metadata": {
                    "source": "test_producer",
                    "version": "1.0",
                    "batch": random.randint(1, 10)
                }
            },
            "processing_hint": {
                "estimated_time": random.uniform(0.1, 5.0),  # Expected processing time
                "priority": random.choice(["low", "normal", "high"]),
                "retryable": random.choice([True, False])
            }
        }

    def send_message(self, message=None, key=None):
        """Send a single message"""
        if message is None:
            message = self.generate_test_message()

        if key is None:
            key = message.get("user_id", self.message_count)

        try:
            future = self.producer.send(self.topic, value=message, key=key)
            # Wait for send result
            record_metadata = future.get(timeout=10)

            print(f"✅ Message sent: partition={record_metadata.partition}, "
                  f"offset={record_metadata.offset}, key={key}")
            return True

        except Exception as e:
            print(f"❌ Send failed: {e}")
            return False

    def send_batch(self, count=10, interval=0.5):
        """Send messages in batch"""
        print(f"📤 Starting to send {count} messages, interval {interval} seconds")

        success_count = 0
        start_time = time.time()

        for i in range(count):
            message = self.generate_test_message()
            if self.send_message(message):
                success_count += 1

            if i < count - 1:  # Do not wait after the last message
                time.sleep(interval)

        elapsed = time.time() - start_time
        print(f"📊 Send complete: {success_count}/{count} succeeded, time taken {elapsed:.2f}s")

        # Ensure all messages are sent
        self.producer.flush()

    def send_continuous(self, duration_seconds=60, rate_per_second=2):
        """Send messages continuously"""
        print(f"🔄 Sending messages continuously for {duration_seconds} seconds at {rate_per_second} msgs/sec")

        interval = 1.0 / rate_per_second
        end_time = time.time() + duration_seconds
        sent_count = 0

        while time.time() < end_time:
            message = self.generate_test_message()
            if self.send_message(message):
                sent_count += 1

            time.sleep(interval)

        print(f"📊 Continuous send complete: total {sent_count} messages sent")
        self.producer.flush()

    def send_burst(self, burst_size=100, burst_count=3, burst_interval=10):
        """Burst send mode"""
        print(f"💥 Burst send mode: {burst_count} rounds, {burst_size} per round, {burst_interval}s interval")

        for burst in range(burst_count):
            print(f"💥 Round {burst + 1} burst...")

            # Rapidly send a batch of messages
            for i in range(burst_size):
                message = self.generate_test_message()
                self.send_message(message)

                if i % 10 == 9:  # Flush every 10 messages
                    self.producer.flush()

            self.producer.flush()
            print(f"✅ Round {burst + 1} complete, sent {burst_size} messages")

            if burst < burst_count - 1:  # Do not wait after the last round
                print(f"⏳ Waiting {burst_interval} seconds...")
                time.sleep(burst_interval)

    def close(self):
        """Close producer"""
        self.producer.close()


def main():
    print("🚀 Kafka test message producer")
    print("=" * 50)

    # Create producer
    producer = TestMessageProducer()

    try:
        print("📋 Select send mode:")
        print("1. Send 10 test messages")
        print("2. Send continuously for 60 seconds (2 msgs/sec)")
        print("3. Burst mode (3 rounds x 100 messages)")
        print("4. Custom batch send")

        choice = input("Please select (1-4): ").strip()

        if choice == "1":
            producer.send_batch(count=10, interval=1.0)

        elif choice == "2":
            producer.send_continuous(duration_seconds=60, rate_per_second=2)

        elif choice == "3":
            producer.send_burst(burst_size=100, burst_count=3, burst_interval=10)

        elif choice == "4":
            count = int(input("Number to send: "))
            interval = float(input("Interval in seconds: "))
            producer.send_batch(count=count, interval=interval)

        else:
            print("❌ Invalid selection")
            return

    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")

    except Exception as e:
        print(f"❌ Error occurred: {e}")

    finally:
        print("🔚 Closing producer...")
        producer.close()
        print("✅ Producer closed")


if __name__ == "__main__":
    print("🔧 Configuration:")
    print("   Kafka address: localhost:9092")
    print("   Topic: test-topic")
    print()

    main()

    print("\n💡 Tips:")
    print("   You can now run the consumer to process these messages:")
    print("   python quick_start.py")
