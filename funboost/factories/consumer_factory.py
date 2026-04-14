# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:19

import os
import threading
import typing
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.func_params_model import BoosterParams


def get_consumer(boost_params: BoosterParams) -> AbstractConsumer:
    """
    :param args: Parameters are the same as AbstractConsumer's parameters
    :param broker_kind:
    :param kwargs:
    :return:
    """
    from funboost.factories.broker_kind__publsiher_consumer_type_map import broker_kind__publsiher_consumer_type_map, regist_to_funboost
    regist_to_funboost(boost_params.broker_kind)  # Dynamically register brokers into the framework using lazy imports, so users won't get errors for uninstalled third-party packages they don't need.

    if boost_params.broker_kind not in broker_kind__publsiher_consumer_type_map:
        raise ValueError(f'The specified broker kind is invalid, the value you set is {boost_params.broker_kind} ')
    consumer_cls = broker_kind__publsiher_consumer_type_map[boost_params.broker_kind][1]
    if not boost_params.consumer_override_cls:
        return consumer_cls(boost_params)
    else:
        ConsumerClsOverride = type(f'{consumer_cls.__name__}__{boost_params.consumer_override_cls.__name__}', (boost_params.consumer_override_cls, consumer_cls, AbstractConsumer), {})
        # class ConsumerClsOverride(boost_params.consumer_override_cls, consumer_cls, AbstractConsumer):
        #     pass

        return ConsumerClsOverride(boost_params)


class ConsumerCacheProxy:
    pid_registry_queue_name__consumer_map:typing.Dict[typing.Tuple[int,str,str],AbstractConsumer] = {}
    _lock = threading.Lock()

    def __init__(self,boost_params: BoosterParams):
        self.boost_params = boost_params

    @property
    def consumer(self) ->AbstractConsumer:
        pid = os.getpid()
        # Include booster_registry_name as namespace isolation, allowing different registries to use the same queue_name without conflicts
        key = (pid, self.boost_params.booster_registry_name, self.boost_params.queue_name)
        if key not in self.pid_registry_queue_name__consumer_map:
            with self._lock:
                if key not in self.pid_registry_queue_name__consumer_map:
                    self.pid_registry_queue_name__consumer_map[key] = get_consumer(self.boost_params)
        return self.pid_registry_queue_name__consumer_map[key]