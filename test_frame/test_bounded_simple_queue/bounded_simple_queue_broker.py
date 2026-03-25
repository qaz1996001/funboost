# -*- coding: utf-8 -*-
"""
Publisher and Consumer implementation using Bounded SimpleQueue as a Broker.

This follows funboost documentation section 4.21 to dynamically extend brokers in user code,
without modifying the funboost/publishers and funboost/consumers directories.

Usage:
1. Import this module (the broker will be auto-registered)
2. Use broker_kind='BOUNDED_SIMPLE_QUEUE' in the @boost decorator
"""

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.factories.broker_kind__publsiher_consumer_type_map import register_custom_broker
from test_frame.test_bounded_simple_queue.bounded_simple_queue import BoundedSimpleQueues, BoundedSimpleQueue
from funboost.core.broker_kind__exclusive_config_default_define import register_broker_exclusive_config_default


# ============================================================================
# Broker type constant
# ============================================================================
BOUNDED_SIMPLE_QUEUE = 'BOUNDED_SIMPLE_QUEUE'


# ============================================================================
# Publisher implementation
# ============================================================================
class BoundedSimpleQueuePublisher(AbstractPublisher):
    """
    Bounded SimpleQueue publisher.

    Supported broker_exclusive_config options:
    - maxsize: maximum queue capacity, default 10000
    """

    @property
    def _bounded_queue(self) -> BoundedSimpleQueue:
        maxsize = self.publisher_params.broker_exclusive_config['maxsize']
        return BoundedSimpleQueues.get_queue(self._queue_name, maxsize=maxsize)

    def _publish_impl(self, msg):
        """Publish a message to the bounded queue"""
        self._bounded_queue.put(msg)

    def clear(self):
        """Clear the queue"""
        self._bounded_queue.clear()
        self.logger.warning(f'Successfully cleared messages in queue {self._queue_name}')

    def get_message_count(self):
        """Get the number of messages in the queue"""
        return self._bounded_queue.qsize()

    def close(self):
        """Close connection (in-memory queue does not need closing)"""
        pass


# ============================================================================
# Consumer implementation
# ============================================================================
class BoundedSimpleQueueConsumer(AbstractConsumer):
    """
    Bounded SimpleQueue consumer.

    Supported broker_exclusive_config options:
    - maxsize: maximum queue capacity, default 10000
    """

    @property
    def _bounded_queue(self) -> BoundedSimpleQueue:
        maxsize = self.consumer_params.broker_exclusive_config['maxsize']
        return BoundedSimpleQueues.get_queue(self._queue_name, maxsize=maxsize)

    def _dispatch_task(self):
        """Retrieve messages from the queue and submit tasks"""
        while True:
            task = self._bounded_queue.get()
            kw = {'body': task}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        """Confirm consumption (in-memory queue does not need ack)"""
        pass

    def _requeue(self, kw):
        """Requeue message"""
        self._bounded_queue.put(kw['body'])


# ============================================================================
# Auto-register Broker
# ============================================================================
def register_bounded_simple_queue_broker():
    """
    Register Bounded SimpleQueue as a funboost broker.

    After calling this function, you can use in @boost:
    broker_kind='BOUNDED_SIMPLE_QUEUE'

    Supported broker_exclusive_config options:
    - maxsize: maximum queue capacity, default 10000
    """
    # 1. Register broker-specific config defaults
    register_broker_exclusive_config_default(
        BOUNDED_SIMPLE_QUEUE,
        {
            "maxsize": 10000,  # maximum queue capacity
        }
    )

    # 2. Register publisher and consumer
    register_custom_broker(
        broker_kind=BOUNDED_SIMPLE_QUEUE,
        publisher_class=BoundedSimpleQueuePublisher,
        consumer_class=BoundedSimpleQueueConsumer
    )


# Auto-register on module import
register_bounded_simple_queue_broker()
