# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:16
import copy
import os
import threading
import typing
from typing import Callable
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.core.func_params_model import PublisherParams


# broker_kind__publisher_type_map

def get_publisher(publisher_params: PublisherParams) -> AbstractPublisher:
    """
    :param queue_name:
    :param log_level_int:
    :param logger_prefix:
    :param is_add_file_handler:
    :param clear_queue_within_init:
    :param is_add_publish_time: Whether to add publish time; will be deprecated in the future, always added.
    :param consuming_function: The consuming function, used for validating function parameters at publish time. If not provided, no validation is performed on published tasks.
               For example, if the add function accepts x and y parameters, pushing {"x":1,"z":3} would be incorrect since the function does not accept a z parameter.
    :param broker_kind: The type of broker or package used.
    :param broker_exclusive_config: Broker-specific non-universal configuration. Different brokers have their own unique settings that are not compatible across all brokers. Since the framework supports 30+ message queues, message queues are not simply FIFO queues.
           For example, Kafka supports consumer groups, RabbitMQ supports various unique concepts like different ack mechanisms and complex routing mechanisms. Each message queue has its own unique configuration parameters that can be passed here.

    :return:
    """

    from funboost.factories.broker_kind__publsiher_consumer_type_map import broker_kind__publsiher_consumer_type_map, regist_to_funboost
    broker_kind = publisher_params.broker_kind
    regist_to_funboost(broker_kind)  # Dynamically register brokers into the framework using lazy imports, so users won't get errors for uninstalled third-party packages they don't need.
    if broker_kind not in broker_kind__publsiher_consumer_type_map:
        raise ValueError(f'The specified broker kind is invalid, the value you set is {broker_kind} ')
    publisher_cls = broker_kind__publsiher_consumer_type_map[broker_kind][0]
    if not publisher_params.publisher_override_cls:
        return publisher_cls(publisher_params)
    else:
        PublsiherClsOverride = type(f'{publisher_cls.__name__}__{publisher_params.publisher_override_cls.__name__}', (publisher_params.publisher_override_cls, publisher_cls, AbstractPublisher), {})
        # class PublsiherClsOverride(publisher_params.publisher_override_cls, publisher_cls, AbstractPublisher):
        #     pass

        return PublsiherClsOverride(publisher_params)

class PublisherCacheProxy:
    pid_registry_queue_name__publisher_map:typing.Dict[typing.Tuple[int,str,str],AbstractPublisher] = {}
    _lock = threading.Lock()
    def __init__(self,publisher_params: PublisherParams):
        self.publisher_params = publisher_params
      
    @property
    def publisher(self) ->AbstractPublisher:
        pid = os.getpid()
        key = (pid, self.publisher_params.booster_registry_name, self.publisher_params.queue_name)
        if key not in self.pid_registry_queue_name__publisher_map:
            with self._lock:
                if key not in self.pid_registry_queue_name__publisher_map:
                    self.pid_registry_queue_name__publisher_map[key] = get_publisher(self.publisher_params)
        return self.pid_registry_queue_name__publisher_map[key]