import typing

from funboost.publishers.empty_publisher import EmptyPublisher

from funboost.publishers.nats_publisher import NatsPublisher
from funboost.publishers.peewee_publisher import PeeweePublisher
from funboost.publishers.redis_publisher_lpush import RedisPublisherLpush
from funboost.publishers.redis_publisher_priority import RedisPriorityPublisher
from funboost.publishers.redis_pubsub_publisher import RedisPubSubPublisher
from funboost.publishers.tcp_publisher import TCPPublisher
from funboost.publishers.txt_file_publisher import TxtFilePublisher
from funboost.publishers.udp_publisher import UDPPublisher
from funboost.publishers.zeromq_publisher import ZeroMqPublisher
from funboost.publishers.kafka_publisher import KafkaPublisher
from funboost.publishers.local_python_queue_publisher import LocalPythonQueuePublisher
from funboost.publishers.fastest_mem_queue_publisher import FastestMemQueuePublisher
from funboost.publishers.mongomq_publisher import MongoMqPublisher

from funboost.publishers.persist_queue_publisher import PersistQueuePublisher

from funboost.publishers.rabbitmq_pika_publisher import RabbitmqPublisher

from funboost.publishers.redis_publisher import RedisPublisher

from funboost.publishers.redis_stream_publisher import RedisStreamPublisher
from funboost.publishers.mqtt_publisher import MqttPublisher
from funboost.publishers.httpsqs_publisher import HttpsqsPublisher

from funboost.consumers.empty_consumer import EmptyConsumer
from funboost.consumers.redis_consumer_priority import RedisPriorityConsumer
from funboost.consumers.redis_pubsub_consumer import RedisPbSubConsumer

from funboost.consumers.kafka_consumer import KafkaConsumer
from funboost.consumers.local_python_queue_consumer import LocalPythonQueueConsumer
from funboost.consumers.fastest_mem_queue_consumer import FastestMemQueueConsumer
from funboost.consumers.mongomq_consumer import MongoMqConsumer
from funboost.consumers.nats_consumer import NatsConsumer

from funboost.consumers.peewee_conusmer import PeeweeConsumer
from funboost.consumers.persist_queue_consumer import PersistQueueConsumer
from funboost.consumers.rabbitmq_pika_consumer import RabbitmqConsumer

from funboost.consumers.redis_brpoplpush_consumer import RedisBrpopLpushConsumer
from funboost.consumers.redis_consumer import RedisConsumer
from funboost.consumers.redis_consumer_ack_able import RedisConsumerAckAble

from funboost.consumers.redis_stream_consumer import RedisStreamConsumer
from funboost.consumers.tcp_consumer import TCPConsumer
from funboost.consumers.txt_file_consumer import TxtFileConsumer
from funboost.consumers.udp_consumer import UDPConsumer
from funboost.consumers.zeromq_consumer import ZeroMqConsumer
from funboost.consumers.mqtt_consumer import MqttConsumer
from funboost.consumers.httpsqs_consumer import HttpsqsConsumer
from funboost.consumers.redis_consumer_ack_using_timeout import RedisConsumerAckUsingTimeout

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.constant import BrokerEnum

broker_kind__publsiher_consumer_type_map = {


    BrokerEnum.REDIS: (RedisPublisher, RedisConsumer),
    BrokerEnum.MEMORY_QUEUE: (LocalPythonQueuePublisher, LocalPythonQueueConsumer),
    BrokerEnum.FASTEST_MEM_QUEUE: (FastestMemQueuePublisher, FastestMemQueueConsumer),
    BrokerEnum.RABBITMQ_PIKA: (RabbitmqPublisher, RabbitmqConsumer),
    BrokerEnum.MONGOMQ: (MongoMqPublisher, MongoMqConsumer),
    BrokerEnum.PERSISTQUEUE: (PersistQueuePublisher, PersistQueueConsumer),
    BrokerEnum.KAFKA: (KafkaPublisher, KafkaConsumer),
    BrokerEnum.REDIS_ACK_ABLE: (RedisPublisher, RedisConsumerAckAble),
    BrokerEnum.REDIS_PRIORITY: (RedisPriorityPublisher, RedisPriorityConsumer),

    BrokerEnum.REDIS_STREAM: (RedisStreamPublisher, RedisStreamConsumer),
    BrokerEnum.ZEROMQ: (ZeroMqPublisher, ZeroMqConsumer),
    BrokerEnum.REDIS_BRPOP_LPUSH: (RedisPublisherLpush, RedisBrpopLpushConsumer),
    BrokerEnum.MQTT: (MqttPublisher, MqttConsumer),
    BrokerEnum.HTTPSQS: (HttpsqsPublisher, HttpsqsConsumer),
    BrokerEnum.UDP: (UDPPublisher, UDPConsumer),
    BrokerEnum.TCP: (TCPPublisher, TCPConsumer),

    BrokerEnum.NATS: (NatsPublisher, NatsConsumer),
    BrokerEnum.TXT_FILE: (TxtFilePublisher, TxtFileConsumer),
    BrokerEnum.PEEWEE: (PeeweePublisher, PeeweeConsumer),
    BrokerEnum.REDIS_PUBSUB: (RedisPubSubPublisher, RedisPbSubConsumer),
    BrokerEnum.REIDS_ACK_USING_TIMEOUT: (RedisPublisher, RedisConsumerAckUsingTimeout),
    BrokerEnum.EMPTY:(EmptyPublisher,EmptyConsumer),

}

for broker_kindx, cls_tuple in broker_kind__publsiher_consumer_type_map.items():
    cls_tuple[1].BROKER_KIND = broker_kindx


def register_custom_broker(broker_kind, publisher_class: typing.Type[AbstractPublisher], consumer_class: typing.Type[AbstractConsumer]):
    """
    Dynamically register a broker into the framework, making it easy to add broker types or customize consumer logic.
    :param broker_kind:
    :param publisher_class:
    :param consumer_class:
    :return:
    """
    if not issubclass(publisher_class, AbstractPublisher):
        raise TypeError(f'publisher_class must be a subclass of AbstractPublisher')
    if not issubclass(consumer_class, AbstractConsumer):
        raise TypeError(f'consumer_class must be a subclass of AbstractConsumer')
    broker_kind__publsiher_consumer_type_map[broker_kind] = (publisher_class, consumer_class)
    consumer_class.BROKER_KIND = broker_kind


def regist_to_funboost(broker_kind: str):
    """
    Not defined directly in broker_kind__publsiher_consumer_type_map; lazy imports are used because funboost does not
    automatically pip install these third-party packages, preventing errors on startup.
    This way, when users need to use certain third-party broker packages as message queues, they can pip install them
    based on the import error messages, or use `pip install funboost[all]` to install all broker dependencies at once.
    It is recommended to install third-party package versions according to extra_brokers and install_requires in
    https://github.com/ydf0509/funboost/blob/master/setup.py.
    """
    if broker_kind == BrokerEnum.RABBITMQ_AMQPSTORM:
        from funboost.publishers.rabbitmq_amqpstorm_publisher import RabbitmqPublisherUsingAmqpStorm
        from funboost.consumers.rabbitmq_amqpstorm_consumer import RabbitmqConsumerAmqpStorm
        register_custom_broker(BrokerEnum.RABBITMQ_AMQPSTORM, RabbitmqPublisherUsingAmqpStorm, RabbitmqConsumerAmqpStorm)

    if broker_kind == BrokerEnum.RABBITMQ_COMPLEX_ROUTING:
        from funboost.publishers.rabbitmq_complex_routing_publisher import RabbitmqComplexRoutingPublisher
        from funboost.consumers.rabbitmq_complex_routing_consumer import RabbitmqComplexRoutingConsumer
        register_custom_broker(BrokerEnum.RABBITMQ_COMPLEX_ROUTING, RabbitmqComplexRoutingPublisher, RabbitmqComplexRoutingConsumer)

    if broker_kind == BrokerEnum.RABBITMQ_RABBITPY:
        from funboost.publishers.rabbitmq_rabbitpy_publisher import RabbitmqPublisherUsingRabbitpy
        from funboost.consumers.rabbitmq_rabbitpy_consumer import RabbitmqConsumerRabbitpy
        register_custom_broker(BrokerEnum.RABBITMQ_RABBITPY, RabbitmqPublisherUsingRabbitpy, RabbitmqConsumerRabbitpy)

    if broker_kind == BrokerEnum.PULSAR:
        from funboost.consumers.pulsar_consumer import PulsarConsumer
        from funboost.publishers.pulsar_publisher import PulsarPublisher
        register_custom_broker(BrokerEnum.PULSAR, PulsarPublisher, PulsarConsumer)

    if broker_kind == BrokerEnum.CELERY:
        from funboost.consumers.celery_consumer import CeleryConsumer
        from funboost.publishers.celery_publisher import CeleryPublisher
        register_custom_broker(BrokerEnum.CELERY, CeleryPublisher, CeleryConsumer)

    if broker_kind == BrokerEnum.NAMEKO:
        from funboost.consumers.nameko_consumer import NamekoConsumer
        from funboost.publishers.nameko_publisher import NamekoPublisher
        register_custom_broker(BrokerEnum.NAMEKO, NamekoPublisher, NamekoConsumer)

    if broker_kind == BrokerEnum.SQLACHEMY:
        from funboost.consumers.sqlachemy_consumer import SqlachemyConsumer
        from funboost.publishers.sqla_queue_publisher import SqlachemyQueuePublisher
        register_custom_broker(BrokerEnum.SQLACHEMY, SqlachemyQueuePublisher, SqlachemyConsumer)

    if broker_kind == BrokerEnum.DRAMATIQ:
        from funboost.consumers.dramatiq_consumer import DramatiqConsumer
        from funboost.publishers.dramatiq_publisher import DramatiqPublisher
        register_custom_broker(BrokerEnum.DRAMATIQ, DramatiqPublisher, DramatiqConsumer)

    if broker_kind == BrokerEnum.HUEY:
        from funboost.consumers.huey_consumer import HueyConsumer
        from funboost.publishers.huey_publisher import HueyPublisher
        register_custom_broker(BrokerEnum.HUEY, HueyPublisher, HueyConsumer)

    if broker_kind == BrokerEnum.KAFKA_CONFLUENT:
        from funboost.consumers.kafka_consumer_manually_commit import KafkaConsumerManuallyCommit
        from funboost.publishers.confluent_kafka_publisher import ConfluentKafkaPublisher
        register_custom_broker(BrokerEnum.KAFKA_CONFLUENT, ConfluentKafkaPublisher, KafkaConsumerManuallyCommit)

    if broker_kind == BrokerEnum.KAFKA_CONFLUENT_SASlPlAIN:
        from funboost.consumers.kafka_consumer_manually_commit import SaslPlainKafkaConsumer
        from funboost.publishers.confluent_kafka_publisher import SaslPlainKafkaPublisher
        register_custom_broker(broker_kind, SaslPlainKafkaPublisher, SaslPlainKafkaConsumer)

    if broker_kind == BrokerEnum.RQ:
        from funboost.consumers.rq_consumer import RqConsumer
        from funboost.publishers.rq_publisher import RqPublisher
        register_custom_broker(broker_kind, RqPublisher, RqConsumer)

    if broker_kind == BrokerEnum.KOMBU:
        from funboost.consumers.kombu_consumer import KombuConsumer
        from funboost.publishers.kombu_publisher import KombuPublisher
        register_custom_broker(broker_kind, KombuPublisher, KombuConsumer)

    if broker_kind == BrokerEnum.NSQ:
        from funboost.publishers.nsq_publisher import NsqPublisher
        from funboost.consumers.nsq_consumer import NsqConsumer
        register_custom_broker(broker_kind, NsqPublisher, NsqConsumer)

    if broker_kind == BrokerEnum.GRPC:
        from funboost.consumers.grpc_consumer import GrpcConsumer
        from funboost.publishers.grpc_publisher import GrpcPublisher
        register_custom_broker(broker_kind, GrpcPublisher, GrpcConsumer)

    if broker_kind == BrokerEnum.MYSQL_CDC:
        from funboost.consumers.mysql_cdc_consumer import MysqlCdcConsumer
        from funboost.publishers.mysql_cdc_publisher import MysqlCdcPublisher
        register_custom_broker(broker_kind, MysqlCdcPublisher, MysqlCdcConsumer)
    
    if broker_kind == BrokerEnum.HTTP:
        from funboost.consumers.http_consumer import HTTPConsumer
        from funboost.publishers.http_publisher import HTTPPublisher
        register_custom_broker(broker_kind, HTTPPublisher, HTTPConsumer)

    if broker_kind == BrokerEnum.SQS:
        from funboost.consumers.sqs_consumer import SqsConsumer
        from funboost.publishers.sqs_publisher import SqsPublisher
        register_custom_broker(broker_kind, SqsPublisher, SqsConsumer)

    if broker_kind == BrokerEnum.RABBITMQ_AMQP:
        from funboost.publishers.rabbitmq_amqp_publisher import RabbitmqAmqpPublisher
        from funboost.consumers.rabbitmq_amqp_consumer import RabbitmqAmqpConsumer
        register_custom_broker(BrokerEnum.RABBITMQ_AMQP, RabbitmqAmqpPublisher, RabbitmqAmqpConsumer)

    if broker_kind == BrokerEnum.POSTGRES:
        from funboost.publishers.postgres_publisher import PostgresPublisher
        from funboost.consumers.postgres_consumer import PostgresConsumer
        register_custom_broker(BrokerEnum.POSTGRES, PostgresPublisher, PostgresConsumer)
        
    if broker_kind == BrokerEnum.ROCKETMQ:
        from funboost.publishers.rocketmq_publisher import RocketmqPublisher
        from funboost.consumers.rocketmq_consumer import RocketmqConsumer
        register_custom_broker(BrokerEnum.ROCKETMQ, RocketmqPublisher, RocketmqConsumer)
    if broker_kind == BrokerEnum.ROCKETMQ5:
        from funboost.publishers.rocketmq5_publisher import Rocketmq5Publisher
        from funboost.consumers.rocketmq5_consumer import Rocketmq5Consumer
        register_custom_broker(BrokerEnum.ROCKETMQ5, Rocketmq5Publisher, Rocketmq5Consumer)
        
    if broker_kind == BrokerEnum.WATCHDOG:
        from funboost.contrib.register_custom_broker_contrib  import watchdog_broker
        # No need to call register_custom_broker, it is already registered in watchdog_broker.py
        
    if broker_kind == BrokerEnum.WEBSOCKET:
        from funboost.contrib.register_custom_broker_contrib import websocket_broker
        # No need to call register_custom_broker, it is already registered in websocket_broker.py
        
        

if __name__ == '__main__':
    import sys

    print(sys.modules)
    