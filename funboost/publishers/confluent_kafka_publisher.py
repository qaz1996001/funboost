# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/20 0008 12:12

import os

from funboost.core.lazy_impoter import KafkaPythonImporter

if os.name == 'nt':
    """
    As a precaution, set the path here, otherwise Python installed via anaconda may encounter ImportError: DLL load failed while importing cimpl: The specified module could not be found.
    Setting extra paths is fine; missing paths causes trouble.
    """
    from pathlib import Path
    import sys

    # print(sys.executable)  #F:\minicondadir\Miniconda2\envs\py38\python.exe
    # print(os.getenv('path'))
    python_install_path = Path(sys.executable).parent.absolute()
    kafka_libs_path = python_install_path / Path(r'.\Lib\site-packages\confluent_kafka.libs')
    dlls_path = python_install_path / Path(r'.\DLLs')
    library_bin_path = python_install_path / Path(r'.\Library\bin')
    # print(library_bin_path)
    path_env = os.getenv('path')
    os.environ['path'] = f'''{path_env};{kafka_libs_path};{dlls_path};{library_bin_path};'''

import atexit
import time

from confluent_kafka import Producer as ConfluentProducer
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher


class ConfluentKafkaPublisher(AbstractPublisher, ):
    """
    Uses kafka as the broker. The confluent_kafka package has much better performance than kafka-python.
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):

        # self._producer = KafkaProducer(bootstrap_servers=funboost_config_deafult.KAFKA_BOOTSTRAP_SERVERS)
        try:
            admin_client = KafkaPythonImporter().KafkaAdminClient(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
            admin_client.create_topics([KafkaPythonImporter().NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except KafkaPythonImporter().TopicAlreadyExistsError:
            pass
        except BaseException as e:
            self.logger.exception(e)
        atexit.register(self.close)  # Will raise an error if not actively closed before program exit.
        self._confluent_producer = ConfluentProducer({'bootstrap.servers': ','.join(BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)})
        self._recent_produce_time = time.time()

    # noinspection PyAttributeOutsideInit
    def _publish_impl(self, msg):
        # noinspection PyTypeChecker
        # self.logger.debug(msg)
        self._confluent_producer.produce(self._queue_name, msg.encode(), )
        if time.time() - self._recent_produce_time > 1:
            self._confluent_producer.flush()
            self._recent_produce_time = time.time()

    def clear(self):
        self.logger.warning('Kafka queue clearing not yet implemented')
        # self._consumer.seek_to_end()
        # self.logger.warning(f'Reset kafka offset to the latest position')

    def get_message_count(self):
        return -1  # Haven't found a method to get unconsumed count across all partitions.

    def close(self):
        pass
        # self._confluent_producer.

    def _at_exit(self):
        # self._producer.flush()
        self._confluent_producer.flush()
        super()._at_exit()


class SaslPlainKafkaPublisher(ConfluentKafkaPublisher):
    """
    Uses kafka as the broker. The confluent_kafka package has much better performance than kafka-python.
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        # self._producer = KafkaProducer(bootstrap_servers=funboost_config_deafult.KAFKA_BOOTSTRAP_SERVERS)
        try:
            admin_client = KafkaPythonImporter().KafkaAdminClient(**BrokerConnConfig.KFFKA_SASL_CONFIG)
            admin_client.create_topics([KafkaPythonImporter().NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except KafkaPythonImporter().TopicAlreadyExistsError:
            pass
        except BaseException as e:
            self.logger.exception(e)
        atexit.register(self.close)  # Will raise an error if not actively closed before program exit.
        self._confluent_producer = ConfluentProducer({
            'bootstrap.servers': ','.join(BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS),
            'security.protocol': BrokerConnConfig.KFFKA_SASL_CONFIG['security_protocol'],
            'sasl.mechanisms': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_mechanism'],
            'sasl.username': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_plain_username'],
            'sasl.password': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_plain_password']
        })
        self._recent_produce_time = time.time()
