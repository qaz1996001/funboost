"""
This is used to test whether tasks are lost when using Redis as the middleware
and the code is arbitrarily shut down.
"""
import os
import time

from funboost import boost,BrokerEnum,FunctionResultStatusPersistanceConfig
from funboost.utils.redis_manager import RedisMixin
import multiprocessing

@boost('test_cost_long_time_fun_queue8889', broker_kind=BrokerEnum.REDIS_BRPOP_LPUSH,
       )
def cost_long_time_fun(x):
   print(f'function started hello {x}')
   time.sleep(120)
   print('function fully finished')

if __name__ == '__main__':
    #  cost_long_time_fun.push(666)
    cost_long_time_fun.consume()
    # cost_long_time_fun.multi_process_consume(4)