from funboost import register_custom_broker
from funboost import boost, FunctionResultStatus
from funboost.consumers.redis_consumer_simple import RedisConsumer
from funboost.publishers.redis_publisher_simple import RedisPublisher

"""
This file demonstrates adding a custom broker type and shows how to use redis to implement
a last-in-first-out queue -- consumption always pulls the most recently published message
rather than prioritizing the earliest published message.
lpush + lpop or rpush + rpop will consume the latest published message; lpush + rpop or
rpush + lpop will consume the earliest published message (the framework's built-in behavior
is to consume the earliest published message).

This approach can also be used in a subclass to override the AbstractConsumer base class logic,
e.g. if you want to insert results into MySQL after task execution or do more fine-grained
customization, you can skip the recommended decorator stacking and override methods directly in the class.
"""


class RedisConsumeLatestPublisher(RedisPublisher):
    def _publish_impl(self, msg):
        self.redis_db_frame.lpush(self._queue_name, msg)


class RedisConsumeLatestConsumer(RedisConsumer):
    pass


BROKER_KIND_REDIS_CONSUME_LATEST = 103
register_custom_broker(BROKER_KIND_REDIS_CONSUME_LATEST, RedisConsumeLatestPublisher, RedisConsumeLatestConsumer)  # Core: this registers user-written classes with the framework so the framework can use them automatically, without modifying the framework's source code.


@boost('test_list_queue', broker_kind=BROKER_KIND_REDIS_CONSUME_LATEST, qps=10, )
def f(x):
    print(x * 10)


if __name__ == '__main__':
    f.clear()
    for i in range(50):
        f.push(i)
    print(f.publisher.get_message_count())
    f.consume()
