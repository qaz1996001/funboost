# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/19 0008 12:12
from funboost.core.lazy_impoter import GnsqImporter
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.funboost_config_deafult import BrokerConnConfig


class NsqPublisher(AbstractPublisher, ):
    """
    Uses NSQ as the broker.
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._nsqd_cleint = GnsqImporter().NsqdHTTPClient(BrokerConnConfig.NSQD_HTTP_CLIENT_HOST, BrokerConnConfig.NSQD_HTTP_CLIENT_PORT)
        self._producer = GnsqImporter().Producer(BrokerConnConfig.NSQD_TCP_ADDRESSES)
        self._producer.start()

    def _publish_impl(self, msg):
        # noinspection PyTypeChecker
        self._producer.publish(self._queue_name, msg.encode())

    def clear(self):
        try:
            self._nsqd_cleint.empty_topic(self._queue_name)
        except GnsqImporter().NSQHttpError as e:
            self.logger.exception(e)  # Cannot clear a non-existent topic; it will raise an error, unlike other message queue brokers.
        self.logger.warning(f'Successfully cleared messages in topic {self._queue_name}')

    def get_message_count(self):
        return -1

    def close(self):
        self._producer.close()
