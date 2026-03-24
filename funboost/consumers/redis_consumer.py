# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
# import time
import time



from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.utils.redis_manager import RedisMixin
from funboost.core.serialization import Serialization

class RedisConsumer(AbstractConsumer, RedisMixin):
    """
    Consumer implemented using Redis as middleware, using Redis list structure.
    If the consuming script is randomly restarted, abnormally closed, or crashes while running, a large batch of tasks will be lost. For high reliability, use rabbitmq, redis_ack_able, or redis_stream middleware.

    This is the complex version, pulling 100 messages at once to reduce Redis interactions. The simple version is in funboost/consumers/redis_consumer_simple.py
    """



    # noinspection DuplicatedCode
    def _dispatch_task(self):
        pull_msg_batch_size =  self.consumer_params.broker_exclusive_config['pull_msg_batch_size']
        while True:
            # if False:
            #     pass
            with self.redis_db_frame.pipeline() as p:
                p.lrange(self._queue_name, 0, pull_msg_batch_size- 1)
                p.ltrim(self._queue_name, pull_msg_batch_size, -1)
                task_str_list = p.execute()[0]
            if task_str_list:
                # self.logger.debug(f'Message fetched from redis queue [{self._queue_name}]:  {task_str_list}  ')
                self._print_message_get_from_broker( task_str_list)
                for task_str in task_str_list:
                    kw = {'body': task_str}
                    self._submit_task(kw)
            else:
                result = self.redis_db_frame.brpop(self._queue_name, timeout=60)
                if result:
                    # self.logger.debug(f'Message fetched from redis queue [{self._queue_name}]:  {result[1].decode()}  ')
                    kw = {'body': result[1]}
                    self._submit_task(kw)

    def _dispatch_task00(self):
        while True:
            result = self.redis_db_frame.blpop(self._queue_name, timeout=60)
            if result:
                # self.logger.debug(f'Message fetched from redis queue [{self._queue_name}]:  {result[1].decode()}  ')
                kw = {'body': result[1]}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # Redis does not have consumption confirmation functionality.

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name,Serialization.to_json_str(kw['body']))
