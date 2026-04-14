# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/7/8 0008 13:27
import json
import time
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.rocketmq_publisher import RocketmqPublisher
from funboost.core.func_params_model import PublisherParams

from funboost.utils import system_util

if system_util.is_windows():
    raise ImportError('The rocketmq package only supports Linux and macOS')

from rocketmq.client import PushConsumer


class RocketmqConsumer(AbstractConsumer):
    """
    Installation required
    """

    GROUP_ID = 'g_funboost'

    def _dispatch_task(self):
        consumer = PushConsumer(f'{self.GROUP_ID}_{self._queue_name}')
        consumer.set_namesrv_addr(BrokerConnConfig.ROCKETMQ_NAMESRV_ADDR)
        consumer.set_thread_count(1)
        consumer.set_message_batch_max_size(self.consumer_params.concurrent_num)

        self._publisher = RocketmqPublisher(publisher_params=PublisherParams(queue_name=self._queue_name,))

        def callback(rocketmq_msg):
            # self.logger.debug(f'Message fetched from rocketmq topic [{self._queue_name}] queue_id {rocketmq_msg.queue_id}: {rocketmq_msg.body}')

            kw = {'body': rocketmq_msg.body, 'rocketmq_msg': rocketmq_msg}
            self._submit_task(kw)

        consumer.subscribe(self._queue_name, callback)
        consumer.start()

        while True:
            time.sleep(3600)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self._publisher.publish(kw['body'])
