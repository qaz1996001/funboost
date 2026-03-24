# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:33
import json
from funboost.constant import BrokerEnum
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.queues.peewee_queue import PeeweeQueue,TaskStatus


class PeeweeConsumer(AbstractConsumer):
    """
    Message queue simulated using peewee to operate 5 types of databases, supports consumption confirmation.
    """


    def _dispatch_task(self):
        self.queue = PeeweeQueue(self.queue_name)
        while True:
            task_dict = self.queue.get()
            # print(task_dict)
            # self.logger.debug(f'Message fetched from database {frame_config.SQLACHEMY_ENGINE_URL[:25]}.. queue [{self._queue_name}]:  {sqla_task_dict}')
            kw = {'body':task_dict['body'], 'job_id': task_dict['job_id']}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        self.queue.set_success(kw['job_id'])

    def _requeue(self, kw):
        self.queue.requeue_task(kw['job_id'])



