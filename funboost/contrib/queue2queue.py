import os
import time
import typing
from multiprocessing import Process
import logging
import threading

from funboost import get_publisher, get_consumer, BrokerEnum, wait_for_possible_has_finish_all_tasks_by_conusmer_list
from funboost.core.func_params_model import PublisherParams, BoosterParams

""" Move messages from one queue to another, e.g. move messages from a dead letter queue to a normal queue."""


def consume_and_push_to_another_queue(source_queue_name: str, source_broker_kind: str,
                                      target_queue_name: str, target_broker_kind: str,
                                      log_level: int = logging.DEBUG,
                                      exit_script_when_finish=False):
    """ Move messages from one queue to another, e.g. move messages from a dead letter queue to a normal queue."""
    if source_queue_name == target_queue_name and source_broker_kind == target_broker_kind:
        raise ValueError('Cannot transfer messages to the same queue, otherwise it would cause an infinite loop')

    target_publisher = get_publisher(publisher_params=PublisherParams(queue_name=target_queue_name, broker_kind=target_broker_kind, log_level=log_level))
    msg_cnt = 0
    msg_cnt_lock = threading.Lock()

    def _task_fun(**kwargs):
        # print(kwargs)
        nonlocal msg_cnt
        target_publisher.publish(kwargs)
        with msg_cnt_lock:
            msg_cnt += 1

    source_consumer = get_consumer(boost_params=BoosterParams(queue_name=source_queue_name, broker_kind=source_broker_kind, consuming_function=_task_fun, log_level=log_level))
    source_consumer._set_do_not_delete_extra_from_msg()
    source_consumer.start_consuming_message()
    if exit_script_when_finish:
        source_consumer.wait_for_possible_has_finish_all_tasks(2)
        print(f'Message transfer complete, exiting script. Total messages transferred from {source_queue_name} to {target_queue_name} queue: {msg_cnt}')
        os._exit(888)  # Exit script


def _consume_and_push_to_another_queue_for_multi_process(source_queue_name: str, source_broker_kind: str,
                                                         target_queue_name: str, target_broker_kind: str,
                                                         log_level: int = logging.DEBUG,
                                                         ):
    consume_and_push_to_another_queue(source_queue_name, source_broker_kind, target_queue_name, target_broker_kind, log_level, False)
    while 1:
        time.sleep(3600)


def multi_prcocess_queue2queue(source_target_list: typing.List[typing.List],
                               log_level: int = logging.DEBUG, exit_script_when_finish=False, n=1):
    """
    Transfer multiple queues using multiple processes.
    :param source_target_list:  Input example: [['test_queue77h5', BrokerEnum.RABBITMQ_AMQPSTORM, 'test_queue77h4', BrokerEnum.RABBITMQ_AMQPSTORM],['test_queue77h6', BrokerEnum.RABBITMQ_AMQPSTORM, 'test_queue77h7', BrokerEnum.REDIS]]
    :param log_level:
    :param exit_script_when_finish:
    :param n:
    :return:
    """
    source_consumer_list = []
    for (source_queue_name, source_broker_kind, target_queue_name, target_broker_kind) in source_target_list:
        for i in range(n):
            Process(target=_consume_and_push_to_another_queue_for_multi_process,
                    args=(source_queue_name, source_broker_kind, target_queue_name, target_broker_kind, log_level)).start()
        if exit_script_when_finish:
            def _fun():
                pass

            source_consumer = get_consumer(boost_params=BoosterParams(queue_name=source_queue_name, broker_kind=source_broker_kind, consuming_function=_fun,
                                                                      log_level=log_level))
            source_consumer_list.append(source_consumer)
    if exit_script_when_finish:
        wait_for_possible_has_finish_all_tasks_by_conusmer_list(consumer_list=source_consumer_list, minutes=2)
        for (source_queue_name, source_broker_kind, target_queue_name, target_broker_kind) in source_target_list:
            print(f'{source_queue_name} transferred to {target_queue_name}, message transfer complete, exiting script')
        os._exit(999)  #


if __name__ == '__main__':
    # Transfer one queue at a time, using a single process
    consume_and_push_to_another_queue('test_queue77h3_dlx', BrokerEnum.REDIS_PRIORITY,
                                      'test_queue77h3', BrokerEnum.REDIS_PRIORITY,
                                      log_level=logging.INFO, exit_script_when_finish=True)

    # Transfer multiple queues using multiple processes.
    multi_prcocess_queue2queue([['test_queue77h5', BrokerEnum.RABBITMQ_AMQPSTORM, 'test_queue77h4', BrokerEnum.RABBITMQ_AMQPSTORM]],
                               log_level=logging.INFO, exit_script_when_finish=True, n=6)
