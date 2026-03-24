# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2026/1/11
"""
Publisher implementation using AWS SQS as the message queue broker.
Uses the boto3 SDK to operate SQS.

AWS SQS is Amazon's managed message queue service, supporting:
- Standard queues (high throughput, at-least-once delivery)
- FIFO queues (strict ordering, exactly-once processing)
- Message visibility timeout
- Message acknowledgment and deletion mechanism

Requires boto3: pip install boto3
"""
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.funboost_config_deafult import BrokerConnConfig


class SqsPublisher(AbstractPublisher):
    """
    Publisher using AWS SQS as the message queue broker.

    Native implementation offers better performance than using SQS indirectly through kombu.
    Supports both standard and FIFO queues.
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        """Initialize SQS client and queue"""
        import boto3
        
        # Build boto3 client parameters
        client_kwargs = {
            'region_name': BrokerConnConfig.SQS_REGION_NAME,
        }
        
        # Use explicit credentials if configured
        if BrokerConnConfig.SQS_AWS_ACCESS_KEY_ID and BrokerConnConfig.SQS_AWS_SECRET_ACCESS_KEY:
            client_kwargs['aws_access_key_id'] = BrokerConnConfig.SQS_AWS_ACCESS_KEY_ID
            client_kwargs['aws_secret_access_key'] = BrokerConnConfig.SQS_AWS_SECRET_ACCESS_KEY
        
        # Use custom endpoint if configured (for LocalStack, etc.)
        if BrokerConnConfig.SQS_ENDPOINT_URL:
            client_kwargs['endpoint_url'] = BrokerConnConfig.SQS_ENDPOINT_URL
        
        self._sqs_client = boto3.client('sqs', **client_kwargs)
        
        # Get or create queue
        self._queue_url = self._get_or_create_queue()
        self.logger.info(f'SQS queue ready: {self._queue_url}')

    def _get_or_create_queue(self) -> str:
        """Get queue URL; create the queue if it doesn't exist"""
        try:
            # Try to get existing queue
            response = self._sqs_client.get_queue_url(QueueName=self._queue_name)
            return response['QueueUrl']
        except self._sqs_client.exceptions.QueueDoesNotExist:
            # Create new queue
            self.logger.info(f'SQS queue {self._queue_name} does not exist, creating...')

            # Get queue attributes from broker_exclusive_config
            broker_config = self.publisher_params.broker_exclusive_config
            visibility_timeout = broker_config['visibility_timeout']
            message_retention_period = broker_config['message_retention_period']
            
            attributes = {
                'VisibilityTimeout': str(visibility_timeout),
                'MessageRetentionPeriod': str(message_retention_period),
            }
            
            # If queue name ends with .fifo, create a FIFO queue
            if self._queue_name.endswith('.fifo'):
                attributes['FifoQueue'] = 'true'
                content_based_deduplication = broker_config['content_based_deduplication']
                attributes['ContentBasedDeduplication'] = 'true' if content_based_deduplication else 'false'
            
            response = self._sqs_client.create_queue(
                QueueName=self._queue_name,
                Attributes=attributes
            )
            return response['QueueUrl']

    def _publish_impl(self, msg: str):
        """Publish message to SQS queue"""
        send_kwargs = {
            'QueueUrl': self._queue_url,
            'MessageBody': msg,
        }
        
        # FIFO queues require MessageGroupId
        if self._queue_name.endswith('.fifo'):
            # Use queue name as default message group ID to ensure message ordering within the same queue
            send_kwargs['MessageGroupId'] = self._queue_name
        
        self._sqs_client.send_message(**send_kwargs)

    def clear(self):
        """Clear all messages in the queue"""
        try:
            self._sqs_client.purge_queue(QueueUrl=self._queue_url)
            self.logger.warning(f'Cleared all messages in SQS queue {self._queue_name}')
        except Exception as e:
            # PurgeQueue has a 60-second cooldown period; may fail if recently purged
            self.logger.error(f'Failed to clear queue: {e}')

    def get_message_count(self) -> int:
        """Get the number of messages in the queue (approximate)"""
        response = self._sqs_client.get_queue_attributes(
            QueueUrl=self._queue_url,
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )
        attrs = response['Attributes']
        # Return visible messages + messages being processed
        visible = int(attrs['ApproximateNumberOfMessages'])
        not_visible = int(attrs['ApproximateNumberOfMessagesNotVisible'])
        return visible + not_visible

    def close(self):
        """Clean up resources"""
        # boto3 client doesn't need explicit closing
        pass
