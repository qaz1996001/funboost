# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2021/4/18 0008 13:32

"""
    This can achieve single partition kafka topic, but with funboost 200 threads consuming messages, and freely force-restarting the consuming process without losing messages
"""

import json
import threading
from collections import defaultdict, OrderedDict
# noinspection PyPackageRequirements
import time

# noinspection PyPackageRequirements
# pip install kafka-python==2.0.2

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.lazy_impoter import KafkaPythonImporter
from funboost.funboost_config_deafult import BrokerConnConfig
from confluent_kafka.cimpl import TopicPartition
from confluent_kafka import Consumer as ConfluentConsumer  # This package is hard to install on Windows; users need to install it themselves when using this middleware. Windows users need C++ 14.0 or above.


class KafkaConsumerManuallyCommit(AbstractConsumer):
    """
    Consumer implemented using confluent_kafka as middleware. 10x faster than kafka-python for operating kafka middleware.
    This uses automatic manual commit every 2 seconds. Since consumption is asynchronous in a concurrent pool, it prevents loss of running tasks when the program is forcefully closed, better than auto-commit.
    Recommended if using kafka.

    You can let the consuming function sleep for 60 seconds internally, then suddenly stop the consuming code. Use kafka-consumer-groups.sh --bootstrap-server 127.0.0.1:9092 --describe --group frame_group to verify the difference between auto-commit and manual commit consumption.
    """


    def custom_init(self):
        self._lock_for_operate_offset_dict = threading.Lock()

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
        # consumer configuration: https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
        self._confluent_consumer = ConfluentConsumer({
            'bootstrap.servers': ','.join(BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS),
            'group.id': self.consumer_params.broker_exclusive_config["group_id"],
            'auto.offset.reset': self.consumer_params.broker_exclusive_config["auto_offset_reset"],
            'enable.auto.commit': False
        })
        self._confluent_consumer.subscribe([self._queue_name])

        self._recent_commit_time = time.time()
        self._partion__offset_consume_status_map = defaultdict(OrderedDict)
        while 1:
            msg = self._confluent_consumer.poll(timeout=10)
            self._manually_commit()
            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue
            # msg type reference: https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#message
            # value()  offset() partition()
            # print('Received message: {}'.format(msg.value().decode('utf-8'))) # noqa
            self._partion__offset_consume_status_map[msg.partition()][msg.offset()] = 0
            kw = {'partition': msg.partition(), 'offset': msg.offset(), 'body': msg.value()}  # noqa
            if self.consumer_params.is_show_message_get_from_broker:
                self.logger.debug(
                    f'Message fetched from kafka topic [{self._queue_name}], partition {msg.partition()}, offset {msg.offset()}: {msg.value()}')  # noqa
            self._submit_task(kw)


    def _manually_commit(self):
        """
        Kafka requires the number of consuming threads and partitions to be one-to-one or one-to-many, not many-to-one. Message concurrent processing is limited by partition count. This supports very high thread count consumption, so commit is very complex.
        Because this supports 200 threads consuming a single partition, consumption and kafka task pulling are not in the same thread, and tasks with larger offsets may complete before those with smaller offsets.
        Every 2 seconds, commit the maximum offset where consecutive consumption status is 1.
        :return:
        """
        with self._lock_for_operate_offset_dict:
            if time.time() - self._recent_commit_time > 2:
                partion_max_consumed_offset_map = dict()
                to_be_remove_from_partion_max_consumed_offset_map = defaultdict(list)
                for partion, offset_consume_status in self._partion__offset_consume_status_map.items():
                    sorted_keys = sorted(offset_consume_status.keys())
                    offset_consume_status_ordered = {key: offset_consume_status[key] for key in sorted_keys}
                    max_consumed_offset = None

                    for offset, consume_status in offset_consume_status_ordered.items():
                        # print(offset,consume_status)
                        if consume_status == 1:
                            max_consumed_offset = offset
                            to_be_remove_from_partion_max_consumed_offset_map[partion].append(offset)
                        else:
                            break
                    if max_consumed_offset is not None:
                        partion_max_consumed_offset_map[partion] = max_consumed_offset
                # self.logger.info(partion_max_consumed_offset_map)
                # TopicPartition
                offsets = list()
                for partion, max_consumed_offset in partion_max_consumed_offset_map.items():
                    # print(partion,max_consumed_offset)
                    offsets.append(TopicPartition(topic=self._queue_name, partition=partion, offset=max_consumed_offset + 1))
                if len(offsets):
                    self._confluent_consumer.commit(offsets=offsets, asynchronous=False)
                self._recent_commit_time = time.time()
                for partion, offset_list in to_be_remove_from_partion_max_consumed_offset_map.items():
                    for offset in offset_list:
                        del self._partion__offset_consume_status_map[partion][offset]

    def _confirm_consume(self, kw):
        with self._lock_for_operate_offset_dict:
            self._partion__offset_consume_status_map[kw['partition']][kw['offset']] = 1
            # print(self._partion__offset_consume_status_map)

    def _requeue(self, kw):
        self._producer.send(self._queue_name, json.dumps(kw['body']).encode())


class SaslPlainKafkaConsumer(KafkaConsumerManuallyCommit):

    def _dispatch_task(self):

        try:
            admin_client = KafkaPythonImporter().KafkaAdminClient(
                **BrokerConnConfig.KFFKA_SASL_CONFIG)
            admin_client.create_topics([KafkaPythonImporter().NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except KafkaPythonImporter().TopicAlreadyExistsError:
            pass

        self._producer = KafkaPythonImporter().KafkaProducer(
            **BrokerConnConfig.KFFKA_SASL_CONFIG)
        # consumer configuration: https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
        self._confluent_consumer = ConfluentConsumer({
            'bootstrap.servers': ','.join(BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS),
            'security.protocol': BrokerConnConfig.KFFKA_SASL_CONFIG['security_protocol'],
            'sasl.mechanisms': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_mechanism'],
            'sasl.username': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_plain_username'],
            'sasl.password': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_plain_password'],
            'group.id': self.consumer_params.broker_exclusive_config["group_id"],
            'auto.offset.reset': self.consumer_params.broker_exclusive_config["auto_offset_reset"],
            'enable.auto.commit': False
        })
        self._confluent_consumer.subscribe([self._queue_name])

        self._recent_commit_time = time.time()
        self._partion__offset_consume_status_map = defaultdict(OrderedDict)

        while 1:
            msg = self._confluent_consumer.poll(timeout=10)
            self._manually_commit()
            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue
            # msg type: https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#message
            # value()  offset() partition()
            # print('Received message: {}'.format(msg.value().decode('utf-8'))) # noqa
            self._partion__offset_consume_status_map[msg.partition(
            )][msg.offset()] = 0
            kw = {'partition': msg.partition(), 'offset': msg.offset(), 'body': msg.value()}  # noqa
            if self.consumer_params.is_show_message_get_from_broker:
                self.logger.debug(
                    f'Message fetched from kafka topic [{self._queue_name}], partition {msg.partition()}, offset {msg.offset()}: {msg.value()}')  # noqa
            self._submit_task(kw)
