# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2026/1/11
"""
使用 amqp 包实现的高性能 RabbitMQ Consumer。
amqp 是 Celery/Kombu 底层使用的 AMQP 客户端，性能比 pika 更好。

安装：pip install amqp (通常已随 celery/kombu 安装)
"""
import socket
import time
from funboost.consumers.base_consumer import AbstractConsumer


class RabbitmqAmqpConsumer(AbstractConsumer):
    """
    Implemented using the amqp package, a high-performance AMQP client.
    amqp is the underlying dependency of Celery/Kombu, with better performance than pika.
    """

    def _dispatch_task(self):
        def callback(message):
            """Message callback handler"""
            body = message.body
            if isinstance(body, bytes):
                body = body.decode('utf-8')
            kw = {'message': message, 'body': body, 'channel': rp.channel}
            self._submit_task(kw)

        # Reuse publisher's connection and channel
        rp = self.bulid_a_new_publisher_of_same_queue()
        rp.init_broker()

        # Set prefetch to control the number of messages prefetched by the consumer at once
        rp.channel.basic_qos(
            prefetch_size=0,
            prefetch_count=self.consumer_params.concurrent_num * 2,
            a_global=False
        )

        # Start consuming
        no_ack = self.consumer_params.broker_exclusive_config['no_ack']
        rp.channel.basic_consume(
            queue=self.queue_name,
            callback=callback,
            no_ack=no_ack,
        )

        self._rp = rp

        self.logger.info(f'amqp started consuming queue {self.queue_name}')

        # Heartbeat interval (seconds), set to a value smaller than the server heartbeat timeout
        heartbeat_interval = 5
        last_heartbeat_time = time.time()
        
        while True:
            try:
                # drain_events 使用较短超时，以便及时发送心跳
                rp.connection.drain_events(timeout=heartbeat_interval)
            except socket.timeout:
                # Timeout is normal, continue loop
                pass
            except OSError as e:
                # Connection reset, try reconnecting
                self.logger.error(f'amqp connection error: {type(e).__name__} {e}')
                self._reconnect(rp, callback, no_ack)
                last_heartbeat_time = time.time()
                continue
            except Exception as e:
                exc_name = type(e).__name__
                # Check if it's a connection-related exception (needs reconnection)
                if ('Connection' in exc_name or 'Channel' in exc_name or 'AMQP' in exc_name or
                    'Recoverable' in exc_name):
                    self.logger.error(f'amqp connection/channel error: {exc_name} {e}, triggering reconnection')
                    self._reconnect(rp, callback, no_ack)
                    last_heartbeat_time = time.time()
                    continue
                elif 'PreconditionFailed' in exc_name:
                    # PreconditionFailed usually occurs during ack/reject, already handled in _confirm_consume
                    self.logger.debug(f'amqp drain_events PreconditionFailed (already handled): {e}')
                else:
                    self.logger.error(f'amqp drain_events error: {exc_name} {e}')
            
            # Actively send heartbeat
            try:
                current_time = time.time()
                if current_time - last_heartbeat_time >= heartbeat_interval:
                    # amqp package heartbeat check
                    rp.connection.heartbeat_tick()
                    last_heartbeat_time = current_time
            except Exception as e:
                self.logger.warning(f'Failed to send heartbeat: {e}')
    
    def _reconnect(self, rp, callback, no_ack):
        """Reconnection logic"""
        try:
            time.sleep(5)
            rp.has_init_broker = 0  # 重置初始化标志
            rp.init_broker()
            rp.channel.basic_qos(
                prefetch_size=0,
                prefetch_count=self.consumer_params.concurrent_num,
                a_global=False
            )
            rp.channel.basic_consume(
                queue=self.queue_name,
                callback=callback,
                no_ack=no_ack,
            )
            self.logger.info('amqp reconnection successful')
        except Exception as reconnect_error:
            self.logger.error(f'amqp reconnection failed: {reconnect_error}')
            time.sleep(5)

    def _confirm_consume(self, kw):
        """Confirm consumption"""
        if self.consumer_params.broker_exclusive_config['no_ack'] is False:
            try:
                # Use the current valid channel for ack (channel may change after reconnection)
                self._rp.channel.basic_ack(kw['message'].delivery_tag)
            except Exception as e:
                exc_name = type(e).__name__
                # PreconditionFailed means delivery tag is invalid (caused by reconnection), message will be automatically redelivered by RabbitMQ
                if 'PreconditionFailed' in exc_name:
                    self.logger.debug(f'amqp ack skipped (delivery tag invalid, message will be redelivered): {e}')
                else:
                    self.logger.error(f'amqp confirm consumption failed {exc_name} {e}')

    def _requeue(self, kw):
        """Requeue"""
        try:
            # Use the current valid channel for reject (channel may change after reconnection)
            self._rp.channel.basic_reject(kw['message'].delivery_tag, requeue=True)
        except Exception as e:
            exc_name = type(e).__name__
            # PreconditionFailed means delivery tag is invalid, message will be automatically redelivered by RabbitMQ
            if 'PreconditionFailed' in exc_name:
                self.logger.debug(f'amqp requeue skipped (delivery tag invalid, message will be redelivered): {e}')
            else:
                self.logger.error(f'amqp requeue failed {exc_name} {e}')
