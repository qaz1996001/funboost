import json
import os
import threading
import time

from funboost import register_custom_broker, AbstractConsumer, AbstractPublisher,BrokerEnum
from funboost import boost

"""
This file demonstrates adding a custom broker type using a Python list as an in-memory
message queue. This is purely to demonstrate how to extend custom brokers; using a list as
a real message queue broker is not recommended.

This approach can also be used to override AbstractConsumer base class logic, e.g. if you
want to insert results into MySQL after task execution, you can skip the recommended
decorator stacking and override methods directly in the class.
"""

queue_name__list_map = {}

list_operation_lock = threading.Lock()  # list type is not thread-safe; queue.Queue is, but list is not.


class ListPublisher(AbstractPublisher):
    def __init__(self, *args, **kwargs):
        print('This class can override any method of AbstractPublisher, but must implement: _publish_impl clear  get_message_count  close ')
        super().__init__(*args, **kwargs)
        if self.queue_name not in queue_name__list_map:
            queue_name__list_map[self.queue_name] = []
        self.msg_list: list = queue_name__list_map[self.queue_name]

    def _publish_impl(self, msg: str):
        self.msg_list.append(msg)

    def clear(self):
        self.msg_list.clear()

    def get_message_count(self):
        return len(self.msg_list)

    def close(self):
        pass


class ListConsumer(AbstractConsumer):
    def __init__(self, *args, **kwargs):
        print('This class can override any method of AbstractConsumer, but must implement: _dispatch_task  _confirm_consume  _requeue ')
        super().__init__(*args, **kwargs)
        if self.queue_name not in queue_name__list_map:
            queue_name__list_map[self.queue_name] = []
        self.msg_list: list = queue_name__list_map[self.queue_name]

    def _dispatch_task(self):
        while True:
            try:
                task_str = self.msg_list.pop(-1)  # pop(0) 消耗的性能更高
            except IndexError:  # indicates the list is empty
                time.sleep(0.1)
                continue
            kw = {'body': json.loads(task_str)}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # Not demonstrating ack consumption for list-based broker here

    def _requeue(self, kw):
        self.msg_list.append(json.dumps(kw['body']))


BROKER_KIND_LIST = 101
register_custom_broker(BROKER_KIND_LIST, ListPublisher, ListConsumer)  # Core: this registers user-written classes with the framework so it can use them automatically, without modifying framework source code.


@boost('test_list_queue', broker_kind=BROKER_KIND_LIST, qps=0.5,concurrent_num=2)
def f(x):
    print(os.getpid())
    print(x * 10)


if __name__ == '__main__':
    for i in range(5000):
        f.push(i)
    print(f.publisher.get_message_count())
    f.multi_process_consume(10)
