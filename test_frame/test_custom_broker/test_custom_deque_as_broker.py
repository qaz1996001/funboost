import json
import threading
import time
from collections import deque
from funboost import register_custom_broker, AbstractConsumer, AbstractPublisher
from funboost import boost,ConcurrentModeEnum,BrokerEnum

"""
This file demonstrates adding a custom broker type using Python's deque as an in-memory
message queue. This is purely to show how to extend custom brokers.

This approach can also be used in a subclass to override the AbstractConsumer base class logic,
e.g. if you want to insert results into MySQL after task execution or do more fine-grained
customization, you can skip the recommended decorator stacking and override methods directly in the class.
"""

queue_name__deque_map = {}


class DequePublisher(AbstractPublisher):
    def __init__(self, *args, **kwargs):
        print('This class can override any method of AbstractPublisher, but must implement: _publish_impl clear  get_message_count  close ')
        super().__init__(*args, **kwargs)
        if self.queue_name not in queue_name__deque_map:
            queue_name__deque_map[self.queue_name] = deque()
        self.msg_deque: deque = queue_name__deque_map[self.queue_name]

    def _publish_impl(self, msg: str):
        self.msg_deque.append(msg)

    def clear(self):
        self.msg_deque.clear()

    def get_message_count(self):
        return len(self.msg_deque)

    def close(self):
        pass


class DequeConsumer(AbstractConsumer):
    def __init__(self, *args, **kwargs):
        print('This class can override any method of AbstractConsumer, but must implement: _dispatch_task  _confirm_consume  _requeue ')
        super().__init__(*args, **kwargs)
        if self.queue_name not in queue_name__deque_map:
            queue_name__deque_map[self.queue_name] = deque()
        self.msg_deque: deque = queue_name__deque_map[self.queue_name]

    def _dispatch_task(self):
        while True:
            try:
                task_str = self.msg_deque.popleft()
            except IndexError:  # indicates the deque is empty
                time.sleep(0.01)
                continue
            kw = {'body': json.loads(task_str)}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # Not demonstrating ack consumption for list-based broker here

    def _requeue(self, kw):
        self.msg_deque.append(json.dumps(kw['body']))


BrokerEnum.BROKER_KIND_DEQUE = 102
register_custom_broker(BrokerEnum.BROKER_KIND_DEQUE, DequePublisher, DequeConsumer)  # Core: this registers user-written classes with the framework so it can use them automatically, without modifying framework source code.


@boost('test_list_queue', broker_kind=BrokerEnum.BROKER_KIND_DEQUE, qps=0, log_level=20,concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,concurrent_num=1,
       )
def f(x):
    if x % 10000 == 0:
        print(x)


if __name__ == '__main__':
    for i in range(1000):
        f.push(i)
    print(f.publisher.get_message_count())
    f.consume()

