# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/6 0006 12:12
import copy
import json
import time
import typing
import uuid

from nameko.standalone.rpc import ClusterRpcProxy

from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher, TaskOptions


def get_nameko_config():
    return {'AMQP_URI': f'amqp://{BrokerConnConfig.RABBITMQ_USER}:{BrokerConnConfig.RABBITMQ_PASS}@{BrokerConnConfig.RABBITMQ_HOST}:{BrokerConnConfig.RABBITMQ_PORT}/{BrokerConnConfig.RABBITMQ_VIRTUAL_HOST}'}


class NamekoPublisher(AbstractPublisher, ):
    """
    Uses nameko as the broker.
    """

    def custom_init(self):
        self._rpc = ClusterRpcProxy(get_nameko_config())

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                task_options: TaskOptions = None):
        msg, msg_function_kw, extra_params, task_id = self._convert_msg(msg, task_id, task_options)
        t_start = time.time()
        with self._rpc as rpc:
            res = getattr(rpc, self.queue_name).call(**msg_function_kw)
        self.logger.debug(f'Called nameko {self.queue_name} service call method, took {round(time.time() - t_start, 4)} seconds, params  {msg_function_kw}')  # Full msg is too long to display.
        return res

    def _publish_impl(self, msg):
        pass

    def clear(self):
        self.logger.warning('Not yet implemented')

    def get_message_count(self):
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass
