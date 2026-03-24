# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:30

import amqpstorm
from funboost.consumers.base_consumer import AbstractConsumer



class RabbitmqConsumerAmqpStorm(AbstractConsumer):
    """
    Implemented using AmqpStorm, thread-safe, no locking needed.
    funboost strongly recommends using this as the message queue middleware.
    """

    # _rabbitmq_pb_cls = RabbitmqPublisherUsingAmqpStorm

    def _dispatch_task(self):
        # noinspection PyTypeChecker
        def callback(amqpstorm_message: amqpstorm.Message):
            body = amqpstorm_message.body
            # self.logger.debug(f'Message fetched from rabbitmq queue [{self._queue_name}]:  {body}')
            kw = {'amqpstorm_message': amqpstorm_message, 'body': body}
            self._submit_task(kw)

        # rp = self._rabbitmq_pb_cls(publisher_params=PublisherParams(queue_name=self.queue_name,broker_kind=self.consumer_params.broker_kind,
                                                                    # broker_exclusive_config=self.consumer_params.broker_exclusive_config))
        rp = self.bulid_a_new_publisher_of_same_queue()
        rp.init_broker()
        rp.channel_wrapper_by_ampqstormbaic.qos(max(10,self.consumer_params.concurrent_num * 2))
        rp.channel_wrapper_by_ampqstormbaic.consume(callback=callback, queue=self.queue_name, no_ack=self.consumer_params.broker_exclusive_config['no_ack'],
                                                    )
        self._rp = rp
        rp.channel.start_consuming(auto_decode=True)

    def _confirm_consume(self, kw):
        # noinspection PyBroadException
        if self.consumer_params.broker_exclusive_config['no_ack'] is False:
            try:
                kw['amqpstorm_message'].ack()  # Confirm consumption
            except BaseException as e:
                self.logger.error(f'AmqpStorm confirm consumption failed  {type(e)} {e}')

    def _requeue(self, kw):
        # amqpstorm.Message.delivery_tag
        # print(kw['amqpstorm_message'].delivery_tag)
        kw['amqpstorm_message'].nack(requeue=True)
        # kw['amqpstorm_message'].reject(requeue=True)
        # kw['amqpstorm_message'].ack()
        # self.publisher_of_same_queue.publish(kw['body'])
