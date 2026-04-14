import threading
import json
import time
import redis
from collections import defaultdict
from funboost import boost, BrokerEnum, BoosterParams, EmptyConsumer, EmptyPublisher,funboost_config_deafult


'''
Uses Redis as the message queue middleware implementation.
By specifying consumer_override_cls and publisher_override_cls as user-defined classes, you can add new message queue types.
'''


class MyRedisConsumer(EmptyConsumer):
    def custom_init(self):
        print(funboost_config_deafult.BrokerConnConfig.REDIS_URL)
        self.redis_client = redis.from_url(funboost_config_deafult.BrokerConnConfig.REDIS_URL)

    def _dispatch_task(self):
        while True:
            try:
                _, msg_bytes = self.redis_client.brpop(self.queue_name)
                msg = msg_bytes.decode('utf-8')
                self._submit_task({'body': msg})
            except redis.exceptions.ConnectionError as e:
                print(f"Redis connection error: {e}")
                time.sleep(5)  # Wait before retrying after a connection error
            except Exception as e:
                print(f"Error during message consumption: {e}")
                time.sleep(1)

    def _confirm_consume(self, kw):
        """ For demonstration purposes, kept simple; does not implement consumption acknowledgment. """
        pass

    def _requeue(self, kw):
        self.redis_client.lpush(self.queue_name, kw['body'])

class MyRedisPublisher(EmptyPublisher):
    def custom_init(self):
        self.redis_client = redis.from_url(funboost_config_deafult.BrokerConnConfig.REDIS_URL)

    def _publish_impl(self, msg: str):
        self.redis_client.lpush(self.queue_name, msg)

    def clear(self):
        self.redis_client.delete(self.queue_name)

    def get_message_count(self):
        return self.redis_client.llen(self.queue_name)

    def close(self):
        self.redis_client.connection_pool.disconnect()

'''
When completely customizing and adding new middleware, it is recommended to set broker_kind to BrokerEnum.EMPTY.
'''

@boost(BoosterParams(queue_name='test_define_redis_queue',
                     broker_kind=BrokerEnum.REDIS,  # Using Redis as middleware
                     concurrent_num=1, consumer_override_cls=MyRedisConsumer, publisher_override_cls=MyRedisPublisher,
                     is_show_message_get_from_broker=True))
def cost_long_time_fun(x):
    print(f'start {x}')
    time.sleep(2)
    print(f'end {x}')

if __name__ == '__main__':
    for i in range(10):
        cost_long_time_fun.push(i)
    cost_long_time_fun.consume()
