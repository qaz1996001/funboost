
from funboost import BoostersManager, PublisherParams, BrokerEnum, TaskOptions

BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING
EXCHANGE_NAME = 'direct_log_exchange'



if __name__ == '__main__':
    # Optimization: get a generic publisher targeting the exchange rather than any specific queue.
    # The queue_name here is only used to generate the publisher instance; it will be overridden by the dynamic routing key when publishing.
    common_publisher = BoostersManager.get_cross_project_publisher(PublisherParams(
        queue_name='common_publisher_for_direct_exchange',
        broker_kind=BROKER_KIND_FOR_TEST,
        broker_exclusive_config={
            'exchange_name': EXCHANGE_NAME,
            'exchange_type': 'direct',
            # The publisher does not need to know the binding key, but you can set a default publish routing key if needed
            # 'routing_key_for_publish': 'info'
        }
    ))

    for i in range(10):
        # Publish an info message with routing key 'info'; only info_fun will receive it
        common_publisher.publish({'msg': f'This is a regular INFO message {i}'},
                                 task_options=TaskOptions(
                                     other_extra_params={'routing_key_for_publish': 'info'}))

        # Publish an error message with routing key 'error'; only error_fun will receive it
        common_publisher.publish({'msg': f'This is a serious ERROR message {i}'},
                                 task_options=TaskOptions(
                                     other_extra_params={'routing_key_for_publish': 'error'}))
