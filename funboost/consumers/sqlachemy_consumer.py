# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:33
import json
from funboost.constant import BrokerEnum
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.queues import sqla_queue


class SqlachemyConsumer(AbstractConsumer):
    """
    Simulates a message queue for 5 types of databases using SQLAlchemy, supports consumption confirmation.
    """


    def _dispatch_task(self):
        self.queue = sqla_queue.SqlaQueue(self._queue_name, BrokerConnConfig.SQLACHEMY_ENGINE_URL)
        while True:
            sqla_task_dict = self.queue.get()
            # self.logger.debug(f'Message fetched from database {frame_config.SQLACHEMY_ENGINE_URL[:25]}.. queue [{self._queue_name}]:  {sqla_task_dict}')
            self._print_message_get_from_broker(f'from database {BrokerConnConfig.SQLACHEMY_ENGINE_URL[:25]}', sqla_task_dict)
            kw = {'body': sqla_task_dict['body'], 'sqla_task_dict': sqla_task_dict}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        self.queue.set_success(kw['sqla_task_dict'])

    def _requeue(self, kw):
        self.queue.set_task_status(kw['sqla_task_dict'], sqla_queue.TaskStatus.REQUEUE)

