import os
import signal
from multiprocessing import Process
import time
from typing import List
from concurrent.futures import ProcessPoolExecutor
from funboost.core.booster import Booster
from funboost.core.helper_funs import run_forever
from funboost.core.loggers import flogger
from funboost.core.lazy_impoter import funboost_lazy_impoter


def _run_consumer_in_new_process(queue_name, ):
    booster_current_pid = funboost_lazy_impoter.BoostersManager.get_or_create_booster_by_queue_name(queue_name)
    # booster_current_pid = boost(**boost_params)(consuming_function)
    booster_current_pid.consume()
    # ConsumersManager.join_all_consumer_dispatch_task_thread()
    run_forever()


def run_consumer_with_multi_process(booster: Booster, process_num=1):
    """
    :param booster: The consuming function decorated with @boost
    :param process_num: Number of processes to start. Mainly for multi-process concurrency + 4 fine-grained concurrency modes (threading, gevent, eventlet, asyncio). Stacked concurrency.
    This is the multi-process approach, written once and compatible with both Windows and Linux. Launches 6 processes at once, combined with multi-threaded concurrency.
    """
    '''
       from funboost import boost, BrokerEnum, ConcurrentModeEnum, run_consumer_with_multi_process
       import os

       @boost('test_multi_process_queue',broker_kind=BrokerEnum.REDIS_ACK_ABLE,concurrent_mode=ConcurrentModeEnum.THREADING,)
       def fff(x):
           print(x * 10,os.getpid())

       if __name__ == '__main__':
           # fff.consume()
           run_consumer_with_multi_process(fff,6) # Start 6 processes at once, combined with multi-threaded concurrency.
           fff.multi_process_conusme(6)    # This also starts 6 processes at once, combined with multi-threaded concurrency.
    '''
    if not isinstance(booster, Booster):
        raise ValueError(f'{booster} parameter must be a function decorated with @boost')
    if process_num == 1 and False:
        booster.consume()
    else:
        for i in range(process_num):
            # print(i)
            Process(target=_run_consumer_in_new_process,
                    args=(booster.queue_name,)).start()


def _multi_process_pub_params_list_in_new_process(queue_name, msgs: List[dict]):
    booster_current_pid = funboost_lazy_impoter.BoostersManager.get_or_create_booster_by_queue_name(queue_name)
    publisher = booster_current_pid.publisher
    publisher.set_log_level(20)  # Ultra-high-speed publishing; printing detailed debug logs would freeze the screen and severely reduce performance.
    for msg in msgs:
        publisher.publish(msg)


def multi_process_pub_params_list(booster: Booster, params_list, process_num=16):
    """Ultra-high-speed multi-process task publishing, making full use of multi-core CPUs."""
    if not isinstance(booster, Booster):
        raise ValueError(f'{booster} parameter must be a function decorated with @boost')
    params_list_len = len(params_list)
    if params_list_len < 1000 * 100:
        raise ValueError(f'The number of tasks to publish is {params_list_len}; this method requires at least 100,000 tasks.')
    ava_len = params_list_len // process_num + 1
    with ProcessPoolExecutor(process_num) as pool:
        t0 = time.time()
        for i in range(process_num):
            msgs = params_list[i * ava_len: (i + 1) * ava_len]
            # print(msgs)
            pool.submit(_multi_process_pub_params_list_in_new_process, booster.queue_name,
                        msgs)
    flogger.info(f'\n Published {params_list_len} tasks via multi_process_pub_params_list multi-process approach. Time elapsed: {time.time() - t0} seconds')
