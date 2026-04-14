from funboost import get_consumer, BrokerEnum


def add(a, b):
    print(a + b)


# Non-decorator approach; there is one additional parameter — the consuming_function value must be specified manually.
consumer = get_consumer('queue_test_f01', consuming_function=add, qps=0.2, broker_kind=BrokerEnum.REDIS_ACK_ABLE)

if __name__ == '__main__':
    for i in range(10, 20):
        consumer.publisher_of_same_queue.publish(dict(a=i, b=i * 2))  # consumer.publisher_of_same_queue.publish  publish a task
    consumer.start_consuming_message()  # Use consumer.start_consuming_message to consume tasks