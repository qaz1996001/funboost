# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/20 0008 12:12

# noinspection PyPackageRequirements
import atexit

from funboost.core.lazy_impoter import KafkaPythonImporter
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher


class KafkaPublisher(AbstractPublisher, ):
    """
    Uses kafka as the broker.
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._producer = KafkaPythonImporter().KafkaProducer(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
        self._admin_client = KafkaPythonImporter().KafkaAdminClient(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
        try:
            self._admin_client.create_topics([KafkaPythonImporter().NewTopic(self._queue_name,
                                                                             self.publisher_params.broker_exclusive_config['num_partitions'],
                                                                             self.publisher_params.broker_exclusive_config['replication_factor'])])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except KafkaPythonImporter().TopicAlreadyExistsError:
            pass
        except BaseException as e:
            self.logger.exception(e)
        atexit.register(self.close)  # Will raise an error if not actively closed before program exit.

    def _publish_impl(self, msg):
        # noinspection PyTypeChecker
        # self.logger.debug(msg)
        # print(msg)
        self._producer.send(self._queue_name, msg.encode(), )

    def clear(self):
        self.logger.warning('Kafka queue clearing not yet implemented')
        # self._consumer.seek_to_end()
        # self.logger.warning(f'Reset kafka offset to the latest position')

    def get_message_count(self):
        # return -1 # Haven't found a method to get unconsumed count across all partitions.
        # print(self._admin_client.list_consumer_group_offsets('frame_group'))
        # print(self._admin_client.describe_consumer_groups('frame_group'))
        return -1

    def close(self):
        self._producer.close()

    def _at_exit(self):
        self._producer.flush()
        super()._at_exit()
