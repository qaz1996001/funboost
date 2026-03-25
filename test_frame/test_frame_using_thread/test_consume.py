# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57
# import gevent.monkey;gevent.monkey.patch_all()
import time
import random

from funboost import get_consumer, AbstractConsumer
from funboost.consumers.base_consumer import ConsumersManager, FunctionResultStatusPersistanceConfig
from funboost.utils import LogManager



logger = LogManager('test_consume').get_logger_and_add_handlers()


class RandomError(Exception):
    pass


def add(a, b):
    logger.info(f'Consuming message {a} + {b}...')
    # time.sleep(random.randint(1, 3))  # Simulate blocking for 10 seconds; must use concurrency to bypass.
    if random.randint(4, 6) == 5:
        raise RandomError('Demonstrating random error')
    logger.info(f'Calculation {a} + {b} result is  {a + b}')
    return a + b


def sub(x, y):
    logger.info(f'Consuming message {x} - {y}...')
    time.sleep(4)  # Simulate blocking for 10 seconds; must use concurrency to bypass.
    if random.randint(1, 10) == 4:
        raise ValueError('4444')
    result = x - y
    logger.info(f'Calculation {x} - {y} result is  {result}')
    return result


# Just pass the consuming function name to consuming_function; it's that simple.
consumer_add = get_consumer('queue_test569', consuming_function=add, concurrent_num=50, max_retry_times=3,
                            qps=2000, log_level=10, logger_prefix='zz_platform_consume',
                            function_timeout=0, is_print_detail_exception=False,
                            msg_expire_seconds=3600,
                            is_using_rpc_mode=True,
                            function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(True, False, 7 * 24 * 3600),
                            broker_kind=9, concurrent_mode=1, )  # By setting broker_kind, switch broker to rabbitmq or redis etc. (9 types) with one change.

consumer_sub = get_consumer('queue_test86', consuming_function=sub, concurrent_num=200, qps=108, log_level=10, logger_prefix='xxxxx_platform_consume',
                            is_print_detail_exception=True,
                            broker_kind=9, concurrent_mode=1)  # By setting

if __name__ == '__main__':
    ConsumersManager.show_all_consumer_info()
    consumer_add.start_consuming_message()
    # consumer_sub.start_consuming_message()





