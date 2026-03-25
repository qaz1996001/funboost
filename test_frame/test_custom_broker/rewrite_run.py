from funboost import register_custom_broker
from funboost import boost, FunctionResultStatus
from funboost.consumers.redis_consumer_simple import RedisConsumer as SimpleRedisConsumer
from funboost.publishers.redis_publisher_simple import RedisPublisher as SimpleRedisPublisher

"""
Demonstrates overriding the most critical _run method. Inside _run, you can control the
function execution logic. The _run method is the most critical method in the consumer.
"""


class MyRedisPublisher(SimpleRedisPublisher):
    pass


class MyRedisConsumer(SimpleRedisConsumer):
    def _run(self, kw: dict, ):
        self.logger.warning(f'kw: {kw}')
        print(self._get_priority_conf)
        super()._run(kw)   # For finer control, copy all code from AbstractConsumer's _run method here and modify the logic directly


BROKER_KIND_MY_REEDIS = 104
register_custom_broker(BROKER_KIND_MY_REEDIS, MyRedisPublisher, MyRedisConsumer)  # Core: this registers user-written classes with the framework so it can use them automatically, without modifying framework source code.


@boost('test_my_redis_queue', broker_kind=BROKER_KIND_MY_REEDIS, qps=1, )
def f(x):
    print(x * 10)

if __name__ == '__main__':
    for i in range(50):
        f.push(i)
    print(f.publisher.get_message_count())
    f.consume()
