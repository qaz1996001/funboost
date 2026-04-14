# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/18
"""
PostgreSQL Publisher - Native high-performance implementation
Leverages PostgreSQL's RETURNING and NOTIFY features
"""
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.queues.postgres_queue import PostgresQueue


class PostgresPublisher(AbstractPublisher):
    """
    PostgreSQL native publisher.

    Advantages over the generic SQLAlchemy implementation:
    1. Uses native psycopg2 for better performance
    2. Supports NOTIFY for real-time consumer notification
    3. Uses connection pooling for more efficient connection management
    """

    def custom_init(self):
        self._priority = self.publisher_params.broker_exclusive_config['priority']
        self._queue = PostgresQueue(
            queue_name=self._queue_name,
            dsn=BrokerConnConfig.POSTGRES_DSN,
            min_conn=self.publisher_params.broker_exclusive_config['min_connections'],
            max_conn=self.publisher_params.broker_exclusive_config['max_connections'],
        )
        self.logger.info(f"PostgreSQL Publisher initialized, queue: {self._queue_name}")

    def _publish_impl(self, msg: str):
        """Publish message, using RETURNING to get job_id"""
        # Try to get priority from message
        priority = self._priority
        try:
            import json
            msg_dict = json.loads(msg)
            if 'extra' in msg_dict and 'priority' in msg_dict.get('extra', {}).get('other_extra_params', {}):
                priority = msg_dict['extra']['other_extra_params']['priority']
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        self._queue.push(msg, priority=priority)

    def clear(self):
        """Clear the queue"""
        self._queue.clear()

    def get_message_count(self):
        """Get the number of pending messages"""
        return self._queue.get_message_count()

    def close(self):
        """Close connection"""
        self._queue.close()
