from funboost import boost, BrokerEnum,BoosterParams,ConcurrentModeEnum
import datetime
import logging

@boost(BoosterParams(queue_name='test_queue_funboost01', 
                     broker_kind=BrokerEnum.REDIS,log_level=logging.INFO,
                     concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
                     )
                     )
def print_number(i):
    if  i % 1000 == 0:
        print(f"{datetime.datetime.now()} current number is: {i}")
    return i  # Return result for easy viewing of task execution status


if __name__ == '__main__':
    print_number.consume()


'''

Tested on win11 + python3.9 + funboost + redis middleware + amd r7 5800h cpu + single-thread concurrency mode

funboost consumption performance test results:

funboost consumes 1000 messages on average every 0.07 seconds, completing 100,000 messages within 7 seconds, capable of consuming 14,000 messages per second

'''