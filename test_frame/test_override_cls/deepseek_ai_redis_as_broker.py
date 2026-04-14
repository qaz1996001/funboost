import time
import redis
from funboost import boost, BrokerEnum, BoosterParams, EmptyConsumer, EmptyPublisher, funboost_config_deafult

'''
Uses Redis as the message queue middleware implementation.
By specifying consumer_override_cls and publisher_override_cls as user-defined classes, you can add new message queue types.
'''

class MyRedisConsumer(EmptyConsumer):
    def custom_init(self):
        """Initialize Redis client"""
        print(funboost_config_deafult.BrokerConnConfig.REDIS_URL)
        self.redis_client = redis.from_url(funboost_config_deafult.BrokerConnConfig.REDIS_URL)

    def _dispatch_task(self):
        """Consume messages from the Redis queue"""
        while True:
            try:
                # Use brpop to block and get messages from the queue
                _, msg_bytes = self.redis_client.brpop(self.queue_name)
                msg = msg_bytes.decode('utf-8')
                # Submit task to funboost for processing
                self._submit_task({'body': msg})
            except redis.exceptions.ConnectionError as e:
                print(f"Redis connection error: {e}")
                time.sleep(5)  # Wait before retrying after a connection error
            except Exception as e:
                print(f"Error during message consumption: {e}")
                time.sleep(1)

    def _confirm_consume(self, kw):
        """Acknowledge consumption (not implemented here, for demonstration)"""
        pass

    def _requeue(self, kw):
        """Put the message back into the queue"""
        self.redis_client.lpush(self.queue_name, kw['body'])


class MyRedisPublisher(EmptyPublisher):
    def custom_init(self):
        """Initialize Redis client"""
        self.redis_client = redis.from_url(funboost_config_deafult.BrokerConnConfig.REDIS_URL)

    def _publish_impl(self, msg: str):
        """Publish message to Redis queue"""
        self.redis_client.lpush(self.queue_name, msg)

    def clear(self):
        """Clear the queue"""
        self.redis_client.delete(self.queue_name)

    def get_message_count(self):
        """Get the number of messages in the queue"""
        return self.redis_client.llen(self.queue_name)

    def close(self):
        """Close Redis connection"""
        self.redis_client.connection_pool.disconnect()


'''
When completely customizing and adding new middleware, it is recommended to set broker_kind to BrokerEnum.EMPTY.
'''

@boost(BoosterParams(
    queue_name='test_define_redis_queue',  # Queue name
    broker_kind=BrokerEnum.REDIS,  # Using Redis as middleware
    concurrent_num=1,  # Concurrency count
    consumer_override_cls=MyRedisConsumer,  # Custom consumer class
    publisher_override_cls=MyRedisPublisher,  # Custom publisher class
    is_show_message_get_from_broker=True  # Show messages fetched from middleware
))
def cost_long_time_fun(x):
    """Example of a time-consuming function"""
    print(f'Starting to process {x}')
    time.sleep(2)  # Simulate time-consuming operation
    print(f'Finished processing {x}')


if __name__ == '__main__':
    # Push 10 tasks to the queue
    for i in range(10):
        cost_long_time_fun.push(i)
    # Start consuming tasks from the queue
    cost_long_time_fun.consume()
