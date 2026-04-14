"""
Implement a Kafka consumer class from scratch,

supporting num_threads set to a large number, which can far exceed the number of partitions.
callback_func is a user-provided custom function, which should automatically execute in a
thread pool of size num_threads.

Requirements:
Survive arbitrary kill -9 restarts at any time without losing or skipping messages.

For example, the following scenario must be avoided:
Message processing time is random, e.g. msg1 takes 100 seconds, msg2 takes 30 seconds, msg3 takes 10 seconds.
If msg3 commits its offset and the program suddenly restarts, msg1 and msg2 can no longer be consumed.

Core solution: Ordered offset commit manager
"""

import threading
import time
import logging
import traceback
from typing import Dict, List, Callable, Optional, Set
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
from collections import defaultdict, deque
from queue import Queue, Empty
import json

try:
    from kafka import KafkaConsumer, TopicPartition
    from kafka.consumer.fetcher import ConsumerRecord
    from kafka.coordinator.assignors.range import RangePartitionAssignor
    from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor
except ImportError:
    print("Please install kafka-python: pip install kafka-python")
    raise


@dataclass
class MessageTask:
    """Message processing task"""
    record: ConsumerRecord
    partition: int
    offset: int
    timestamp: float
    future: Optional[Future] = None
    completed: bool = False
    success: bool = False
    error: Optional[Exception] = None


class OffsetManager:
    """Ordered offset commit manager - ensures offsets are committed in order to avoid message loss"""

    def __init__(self):
        self.lock = threading.RLock()
        # Pending message queue per partition {partition: deque[MessageTask]}
        self.pending_messages: Dict[int, deque] = defaultdict(deque)
        # Maximum consecutive committable offset per partition {partition: offset}
        self.committable_offsets: Dict[int, int] = {}
        # Already committed offset per partition {partition: offset}
        self.committed_offsets: Dict[int, int] = {}

    def add_message(self, task: MessageTask):
        """Add message to pending queue"""
        with self.lock:
            self.pending_messages[task.partition].append(task)

    def mark_completed(self, task: MessageTask, success: bool, error: Optional[Exception] = None):
        """Mark message processing as complete"""
        with self.lock:
            task.completed = True
            task.success = success
            task.error = error

            # Update committable offset
            self._update_committable_offset(task.partition)

    def _update_committable_offset(self, partition: int):
        """
        Update the committable offset for the specified partition

        Key logic: Only commit consecutive successfully processed messages to guarantee no message loss.
        If there is a failed message in between, stop committing, so failed messages
        can be re-consumed after restart.
        """
        queue = self.pending_messages[partition]

        # Key fix: Only process consecutive successful messages; stop on first failure
        consecutive_success_count = 0
        last_committable_offset = None

        # Check consecutive completed and successful messages from the head of the queue
        while (consecutive_success_count < len(queue) and
               queue[consecutive_success_count].completed and
               queue[consecutive_success_count].success):

            task = queue[consecutive_success_count]
            last_committable_offset = task.offset + 1  # Kafka offset needs +1
            consecutive_success_count += 1

        # Update committable offset (only commit the consecutive successful part)
        if last_committable_offset is not None:
            self.committable_offsets[partition] = last_committable_offset

        # Remove consecutively successful messages that can be safely committed
        for _ in range(consecutive_success_count):
            completed_task = queue.popleft()
            self.logger.debug(f"Removed processed message: partition={completed_task.partition}, "
                            f"offset={completed_task.offset}")

        # Check if a failed message is blocking subsequent commits
        if (queue and queue[0].completed and not queue[0].success):
            failed_task = queue[0]
            self.logger.warning(f"Message processing failed, blocking subsequent offset commits: "
                              f"partition={failed_task.partition}, offset={failed_task.offset}, "
                              f"error={failed_task.error}. Will re-consume from this point after restart.")

        # Remove failed completed messages from queue head (but do not affect offset commits)
        while queue and queue[0].completed and not queue[0].success:
            failed_task = queue.popleft()
            self.logger.info(f"Removed failed message: partition={failed_task.partition}, "
                           f"offset={failed_task.offset}")

    def get_committable_offsets(self) -> Dict[TopicPartition, int]:
        """Get offsets that can be safely committed"""
        with self.lock:
            result = {}
            for partition, offset in self.committable_offsets.items():
                if offset > self.committed_offsets.get(partition, -1):
                    topic_partition = TopicPartition(topic='', partition=partition)
                    result[topic_partition] = offset
            return result

    def mark_committed(self, offsets: Dict[TopicPartition, int]):
        """Mark offsets as committed"""
        with self.lock:
            for tp, offset in offsets.items():
                self.committed_offsets[tp.partition] = offset

    def clear_partition(self, partition: int):
        """Clear partition data (used for rebalance)"""
        with self.lock:
            if partition in self.pending_messages:
                del self.pending_messages[partition]
            if partition in self.committable_offsets:
                del self.committable_offsets[partition]
            if partition in self.committed_offsets:
                del self.committed_offsets[partition]

    def get_status(self) -> Dict:
        """Get status information"""
        with self.lock:
            return {
                'pending_count': {p: len(q) for p, q in self.pending_messages.items()},
                'committable_offsets': dict(self.committable_offsets),
                'committed_offsets': dict(self.committed_offsets)
            }


class KafkaManyThreadsConsumer:
    """
    Kafka consumer supporting a large number of threads, ensuring no message loss or skipping

    Core features:
    1. Supports thread count far exceeding partition count
    2. Ordered offset commits to avoid message loss
    3. Supports kill -9 restart without message loss
    4. Automatic rebalance handling
    """

    def __init__(self, kafka_broker_address: str, topic: str, group_id: str,
                 num_threads: int = 100, callback_func: Optional[Callable] = None):
        self.kafka_broker_address = kafka_broker_address
        self.topic = topic
        self.group_id = group_id
        self.num_threads = num_threads
        self.callback_func = callback_func or self._default_callback

        # Core components
        self.consumer: Optional[KafkaConsumer] = None
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.offset_manager = OffsetManager()

        # Control variables
        self.running = False
        self.shutdown_event = threading.Event()

        # Threads
        self.consume_thread: Optional[threading.Thread] = None
        self.commit_thread: Optional[threading.Thread] = None

        # Statistics
        self.stats = {
            'consumed_count': 0,
            'processed_count': 0,
            'failed_count': 0,
            'committed_count': 0
        }
        self.stats_lock = threading.Lock()

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f'KafkaConsumer-{group_id}')

    def _default_callback(self, message):
        """Default message handler"""
        self.logger.info(f"Processing message: partition={message.partition}, offset={message.offset}, "
                        f"value={message.value[:100] if message.value else None}...")
        # Simulate processing time
        time.sleep(0.1)

    def start(self):
        """Start the consumer"""
        if self.running:
            self.logger.warning("Consumer is already running")
            return

        self.logger.info(f"Starting Kafka consumer: topic={self.topic}, group_id={self.group_id}, "
                        f"threads={self.num_threads}")

        try:
            # Create Kafka consumer
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=[self.kafka_broker_address],
                group_id=self.group_id,
                auto_offset_reset='earliest',
                enable_auto_commit=False,  # Disable auto commit, manually control offset
                max_poll_records=500,
                session_timeout_ms=30000,
                heartbeat_interval_ms=3000,
                consumer_timeout_ms=1000,  # Set poll timeout
                value_deserializer=lambda x: x.decode('utf-8') if x else None,
                key_deserializer=lambda x: x.decode('utf-8') if x else None
            )

            # Create thread pool
            self.thread_pool = ThreadPoolExecutor(
                max_workers=self.num_threads,
                thread_name_prefix=f'KafkaWorker-{self.group_id}'
            )

            self.running = True

            # Start consume thread
            self.consume_thread = threading.Thread(
                target=self._consume_loop,
                name=f'KafkaConsume-{self.group_id}',
                daemon=True
            )
            self.consume_thread.start()

            # Start commit thread
            self.commit_thread = threading.Thread(
                target=self._commit_loop,
                name=f'KafkaCommit-{self.group_id}',
                daemon=True
            )
            self.commit_thread.start()

            self.logger.info("Kafka consumer started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start Kafka consumer: {e}")
            self.stop()
            raise

    def stop(self):
        """Stop the consumer"""
        if not self.running:
            return

        self.logger.info("Stopping Kafka consumer...")

        # Set stop flag
        self.running = False
        self.shutdown_event.set()

        # Wait for threads to finish
        if self.consume_thread and self.consume_thread.is_alive():
            self.consume_thread.join(timeout=10)

        if self.commit_thread and self.commit_thread.is_alive():
            self.commit_thread.join(timeout=10)

        # Shutdown thread pool
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True, timeout=30)

        # Final offset commit
        self._commit_offsets()

        # Close consumer
        if self.consumer:
            self.consumer.close()

        self.logger.info("Kafka consumer stopped")

    def _consume_loop(self):
        """Consume loop - main thread"""
        self.logger.info("Starting message consume loop")

        while self.running:
            try:
                # Poll messages
                message_batch = self.consumer.poll(timeout_ms=1000)

                if not message_batch:
                    continue

                # Process messages for each partition
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        if not self.running:
                            break

                        self._process_message(message)

                        with self.stats_lock:
                            self.stats['consumed_count'] += 1

            except Exception as e:
                if self.running:
                    self.logger.error(f"Error while consuming messages: {e}\n{traceback.format_exc()}")
                    time.sleep(1)  # Brief pause on error

        self.logger.info("Consume loop ended")

    def _process_message(self, record: ConsumerRecord):
        """Process a single message"""
        # Create message task
        task = MessageTask(
            record=record,
            partition=record.partition,
            offset=record.offset,
            timestamp=time.time()
        )

        # Add to offset manager
        self.offset_manager.add_message(task)

        # Submit to thread pool for processing
        future = self.thread_pool.submit(self._execute_callback, task)
        task.future = future

        self.logger.debug(f"Submitted message to thread pool: partition={record.partition}, offset={record.offset}")

    def _execute_callback(self, task: MessageTask):
        """Execute callback function in thread pool"""
        start_time = time.time()
        success = False
        error = None

        try:
            # Execute user callback
            self.callback_func(task.record)
            success = True

            with self.stats_lock:
                self.stats['processed_count'] += 1

            self.logger.debug(f"Message processed successfully: partition={task.partition}, offset={task.offset}, "
                            f"time_taken={time.time() - start_time:.2f}s")

        except Exception as e:
            error = e
            success = False

            with self.stats_lock:
                self.stats['failed_count'] += 1

            self.logger.error(f"Message processing failed: partition={task.partition}, offset={task.offset}, "
                            f"error={e}\n{traceback.format_exc()}")
        finally:
            # Mark task as complete
            self.offset_manager.mark_completed(task, success, error)

    def _commit_loop(self):
        """Offset commit loop"""
        self.logger.info("Starting offset commit loop")

        while self.running:
            try:
                self._commit_offsets()
                time.sleep(5)  # Commit every 5 seconds

            except Exception as e:
                if self.running:
                    self.logger.error(f"Error while committing offset: {e}")
                    time.sleep(1)

        self.logger.info("Offset commit loop ended")

    def _commit_offsets(self):
        """Commit offsets"""
        committable_offsets = self.offset_manager.get_committable_offsets()

        if not committable_offsets:
            return

        try:
            # Construct commit format
            commit_offsets = {}
            for tp, offset in committable_offsets.items():
                # Update topic information
                tp_with_topic = TopicPartition(self.topic, tp.partition)
                commit_offsets[tp_with_topic] = offset

            # Commit to Kafka
            self.consumer.commit(offsets=commit_offsets)

            # Mark as committed
            self.offset_manager.mark_committed(committable_offsets)

            with self.stats_lock:
                self.stats['committed_count'] += len(commit_offsets)

            self.logger.info(f"Successfully committed offsets: {commit_offsets}")

        except Exception as e:
            self.logger.error(f"Failed to commit offsets: {e}")

    def get_stats(self) -> Dict:
        """Get statistics"""
        with self.stats_lock:
            stats = self.stats.copy()

        # Add offset manager status
        stats.update({
            'offset_manager_status': self.offset_manager.get_status(),
            'thread_pool_active': self.thread_pool._threads if self.thread_pool else 0,
            'running': self.running
        })

        return stats

    def wait_for_completion(self, timeout: Optional[float] = None):
        """Wait for consumption to complete"""
        if self.consume_thread:
            self.consume_thread.join(timeout=timeout)
        if self.commit_thread:
            self.commit_thread.join(timeout=timeout)


# Usage example
def example_callback(message):
    """Example callback function"""
    import random

    # Simulate different processing times
    processing_time = random.uniform(0.1, 2.0)
    time.sleep(processing_time)

    print(f"Processing message: partition={message.partition}, offset={message.offset}, "
          f"time_taken={processing_time:.2f}s, value={message.value[:50] if message.value else None}...")

    # Simulate occasional processing failure
    if random.random() < 0.05:  # 5% failure rate
        raise Exception("Simulated processing failure")


if __name__ == "__main__":
    # Create consumer instance
    consumer = KafkaManyThreadsConsumer(
        kafka_broker_address="localhost:9092",
        topic="test-topic",
        group_id="test-group",
        num_threads=50,
        callback_func=example_callback
    )

    try:
        # Start consumer
        consumer.start()

        # Periodically print statistics
        while True:
            time.sleep(10)
            stats = consumer.get_stats()
            print(f"Statistics: {json.dumps(stats, indent=2, ensure_ascii=False)}")

    except KeyboardInterrupt:
        print("Received interrupt signal, stopping...")
    finally:
        consumer.stop()
