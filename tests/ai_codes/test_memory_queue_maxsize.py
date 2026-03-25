# -*- coding: utf-8 -*-
"""
Test the bounded queue size configuration of MEMORY_QUEUE

Set the maximum queue capacity via broker_exclusive_config={'maxsize': N}
"""
import threading
import time
from funboost import boost, BrokerEnum, BoosterParams, run_forever

# Test 1: Use bounded queue with maxsize=3
@boost(BoosterParams(
    queue_name='test_memory_queue_maxsize',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=1,  # Use single thread for easier observation of blocking effect
    log_level=20,
    broker_exclusive_config={'maxsize': 3},  # Set bounded queue, max 3 messages
))
def process_task(num):
    print(f"Processing task: {num}, current time: {time.strftime('%H:%M:%S')}")
    time.sleep(1)  # Simulate time-consuming operation
    return num * 2


def test_bounded_queue():
    """Test blocking effect of bounded queue"""
    print("=" * 50)
    print("Test bounded queue (maxsize=3)")
    print("=" * 50)

    # Get queue info
    from funboost.queues.memory_queues_map import PythonQueues

    # Publish some messages first (will create the queue)
    for i in range(3):
        process_task.pub({'num': i})
        print(f"Published message {i}, queue size: {process_task.publisher.get_message_count()}")

    # Queue should be full now
    queue_obj = PythonQueues.get_queue('test_memory_queue_maxsize')
    print(f"Queue maxsize: {queue_obj.maxsize}")
    print(f"Current queue size: {queue_obj.qsize()}")
    print(f"Queue is full: {queue_obj.full()}")

    # Try to publish a 4th message in another thread; it should block
    def publish_one_more():
        print(f"Trying to publish 4th message... (should block until a slot is available)")
        start_time = time.time()
        process_task.pub({'num': 100})
        elapsed = time.time() - start_time
        print(f"4th message published successfully, waited {elapsed:.2f} seconds")

    # Start thread to publish 4th message
    t = threading.Thread(target=publish_one_more)
    t.start()

    # Start consumer to consume messages from queue
    print("\nStarting consumer...")
    process_task.consume()

    # Wait for publish thread to complete
    t.join(timeout=10)

    print("\nTest complete!")


# Test 2: Use default unbounded queue (maxsize=0)
@boost(BoosterParams(
    queue_name='test_memory_queue_unbounded',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
    log_level=20,
    # maxsize not specified, defaults to 0 (unbounded queue)
))
def process_unbounded_task(num):
    print(f"Unbounded queue task: {num}")
    return num


def test_unbounded_queue():
    """Test default unbounded queue"""
    print("=" * 50)
    print("Test default unbounded queue (maxsize=0)")
    print("=" * 50)

    # Rapidly publish many messages without blocking
    for i in range(100):
        process_unbounded_task.pub({'num': i})

    print(f"Successfully published 100 messages, queue size: {process_unbounded_task.publisher.get_message_count()}")

    from funboost.queues.memory_queues_map import PythonQueues
    queue_obj = PythonQueues.get_queue('test_memory_queue_unbounded')
    print(f"Queue maxsize: {queue_obj.maxsize}")
    print(f"Queue is full: {queue_obj.full()}")  # Unbounded queue is never full


if __name__ == '__main__':
    # Test unbounded queue first
    test_unbounded_queue()

    print("\n" + "=" * 70 + "\n")

    # Then test bounded queue
    test_bounded_queue()
