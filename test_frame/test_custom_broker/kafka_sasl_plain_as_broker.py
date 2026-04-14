import atexit
import json
from collections import defaultdict, OrderedDict
# noinspection PyPackageRequirements
import time

# noinspection PyPackageRequirements
from kafka import KafkaProducer, KafkaAdminClient

# noinspection PyPackageRequirements
from kafka.admin import NewTopic
# noinspection PyPackageRequirements
from kafka.errors import TopicAlreadyExistsError

from funboost import register_custom_broker
from funboost.consumers.kafka_consumer_manually_commit import KafkaConsumerManuallyCommit
from funboost.publishers.confluent_kafka_publisher import ConfluentKafkaPublisher

from funboost.funboost_config_deafult import BrokerConnConfig

"""
The funboost framework's kafka does not use username/password to connect. If your kafka requires a password,
extending it to support username/password authentication is very simple.
PLAIN username/password kafka server extension example for funboost: just copy and paste the
KafkaConsumerManuallyCommit class and slightly modify the kafka connection code.
No need to inherit AbstractConsumer and rewrite all kafka operations; just inherit the subclass.

Add kafka configuration in funboost_config.py as follows. The variable name KFFKA_CONFIG is arbitrary,
e.g. it can be called KFFKACONFAAA; just reference the variable in your code.

KFFKA_CONFIG = {
    "bootstrap_servers":KAFKA_BOOTSTRAP_SERVERS,
    'sasl_mechanism': "PLAIN",
    'security_protocol': "SASL_PLAINTEXT",
    'sasl_plain_username': "user",
    'sasl_plain_password': "password",
}
"""


class SaslPlainKafkaConsumer(KafkaConsumerManuallyCommit):


    def _dispatch_task(self):

        # This package is hard to install on Windows; users need to figure out installation themselves. Windows users need C++ 14.0+ environment.
        from confluent_kafka import Consumer as ConfluentConsumer
        try:
            admin_client = KafkaAdminClient(
                **BrokerConnConfig.KFFKA_SASL_CONFIG)
            admin_client.create_topics([NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except TopicAlreadyExistsError:
            pass

        self._producer = KafkaProducer(
            **BrokerConnConfig.KFFKA_SASL_CONFIG)
        # consumer 配置 https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
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
            # msg的类型  https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#message
            # value()  offset() partition()
            # print('Received message: {}'.format(msg.value().decode('utf-8'))) # noqa
            self._partion__offset_consume_status_map[msg.partition(
            )][msg.offset()] = 0
            kw = {'partition': msg.partition(), 'offset': msg.offset(), 'body': json.loads(msg.value())}  # noqa
            if self.consumer_params.is_show_message_get_from_broker:
                self.logger.debug(
                    f'Message retrieved from kafka topic [{self._queue_name}], partition {msg.partition()}, offset {msg.offset()}: {msg.value()}')  # noqa
            self._submit_task(kw)


class SaslPlainKafkaPublisher(ConfluentKafkaPublisher):
    """
    Using kafka as broker; the confluent_kafka package has far better performance than kafka-python
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        from confluent_kafka import Producer as ConfluentProducer  # This package is hard to install; users must figure out installation themselves. Windows users need C++ 14.0+ environment.
        # self._producer = KafkaProducer(bootstrap_servers=funboost_config_deafult.KAFKA_BOOTSTRAP_SERVERS)
        try:
            admin_client = KafkaAdminClient(**BrokerConnConfig.KFFKA_SASL_CONFIG)
            admin_client.create_topics([NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except TopicAlreadyExistsError:
            pass
        except BaseException as e:
            self.logger.exception(e)
        atexit.register(self.close)  # If not actively closed before program exit, an error will occur.
        self._confluent_producer = ConfluentProducer({
            'bootstrap.servers': ','.join(BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS),
            'security.protocol': BrokerConnConfig.KFFKA_SASL_CONFIG['security_protocol'],
            'sasl.mechanisms': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_mechanism'],
            'sasl.username': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_plain_username'],
            'sasl.password': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_plain_password']
        })
        self._recent_produce_time = time.time()


BROKER_KIND_SASlPlAINKAFKA = 107
register_custom_broker(BROKER_KIND_SASlPlAINKAFKA, SaslPlainKafkaPublisher, SaslPlainKafkaConsumer)
