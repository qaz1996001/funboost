from funboost import register_custom_broker
from funboost import boost, FunctionResultStatus, BoosterParams
from funboost.consumers.redis_consumer_simple import RedisConsumer
from funboost.publishers.redis_publisher_simple import RedisPublisher

"""
This file demonstrates how to add a custom broker type, showing how to use Redis to implement
a LIFO (Last-In-First-Out) queue, where consumption always pulls the most recently published message
rather than prioritizing the earliest published message.
lpush + lpop or rpush + rpop will consume the most recently published message,
while lpush + rpop or rpush + lpop will consume the earliest published message first
(the framework's built-in behavior currently consumes the earliest published message).

This approach can also be used to override the AbstractConsumer base class logic in subclasses.
For example, if you want to insert results into MySQL after task execution or make more fine-grained
customizations, you can directly override methods in the class instead of using the recommended
decorator stacking approach.

"""


class RedisConsumeLatestPublisher(RedisPublisher):
    def _publish_impl(self, msg):
        self.redis_db_frame.lpush(self._queue_name, msg)


class RedisConsumeLatestConsumer(RedisConsumer):
    pass


BROKER_KIND_REDIS_CONSUME_LATEST = 'BROKER_KIND_REDIS_CONSUME_LATEST'
register_custom_broker(BROKER_KIND_REDIS_CONSUME_LATEST, RedisConsumeLatestPublisher, RedisConsumeLatestConsumer)  # Core: this registers user-written classes into the framework, allowing the framework to automatically use user classes without modifying the framework's source code.

if __name__ == '__main__':
    @boost(boost_params=BoosterParams(queue_name='test_list_queue2', broker_kind=BROKER_KIND_REDIS_CONSUME_LATEST, qps=10, ))
    def f(x):
        print(x * 10)


    f.clear()
    for i in range(50):
        f.push(i)
    print(f.publisher.get_message_count())
    f.consume()  # You can see that consumption starts from the most recently published message.
