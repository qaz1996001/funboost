# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2021/04/18 0008 13:32
# import time
import os

import traceback
from pathlib import Path
from kombu.entity import Exchange, Queue
from kombu.connection import Connection
from kombu.transport.virtual.base import Channel
from kombu.transport.virtual.base import Message
from kombu.transport import redis
from kombu.transport.redis import Empty


from funboost.consumers.base_consumer import AbstractConsumer
from funboost.funboost_config_deafult import BrokerConnConfig



has_patch_kombu_redis = False


def patch_kombu_redis():
    """
    Monkey-patch kombu's redis mode.
    Kombu has a bug: tasks in the redis middleware's unacked queue will never be re-consumed even if the client disconnects or the script with running tasks is suddenly closed.
    This is easily verified by making the consuming function sleep for 100 seconds, then closing the script after 20 seconds. The fetched tasks in the unacked queue will never be acknowledged or re-consumed.
    """
    global has_patch_kombu_redis
    if not has_patch_kombu_redis:
        redis_multichannelpoller_get_raw = redis.MultiChannelPoller.get

        # noinspection PyUnusedLocal
        def monkey_get(self, callback, timeout=None):
            try:
                redis_multichannelpoller_get_raw(self, callback, timeout)
            except Empty:
                self.maybe_restore_messages()
                raise Empty()

        redis.MultiChannelPoller.get = monkey_get
        has_patch_kombu_redis = True


''' kombu 能支持的消息队列中间件有如下，可以查看 D:\ProgramData\Miniconda3\Lib\site-packages\kombu\transport\__init__.py 文件。

TRANSPORT_ALIASES = {
    'amqp': 'kombu.transport.pyamqp:Transport',
    'amqps': 'kombu.transport.pyamqp:SSLTransport',
    'pyamqp': 'kombu.transport.pyamqp:Transport',
    'librabbitmq': 'kombu.transport.librabbitmq:Transport',
    'memory': 'kombu.transport.memory:Transport',
    'redis': 'kombu.transport.redis:Transport',
    'rediss': 'kombu.transport.redis:Transport',
    'SQS': 'kombu.transport.SQS:Transport',
    'sqs': 'kombu.transport.SQS:Transport',
    'mongodb': 'kombu.transport.mongodb:Transport',
    'zookeeper': 'kombu.transport.zookeeper:Transport',
    'sqlalchemy': 'kombu.transport.sqlalchemy:Transport',
    'sqla': 'kombu.transport.sqlalchemy:Transport',
    'SLMQ': 'kombu.transport.SLMQ.Transport',
    'slmq': 'kombu.transport.SLMQ.Transport',
    'filesystem': 'kombu.transport.filesystem:Transport',
    'qpid': 'kombu.transport.qpid:Transport',
    'sentinel': 'kombu.transport.redis:SentinelTransport',
    'consul': 'kombu.transport.consul:Transport',
    'etcd': 'kombu.transport.etcd:Transport',
    'azurestoragequeues': 'kombu.transport.azurestoragequeues:Transport',
    'azureservicebus': 'kombu.transport.azureservicebus:Transport',
    'pyro': 'kombu.transport.pyro:Transport'
}

'''


# noinspection PyAttributeOutsideInit
class KombuConsumer(AbstractConsumer, ):
    """
    Uses kombu as middleware. This can support many niche middleware types at once, but performance is poor. Use this only for middleware types not implemented by the distributed function scheduling framework; users can also compare performance themselves.
    """


    def custom_init(self):
        self.kombu_url = self.consumer_params.broker_exclusive_config['kombu_url'] or BrokerConnConfig.KOMBU_URL
        self._middware_name = self.kombu_url.split(":")[0]
        # logger_name = f'{self.consumer_params.logger_prefix}{self.__class__.__name__}--{self._middware_name}--{self._queue_name}'
        # self.logger = get_logger(logger_name, log_level_int=self.consumer_params.log_level,
        #                          _log_filename=f'{logger_name}.log' if self.consumer_params.create_logger_file else None,
        #                          formatter_template=FunboostCommonConfig.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER,
        #                          )  #
        if self.kombu_url.startswith('filesystem://'):
            self._create_msg_file_dir()

    def _create_msg_file_dir(self):
        os.makedirs(self.consumer_params.broker_exclusive_config['transport_options']['data_folder_in'], exist_ok=True)
        os.makedirs(self.consumer_params.broker_exclusive_config['transport_options']['data_folder_out'], exist_ok=True)
        processed_folder = self.consumer_params.broker_exclusive_config['transport_options'].get('processed_folder', None)
        if processed_folder:
            os.makedirs(processed_folder, exist_ok=True)

    # noinspection DuplicatedCode
    def _dispatch_task(self):  # This is launched by while 1 and will auto-reconnect.
        # patch_kombu_redis() # 不调用

        def callback(body: dict, message: Message):
            # print(type(body),body,type(message),message)
            # self.logger.debug(f""" 从 kombu {self._middware_name} 中取出的消息是 {body}""")
            kw = {'body': body, 'message': message, }
            self._submit_task(kw)

        self.exchange = Exchange('funboost_exchange', 'direct', durable=True)
        self.queue = Queue(self._queue_name, exchange=self.exchange, routing_key=self._queue_name, auto_delete=False, no_ack=False)
        # https://docs.celeryq.dev/projects/kombu/en/stable/reference/kombu.html?highlight=visibility_timeout#kombu.Connection 每种中间件的transport_options不一样。
        self.conn = Connection(self.kombu_url, transport_options=self.consumer_params.broker_exclusive_config['transport_options'])
        self.queue(self.conn).declare()
        with self.conn.Consumer(self.queue, callbacks=[callback], no_ack=False, prefetch_count=self.consumer_params.broker_exclusive_config['prefetch_count']) as consumer:
            # Process messages and handle events on all channels
            channel = consumer.channel  # type:Channel
            channel.body_encoding = 'no_encode'  # Changed encoding here; by default parameters stored in middleware are base64 encoded, which is unnecessary and inconvenient for viewing message plaintext.
            while True:
                self.conn.drain_events()

    def _confirm_consume(self, kw):
        kw['message'].ack()

    def _requeue(self, kw):
        kw['message'].requeue()
