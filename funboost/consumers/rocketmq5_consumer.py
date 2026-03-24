# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2026
"""
RocketMQ 5.x 消费者实现，使用最新版 rocketmq-python-client SDK
pip install rocketmq-python-client

使用 SimpleConsumer 模式：
- 支持单条消息乱序 ACK，不依赖 offset
- 基于 gRPC 协议，纯 Python 实现
- 支持 Windows / Linux / macOS
"""


"""
AI-generated, needs testing when time permits
"""

import time

from funboost.consumers.base_consumer import AbstractConsumer

# pip install rocketmq-python-client
try:
    from rocketmq import ClientConfiguration, Credentials, FilterExpression, SimpleConsumer
except ImportError:
    raise ImportError(
        'The rocketmq-python-client package is required: pip install rocketmq-python-client\n'
        'This is the official Python SDK for RocketMQ 5.x, supporting Windows/Linux/macOS'
    )
class RocketmqConsumer(AbstractConsumer):
    """
    RocketMQ 5.x 消费者，使用 SimpleConsumer 模式
    
    安装方式:
        pip install rocketmq-python-client
        
    特性: 
        - SimpleConsumer 模式：支持单条消息乱序 ACK，不依赖 offset
        - 基于 gRPC 协议，纯 Python 实现
        - 支持 Windows / Linux / macOS
        - 支持 RocketMQ 5.x 版本
        - 消息重入队使用原生 invisible_duration 机制，不 ACK 的消息超时后自动重新可见
        
    broker_exclusive_config configurable parameters:
        - endpoints: RocketMQ gRPC endpoint address, default '127.0.0.1:8081'
        - consumer_group: Consumer group name, default 'funboost_consumer_group'
        - access_key: Access key (optional)
        - secret_key: Secret key (optional)
        - namespace: Namespace (optional)
        - invisible_duration: Message invisible time (seconds), messages are invisible to other consumers during this time after being fetched, default 15
        - max_message_num: Maximum messages per pull, default 32
        - tag: Message filter tag, default '*' means no filtering
    """

    def custom_init(self):
        self._consumer = None

    def _dispatch_task(self):
        """Pull messages from RocketMQ and dispatch to concurrent pool for execution"""
        

        # Get configuration parameters
        endpoints = self.consumer_params.broker_exclusive_config['endpoints']
        consumer_group = self.consumer_params.broker_exclusive_config['consumer_group']
        access_key = self.consumer_params.broker_exclusive_config['access_key']
        secret_key = self.consumer_params.broker_exclusive_config['secret_key']
        namespace = self.consumer_params.broker_exclusive_config['namespace']
        invisible_duration = self.consumer_params.broker_exclusive_config['invisible_duration']
        max_message_num = self.consumer_params.broker_exclusive_config['max_message_num']
        tag = self.consumer_params.broker_exclusive_config['tag']

        # Create credentials
        if access_key and secret_key:
            credentials = Credentials(access_key, secret_key)
        else:
            credentials = Credentials()

        # Create client configuration
        if namespace:
            config = ClientConfiguration(endpoints, credentials, namespace)
        else:
            config = ClientConfiguration(endpoints, credentials)

        # Create subscription expression
        if tag and tag != '*':
            filter_expression = FilterExpression(tag)
        else:
            filter_expression = FilterExpression()

        # Create SimpleConsumer
        self._consumer = SimpleConsumer(
            config,
            consumer_group,
            {self._queue_name: filter_expression}
        )

        self.logger.info(
            f'RocketMQ 5.x SimpleConsumer starting, consumer_group: {consumer_group}, '
            f'topic: {self._queue_name}, endpoints: {endpoints}, invisible_duration: {invisible_duration}s'
        )

        # Start consumer
        self._consumer.startup()
        self.logger.info(f'RocketMQ 5.x SimpleConsumer started and subscribed to topic: {self._queue_name}')

        # SimpleConsumer pull-mode consumption loop
        while True:
            try:
                # Pull messages
                # receive(max_message_num, invisible_duration_seconds)
                messages = self._consumer.receive(max_message_num, invisible_duration)
                
                if messages is None:
                    continue
                    
                for msg in messages:
                    # Build kw dict, containing message and ACK info
                    try:
                        body = msg.body.decode('utf-8') if isinstance(msg.body, bytes) else msg.body
                    except (UnicodeDecodeError, AttributeError):
                        body = msg.body
                        
                    kw = {
                        'body': body,
                        'rocketmq_msg': msg,  # Save original message object for ACK
                        'message_id': msg.message_id,
                    }
                    self._submit_task(kw)
                    
            except Exception as e:
                self.logger.error(f'RocketMQ SimpleConsumer error pulling messages: {e}', exc_info=True)
                time.sleep(1)

    def _confirm_consume(self, kw):
        """
        Confirm consumption - SimpleConsumer supports out-of-order ACK for individual messages.
        Each message can be independently acknowledged, not dependent on offset.
        """
        msg = kw.get('rocketmq_msg')
        if msg and self._consumer:
            try:
                self._consumer.ack(msg)
            except Exception as e:
                self.logger.error(f'RocketMQ ACK message failed: {e}', exc_info=True)

    def _requeue(self, kw):
        """
        Requeue message - Uses RocketMQ's native invisible_duration mechanism.

        Sets the message's invisible time to 0 via change_invisible_duration,
        making the message immediately visible again for re-consumption.

        If the SDK does not support change_invisible_duration, no action is taken
        and the message will automatically become visible after the invisible_duration timeout.
        """
        msg = kw.get('rocketmq_msg')
        if msg and self._consumer:
            try:
                # 尝试使用 change_invisible_duration 立即让消息重新可见
                self._consumer.change_invisible_duration(msg, 0)
                self.logger.debug(f'RocketMQ message {msg.message_id} has been set to immediately visible')
            except AttributeError:
                # SDK does not support change_invisible_duration, message will automatically become visible after invisible_duration timeout
                self.logger.debug(
                    f'RocketMQ message {msg.message_id} will automatically become visible after invisible_duration timeout'
                )
            except Exception as e:
                self.logger.warning(f'RocketMQ change_invisible_duration failed: {e}, message will automatically become visible after timeout')
