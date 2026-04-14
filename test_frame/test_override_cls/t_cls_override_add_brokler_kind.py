import threading
import json
import time
from collections import defaultdict
from funboost import boost, BrokerEnum, BoosterParams, EmptyConsumer, EmptyPublisher

queue_name__list_map = defaultdict(list)
list_lock = threading.Lock()

'''
Uses a Python list as the message queue middleware implementation.
By specifying consumer_override_cls and publisher_override_cls as user-defined classes, you can add new message queue types.
'''


class MyListConsumer(EmptyConsumer):
    def custom_init(self):
        self.list: list = queue_name__list_map[self.queue_name]

    def _dispatch_task(self):
        while True:
            try:
                with list_lock:
                    msg = self.list.pop()
                self._submit_task({'body': msg})
            except IndexError:
                time.sleep(1)

    def _confirm_consume(self, kw):
        """ For demonstration purposes, kept simple; does not implement consumption acknowledgment. """
        pass

    def _requeue(self, kw):
        with list_lock:
            self.list.append(kw['body'])


class MyListPublisher(EmptyPublisher):
    def custom_init(self):
        self.list: list = queue_name__list_map[self.queue_name]

    def _publish_impl(self, msg: str):
        with list_lock:
            self.list.append(msg)

    def clear(self):
        with list_lock:
            self.list.clear()

    def get_message_count(self):
        with list_lock:
            return len(self.list)

    def close(self):
        pass


'''
When completely customizing and adding new middleware, it is recommended to set broker_kind to BrokerEnum.EMPTY.
'''


@boost(BoosterParams(queue_name='test_define_list_queue',
                     broker_kind=BrokerEnum.EMPTY,  # When completely customizing new middleware, set broker_kind to BrokerEnum.EMPTY.
                     concurrent_num=1, consumer_override_cls=MyListConsumer, publisher_override_cls=MyListPublisher,
                     is_show_message_get_from_broker=True))
def cost_long_time_fun(x):
    print(f'start {x}')
    time.sleep(20)
    print(f'end {x}')


if __name__ == '__main__':

    for i in range(100):
        cost_long_time_fun.push(i)
    cost_long_time_fun.consume()
