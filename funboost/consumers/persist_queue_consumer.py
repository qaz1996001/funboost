# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:35
import json
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.persist_queue_publisher import PersistQueuePublisher
from funboost.core.func_params_model import PublisherParams
from persistqueue import Empty

class PersistQueueConsumer(AbstractConsumer):
    """
    Local persistent message queue implemented using the persist queue package.
    """

    def _dispatch_task(self):
        pub = PersistQueuePublisher(publisher_params=PublisherParams(queue_name=self.queue_name))
        while True:
            try:
                item = pub.queue.get(timeout=0.5)
            except Empty:
                continue
            # self.logger.debug(f'Message fetched from local persistent sqlite queue [{self._queue_name}]:   {item}  ')
            kw = {'body': item, 'q': pub.queue, 'item': item}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        kw['q'].ack(kw['item'])

    def _requeue(self, kw):
        kw['q'].nack(kw['item'])
