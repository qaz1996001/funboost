# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2026/1/11
"""
Consumer implementation using AWS SQS as message queue middleware.
Uses the boto3 SDK to operate SQS.

Supports:
- Long Polling to reduce empty polling
- Batch message pulling for improved efficiency
- Message acknowledgment (implemented by deleting messages)
- Message requeue

Install boto3 before use: pip install boto3
"""
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.sqs_publisher import SqsPublisher
from funboost.core.func_params_model import PublisherParams


class SqsConsumer(AbstractConsumer):
    """
    Consumer using AWS SQS as message queue middleware.

    Supports message acknowledgment via deletion to ensure messages are not lost.
    Supports message requeue on consumption failure.
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        """Initialize SQS client"""
        import boto3

        # Build boto3 client parameters
        client_kwargs = {
            'region_name': BrokerConnConfig.SQS_REGION_NAME,
        }

        # Use explicit credentials if configured
        if BrokerConnConfig.SQS_AWS_ACCESS_KEY_ID and BrokerConnConfig.SQS_AWS_SECRET_ACCESS_KEY:
            client_kwargs['aws_access_key_id'] = BrokerConnConfig.SQS_AWS_ACCESS_KEY_ID
            client_kwargs['aws_secret_access_key'] = BrokerConnConfig.SQS_AWS_SECRET_ACCESS_KEY

        # Use custom endpoint if configured (e.g. for LocalStack)
        if BrokerConnConfig.SQS_ENDPOINT_URL:
            client_kwargs['endpoint_url'] = BrokerConnConfig.SQS_ENDPOINT_URL

        self._sqs_client = boto3.client('sqs', **client_kwargs)

        # Get queue URL (using publisher method to ensure queue exists)
        self._sqs_publisher = SqsPublisher(publisher_params=PublisherParams(queue_name=self.queue_name))
        self._queue_url = self._sqs_publisher._queue_url

        # Get configuration from broker_exclusive_config
        self._wait_time_seconds = self.consumer_params.broker_exclusive_config['wait_time_seconds']  # Long polling wait time
        self._max_number_of_messages = self.consumer_params.broker_exclusive_config['max_number_of_messages']  # Max messages per pull
        self._visibility_timeout = self.consumer_params.broker_exclusive_config['visibility_timeout']  # Visibility timeout (seconds)

    def _dispatch_task(self):
        """Pull messages from SQS queue and submit tasks"""
        while True:

            # Receive messages using long polling
            response = self._sqs_client.receive_message(
                QueueUrl=self._queue_url,
                MaxNumberOfMessages=self._max_number_of_messages,
                WaitTimeSeconds=self._wait_time_seconds,
                VisibilityTimeout=self._visibility_timeout,
                AttributeNames=['All'],
                MessageAttributeNames=['All']
            )

            messages = response.get('Messages', [])

            if messages:
                self._print_message_get_from_broker([msg['Body'] for msg in messages])

                for message in messages:
                    # Build task keyword arguments
                    kw = {
                        'body': message['Body'],
                        'receipt_handle': message['ReceiptHandle'],  # Used for consumption confirmation
                        'message_id': message['MessageId'],
                    }
                    self._submit_task(kw)
            # When there are no messages, long polling has already waited WaitTimeSeconds, no additional sleep needed


    def _confirm_consume(self, kw):
        """
        Confirm message consumption.

        In SQS, confirming consumption is implemented by deleting the message.
        If not deleted, the message will become visible again after VisibilityTimeout.
        """
        receipt_handle = kw['receipt_handle']
        try:
            self._sqs_client.delete_message(
                QueueUrl=self._queue_url,
                ReceiptHandle=receipt_handle
            )
        except Exception as e:
            self.logger.error(f'Consumption confirmation (message deletion) failed: {e}')

    def _requeue(self, kw):
        """
        Requeue the message.

        Since SQS messages automatically become visible again after VisibilityTimeout,
        we can either:
        1. Immediately change message visibility to 0, making it visible right away
        2. Or re-send the message to the queue

        Option 2 is used here as it is more reliable and preserves the original message body.
        """
        body = kw['body']
        # Re-send the message
        self._sqs_publisher.publish(body)

        # Delete the original message (to avoid duplicates)
        receipt_handle = kw['receipt_handle']
        try:
            self._sqs_client.delete_message(
                QueueUrl=self._queue_url,
                ReceiptHandle=receipt_handle
            )
        except Exception as e:
            self.logger.error(f'Consumption confirmation (message deletion) failed: {e}, body:{body}')
            pass  # Ignore deletion failure, as the message may have already timed out

