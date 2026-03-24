# -*- coding: utf-8 -*-
"""
High-performance memory queue publisher.

Supports two modes:
1. Standard mode (default): Full funboost feature support
2. Ultra-fast mode (ultra_fast_mode=True): Skips most framework overhead, publishes messages directly
   - Ultra-fast mode auto-generates simplified extra fields
   - Suitable for scenarios with extremely high performance requirements
"""
import time
import typing
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.queues.fastest_mem_queue import FastestMemQueues, FastestMemQueue
from funboost.core.msg_result_getter import AsyncResult


class FastestMemQueuePublisher(AbstractPublisher):
    """
    High-performance memory queue publisher.

    broker_exclusive_config options:
    - ultra_fast_mode: Whether to enable ultra-fast mode, default False
      Ultra-fast mode skips most framework overhead (serialization, decorators, logging, etc.), 3-5x performance improvement
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        super().custom_init()
        self._ultra_fast = self.publisher_params.broker_exclusive_config.get('ultra_fast_mode', False)
        if self._ultra_fast:
            # Ultra-fast mode: pre-generate some constants to reduce runtime overhead
            self._task_id_counter = 0
            self._count = 0
            self._last_log_time = time.time()

    @property
    def _mem_queue(self) -> FastestMemQueue:
        return FastestMemQueues.get_queue(self._queue_name)

    def publish(self, msg: typing.Union[str, dict], task_id=None, task_options=None):
        """
        Publish a message to the queue.

        In ultra-fast mode, skips most framework overhead and puts the message directly into the queue.
        """
        if self._ultra_fast:
            return self._publish_ultra_fast(msg)
        else:
            return super().publish(msg, task_id, task_options)

    def _publish_ultra_fast(self, msg: typing.Union[str, dict]):
        """
        Ultra-fast publish mode: skips serialization, decorators, logging and other overhead.
        """
        # Build message directly without any conversion
        if isinstance(msg, dict):
            # Add minimal extra field (required by consumer ultra-fast mode)
            if 'extra' not in msg:
                self._task_id_counter += 1
                msg['extra'] = {
                    'task_id': f'ultra_{self._task_id_counter}',
                    'publish_time': time.time(),
                }
            self._mem_queue.put(msg)
        else:
            # String messages go in directly
            self._mem_queue.put(msg)
        
        # Simplified counting statistics
        self._count += 1
        current_time = time.time()
        if current_time - self._last_log_time > 10:
            self.logger.info(f'[Ultra-fast mode] Published {self._count} messages to {self._queue_name} in 10 seconds')
            self._count = 0
            self._last_log_time = current_time
        
        return AsyncResult(f'ultra_{self._task_id_counter}', timeout=self.publisher_params.rpc_timeout)

    def _publish_impl(self, msg):
        self._mem_queue.put(msg)

    def clear(self):
        self._mem_queue.clear()
        self.logger.warning(f'Successfully cleared messages in high-performance memory queue {self._queue_name}')

    def get_message_count(self):
        return self._mem_queue.qsize()

    def close(self):
        pass
