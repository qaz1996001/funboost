

from funboost import boost, BoosterParams,BrokerEnum
import logging

@boost(BoosterParams(
    queue_name='test_sqlite_queue8',
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    # qps=10,
    concurrent_num=3,
    log_level=logging.INFO,
   
))
def process_message(x, y):
    """Process WebSocket message"""
    result = x + y
    if x % 100 == 0:
        print(f"Processing message: {x} + {y} = {result}")
    return result



if __name__ == '__main__':
    process_message.mp_consume(4)