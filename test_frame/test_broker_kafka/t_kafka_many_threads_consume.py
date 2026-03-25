


"""
Implement a kafka consumer class from scratch.

Supports setting num_threads to a high number, which can far exceed the number of partitions.
callback_func is a user-supplied custom function that needs to be automatically executed
in a thread pool of size num_threads.

Requirements:
Kill -9 and restart the program at any time, ensuring no messages are lost or skipped.

For example, the following scenario must be avoided:
Message processing time is random, e.g. msg1 takes 100 seconds, msg2 takes 30 seconds, msg3 takes 10 seconds.
If msg3 commits its offset, and the program is suddenly restarted,
msg1 and msg2 can no longer be consumed again.


"""

class KafkaManyThreadsConsumer:
    def __init__(self, kafka_broker_address, topic, group_id, num_threads=100, callback_func=None):
        pass
