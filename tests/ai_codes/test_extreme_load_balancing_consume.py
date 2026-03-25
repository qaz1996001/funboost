import logging
import time
from funboost import boost, BrokerEnum, BoosterParams, ctrl_c_recv, ConcurrentModeEnum

# Extreme consumer load balancing example
@boost(BoosterParams(
    queue_name='test_extreme_load_balancing_queue',
    broker_kind=BrokerEnum.REDIS_ACK_ABLE, # Using REDIS_ACK_ABLE as an example; other brokers work the same way
    log_level=logging.INFO,

    # Key point 1: Set concurrent mode to SINGLE_THREAD
    # This avoids using a thread pool, which means no internal buffer queue inside the thread pool
    concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,

    # Key point 2: Set broker-specific config pull_msg_batch_size to 1
    # By default many brokers (e.g. Redis) pull messages in batches (e.g. 100) into memory
    # Setting it to 1 ensures only one message is pulled at a time; the next is pulled after processing
    broker_exclusive_config={'pull_msg_batch_size': 1},
))
def extreme_load_balancing_consumer(x):
    print(f"Consumer processing: {x}")
    time.sleep(1) # Simulate a time-consuming task

if __name__ == '__main__':
    # Start consuming
    extreme_load_balancing_consumer.consume()
    ctrl_c_recv()
