# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
# noinspection PyPackageRequirements

from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.lazy_impoter import KafkaPythonImporter
from funboost.funboost_config_deafult import BrokerConnConfig
# from nb_log import get_logger
from funboost.core.loggers import get_funboost_file_logger

# LogManager('kafka').get_logger_and_add_handlers(30)
get_funboost_file_logger('kafka', log_level_int=30)


class KafkaConsumer(AbstractConsumer):
    """
    Consumer implemented using kafka as middleware. Auto-commit consumption, at-most-once delivery, randomly restarting will lose a large batch of running tasks. Recommend using confluent_kafka middleware, kafka_consumer_manually_commit.py.

    You can let the consuming function sleep for 60 seconds internally, then suddenly stop the consuming code. Use kafka-consumer-groups.sh --bootstrap-server 127.0.0.1:9092 --describe --group funboost to verify the difference between auto-commit and manual commit consumption.
    """

    """
    auto_offset_reset 介绍
      auto_offset_reset (str): A policy for resetting offsets on
            OffsetOutOfRange errors: 'earliest' will move to the oldest
            available message, 'latest' will move to the most recent. Any
            other value will raise the exception. Default: 'latest'.
    """

    def _dispatch_task(self):
        try:
            admin_client = KafkaPythonImporter().KafkaAdminClient(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
            admin_client.create_topics([KafkaPythonImporter().NewTopic(self._queue_name,
                                                                       self.consumer_params.broker_exclusive_config['num_partitions'],
                                                                       self.consumer_params.broker_exclusive_config['replication_factor'])])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except KafkaPythonImporter().TopicAlreadyExistsError:
            pass

        self._producer = KafkaPythonImporter().KafkaProducer(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
        consumer = KafkaPythonImporter().OfficialKafkaConsumer(self._queue_name, bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS,
                                                               group_id=self.consumer_params.broker_exclusive_config["group_id"],
                                                               enable_auto_commit=True,
                                                               auto_offset_reset=self.consumer_params.broker_exclusive_config["auto_offset_reset"],
                                                               )
        #  auto_offset_reset (str): A policy for resetting offsets on
        #             OffsetOutOfRange errors: 'earliest' will move to the oldest
        #             available message, 'latest' will move to the most recent. Any
        #             other value will raise the exception. Default: 'latest'.       默认是latest

        # kafka group_id

        # REMIND Due to high concurrency consumption with many threads and few partitions, auto-commit is used here. Otherwise, multi-threaded offset commits for the same partition would cause chaos and be meaningless.
        # REMIND For high reliability and consistency, use rabbitmq.
        # REMIND Advantage is high concurrency. Topics are like flipping through a book - offsets can be reset to re-consume at any time. Multiple groups consuming the same topic have independent offsets.
        for message in consumer:
            # Note: message and value are raw byte data, need to decode
            kw = {'consumer': consumer, 'message': message, 'body': message.value.decode('utf-8')}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # Using kafka's auto-commit mode.

    def _requeue(self, kw):
        self._producer.send(self._queue_name, json.dumps(kw['body']).encode())
