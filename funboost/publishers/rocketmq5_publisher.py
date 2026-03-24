# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2026
"""
RocketMQ 5.x publisher implementation using the latest rocketmq-python-client SDK.
pip install rocketmq-python-client

Supports RocketMQ 5.x version, based on gRPC protocol.
Supports Windows / Linux / macOS.
"""

"""
AI-generated, needs testing when time permits.
"""

import time

from funboost.publishers.base_publisher import AbstractPublisher

# pip install rocketmq-python-client
from rocketmq import ClientConfiguration, Credentials, Producer, Message


class RocketmqPublisher(AbstractPublisher):
    """
    RocketMQ 5.x publisher using the rocketmq-python-client package.

    Installation:
        pip install rocketmq-python-client

    Features:
        - Based on gRPC protocol, pure Python implementation
        - Supports Windows / Linux / macOS
        - Supports RocketMQ 5.x version
        - Supports automatic Topic creation
    """

    _topic__rocketmq_producer = {}
    _created_topics = set()  # Track already created topics

    def custom_init(self):
        if self._queue_name not in self.__class__._topic__rocketmq_producer:
            # Get configuration
            endpoints = self.publisher_params.broker_exclusive_config['endpoints']
            access_key = self.publisher_params.broker_exclusive_config['access_key']
            secret_key = self.publisher_params.broker_exclusive_config['secret_key']
            namespace = self.publisher_params.broker_exclusive_config['namespace']
            
            # Auto-create Topic
            self._auto_create_topic(endpoints)
            
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
            
            # Create Producer
            producer = Producer(config, [self._queue_name])
            producer.startup()
            
            self.__class__._topic__rocketmq_producer[self._queue_name] = producer
            self.logger.info(f'RocketMQ 5.x Producer started, topic: {self._queue_name}, endpoints: {endpoints}')
        
        self._producer = self.__class__._topic__rocketmq_producer[self._queue_name]

    def _auto_create_topic(self, endpoints: str):
        """
        Auto-create Topic via HTTP API.
        """
        if self._queue_name in self.__class__._created_topics:
            return
        
        host = endpoints.split(':')[0]
        namesrv_addr = self.publisher_params.broker_exclusive_config.get('namesrv_addr') or f'{host}:9876'
        cluster_name = self.publisher_params.broker_exclusive_config.get('cluster_name', 'DefaultCluster')
        
        try:
            self._create_topic_via_http(host, namesrv_addr, cluster_name)
        except Exception as e:
            self.logger.warning(
                f'Failed to auto-create Topic: {e}\n'
                f'Please create manually: docker exec -it rmq-broker sh mqadmin updateTopic -n localhost:9876 -t {self._queue_name} -c {cluster_name}'
            )

    def _create_topic_via_http(self, host: str, namesrv_addr: str, cluster_name: str):
        """Create Topic via HTTP API"""
        import urllib.request
        import urllib.parse
        import json
        
        # Try multiple possible ports and APIs
        apis_to_try = [
            # RocketMQ Dashboard API
            (8080, '/topic/createOrUpdate', 'form'),
            # Broker HTTP API  
            (10911, '/topic/createOrUpdate', 'form'),
        ]
        
        for port, path, content_type in apis_to_try:
            try:
                url = f'http://{host}:{port}{path}'
                
                if content_type == 'form':
                    data = urllib.parse.urlencode({
                        'topic': self._queue_name,
                        'clusterName': cluster_name,
                        'readQueueNums': 8,
                        'writeQueueNums': 8,
                    }).encode()
                    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                else:
                    data = json.dumps({
                        'topic': self._queue_name,
                        'clusterName': cluster_name,
                        'readQueueNums': 8,
                        'writeQueueNums': 8,
                    }).encode()
                    headers = {'Content-Type': 'application/json'}
                
                req = urllib.request.Request(url, data=data, method='POST', headers=headers)
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        self.logger.info(f'Successfully created Topic via HTTP API ({host}:{port}): {self._queue_name}')
                        self.__class__._created_topics.add(self._queue_name)
                        return
            except Exception:
                continue
        
        # All methods failed
        self.logger.warning(
            f'Unable to auto-create Topic: {self._queue_name}\n'
            f'Please execute manually: docker exec -it <container> sh mqadmin updateTopic -n {namesrv_addr} -t {self._queue_name} -c {cluster_name}'
        )

    def _publish_impl(self, msg: str):
        """Publish message to RocketMQ Topic"""
        message = Message()
        message.topic = self._queue_name
        message.body = msg.encode('utf-8') if isinstance(msg, str) else msg
        self._producer.send(message)

    def clear(self):
        """Clear queue - RocketMQ does not support deleting messages via Python SDK"""
        self.logger.warning(
            'RocketMQ Python SDK does not support clearing queue/deleting messages. '
            'To clear, please use RocketMQ Console or Admin API.'
        )

    def get_message_count(self):
        """Get queue message count - RocketMQ Python SDK does not directly support this feature"""
        if time.time() - getattr(self, '_last_warning_count', 0) > 300:
            setattr(self, '_last_warning_count', time.time())
            self.logger.debug(
                'RocketMQ Python SDK does not yet support getting queue message count. '
                'To check, please use RocketMQ Console.'
            )
        return -1

    def close(self):
        """Close producer connection"""
        pass
