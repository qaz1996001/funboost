import os
import time
from filelock import FileLock  # Use filelock library for process-safe locking
from funboost import boost, BrokerEnum, BoosterParams, EmptyConsumer, EmptyPublisher,ctrl_c_recv

class TxtFileConsumer(EmptyConsumer):
    def custom_init(self):
        """Initialize, create txt file and lock file for the queue"""
        self.file_path = f"{self.queue_name}.txt"
        self.lock_path = f"{self.queue_name}.lock"
        self.file_lock = FileLock(self.lock_path)  # Use file lock
        # Create file if it doesn't exist
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                pass

    def _dispatch_task(self):
        """Read messages from txt file and submit tasks"""
        while True:
            try:
                with self.file_lock:  # Use file lock to protect file operations
                    with open(self.file_path, 'r') as f:
                        lines = f.readlines()
                    if lines:
                        msg = lines[0].strip()
                        with open(self.file_path, 'w') as f:
                            f.writelines(lines[1:])
                        self._submit_task({'body': msg})
                    else:
                        time.sleep(0.1)
            except Exception as e:
                print(f"Error reading message: {e}")
                time.sleep(0.1)

    def _confirm_consume(self, kw):
        """Acknowledge consumption; simple implementation here"""
        pass

    def _requeue(self, kw):
        """Re-queue message"""
        with self.file_lock:
            with open(self.file_path, 'a') as f:
                f.write(f"{kw['body']}\n")

class TxtFilePublisher(EmptyPublisher):
    def custom_init(self):
        """Initialize, create txt file and lock file for the queue"""
        self.file_path = f"{self.queue_name}.txt"
        self.lock_path = f"{self.queue_name}.lock"
        self.file_lock = FileLock(self.lock_path)  # Use file lock
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                pass

    def _publish_impl(self, msg: str):
        """Publish message to txt file"""
        with self.file_lock:
            with open(self.file_path, 'a') as f:
                f.write(f"{msg}\n")

    def clear(self):
        """Clear the queue"""
        with self.file_lock:
            with open(self.file_path, 'w') as f:
                pass

    def get_message_count(self):
        """Get message count"""
        with self.file_lock:
            with open(self.file_path, 'r') as f:
                return len(f.readlines())

    def close(self):
        """Cleanup on close"""
        pass

@boost(BoosterParams(
    queue_name='test_txt_queue',
    broker_kind=BrokerEnum.EMPTY,  # Use EMPTY to indicate a fully custom broker
    concurrent_num=1,
    consumer_override_cls=TxtFileConsumer,
    publisher_override_cls=TxtFilePublisher,
    is_show_message_get_from_broker=True
))
def example_function(x):
    """Example function"""
    print(f'Starting to process {x}')
    time.sleep(1)  # Simulate time-consuming operation
    print(f'Finished processing {x}')
    return x

if __name__ == '__main__':
    # Push 10 messages to the queue
    for i in range(10):
        example_function.push(i)

    # Start consuming messages from the queue
    example_function.consume()
    ctrl_c_recv()
