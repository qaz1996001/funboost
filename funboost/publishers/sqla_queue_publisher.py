# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:05
from funboost.queues import sqla_queue
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher


# noinspection PyProtectedMember
class SqlachemyQueuePublisher(AbstractPublisher):
    """
    Uses SQLAlchemy to operate databases, implementing 5 types of SQL database servers as message queues, including SQLite, MySQL, Microsoft SQL Server, PostgreSQL, and Oracle.
    This simulates a message queue using database tables. This is not a whimsical idea; many packages have implemented this.
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self.queue = sqla_queue.SqlaQueue(self._queue_name, BrokerConnConfig.SQLACHEMY_ENGINE_URL)

    def _publish_impl(self, msg):
        self.queue.push(dict(body=msg, status=sqla_queue.TaskStatus.TO_BE_CONSUMED))

    def clear(self):
        self.queue.clear_queue()
        self.logger.warning(f'Successfully cleared messages in sqlalchemy database queue {self._queue_name}')

    def get_message_count(self):
        return self.queue.to_be_consumed_count

    def close(self):
        pass
