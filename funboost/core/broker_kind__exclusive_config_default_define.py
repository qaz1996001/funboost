
"""
This file defines what unique/special broker configurations can be additionally passed for each broker type,
via a dictionary in the broker_exclusive_config parameter of BoosterParams.
"""

from logging import Logger
from funboost.constant import BrokerEnum


broker_kind__exclusive_config_default_map: dict = {}


def register_broker_exclusive_config_default(
    broker_kind: str, broker_exclusive_config_default: dict
):
    broker_kind__exclusive_config_default_map[broker_kind] = broker_exclusive_config_default



def generate_broker_exclusive_config(
    broker_kind: str,
    user_broker_exclusive_config: dict,
    logger: Logger,
):
    broker_exclusive_config_default = broker_kind__exclusive_config_default_map.get(
        broker_kind, {}
    )
    broker_exclusive_config_keys = broker_exclusive_config_default.keys()
    if user_broker_exclusive_config:
        if set(user_broker_exclusive_config).issubset(broker_exclusive_config_keys):
            logger.info(
                f"Current message queue broker supports special exclusive configurations: {broker_exclusive_config_default.keys()}"
            )
        else:
            logger.warning(f"""Current message queue broker contains unsupported special configurations {user_broker_exclusive_config.keys()},
            supported special exclusive configurations include {broker_exclusive_config_keys}""")
    broker_exclusive_config_merge = dict()
    broker_exclusive_config_merge.update(broker_exclusive_config_default)
    broker_exclusive_config_merge.update(user_broker_exclusive_config)
    return broker_exclusive_config_merge


# Full list of celery configuration options: https://docs.celeryq.dev/en/stable/userguide/configuration.html#new-lowercase-settings
# All @app.task() configuration options can be found in: D:\ProgramData\Miniconda3\Lib\site-packages\celery\app\task.py
register_broker_exclusive_config_default(BrokerEnum.CELERY, {"celery_task_config": {}})


# dramatiq_actor_options possible values:
# {'max_age', 'throws', 'pipe_target', 'pipe_ignore', 'on_success', 'retry_when', 'time_limit', 'min_backoff', 'max_retries', 'max_backoff', 'notify_shutdown', 'on_failure'}
register_broker_exclusive_config_default(
    BrokerEnum.DRAMATIQ, {"dramatiq_actor_options": {}}
)


register_broker_exclusive_config_default(
    BrokerEnum.GRPC,
    {
        "host": "127.0.0.1",
        "port": None,
    },
)

register_broker_exclusive_config_default(
    BrokerEnum.HTTP,
    {
        "host": "127.0.0.1",
        "port": None,
    },
)


"""
retries=0, retry_delay=0, priority=None, context=False,
name=None, expires=None, **kwargs
"""
register_broker_exclusive_config_default(BrokerEnum.HUEY, {"huey_task_kwargs": {}})


"""
auto_offset_reset description

auto_offset_reset (str): A policy for resetting offsets on
OffsetOutOfRange errors: 'earliest' will move to the oldest
available message, 'latest' will move to the most recent. Any
other value will raise the exception. Default: 'latest'.
"""
register_broker_exclusive_config_default(
    BrokerEnum.KAFKA,
    {
        "group_id": "funboost_kafka",
        "auto_offset_reset": "earliest",
        "num_partitions": 10,
        "replication_factor": 1,
    },
)


register_broker_exclusive_config_default(
    BrokerEnum.KAFKA_CONFLUENT,
    {
        "group_id": "funboost_kafka",
        "auto_offset_reset": "earliest",
        "num_partitions": 10,
        "replication_factor": 1,
    },
)


"""
# prefetch_count is the number of messages to prefetch
transport_options is kombu's transport_options.
For example, when using kombu with redis as the broker, you can set visibility_timeout to determine how long after a message is taken out without being acked it will automatically return to the queue.
For what transport_options each broker supports, see the transport_options parameter documentation in kombu's source code.
"""
register_broker_exclusive_config_default(
    BrokerEnum.KOMBU,
    {
        "kombu_url": None,  # If kombu_url is also configured here, it takes priority; otherwise funboost_config.KOMBU_URL is used
        "transport_options": {},  # transport_options is kombu's transport_options.
        "prefetch_count": 500,
    },
)


register_broker_exclusive_config_default(
    BrokerEnum.MYSQL_CDC, {"BinLogStreamReaderConfig": {}}
)  # Parameters are the same as BinLogStreamReader's parameters


"""
consumer_type Members:
Exclusive  Shared Failover KeyShared
"""
register_broker_exclusive_config_default(
    BrokerEnum.PULSAR,
    {
        "subscription_name": "funboost_group",
        "replicate_subscription_state_enabled": True,
        "consumer_type": "Shared",
    },
)


register_broker_exclusive_config_default(
    BrokerEnum.RABBITMQ_AMQPSTORM,
    {
        "queue_durable": True,
        "x-max-priority": None,  # x-max-priority is the RabbitMQ priority queue config, must be an integer, strongly recommended to be less than 5. None means the queue does not support priority.
        "no_ack": False,
    },
)


# RABBITMQ_AMQP uses the amqp package, configuration is the same as RABBITMQ_AMQPSTORM
register_broker_exclusive_config_default(
    BrokerEnum.RABBITMQ_AMQP,
    {
        "queue_durable": True,
        "x-max-priority": None,  # x-max-priority is the RabbitMQ priority queue config, must be an integer, strongly recommended to be less than 5. None means the queue does not support priority.
        "no_ack": False,
    },
)


register_broker_exclusive_config_default(
    BrokerEnum.RABBITMQ_COMPLEX_ROUTING,
    {
        "queue_durable": True,
        "x-max-priority": None,  # x-max-priority is the RabbitMQ priority queue config, must be an integer, strongly recommended to be less than 5. None means the queue does not support priority.
        "no_ack": False,
        "exchange_name": "",
        "exchange_type": "direct",
        "routing_key_for_bind": None,  # Key used when binding exchange and queue. None means using queue_name as the binding key; "" (empty string) also means using queue_name. For fanout and headers exchanges, this value is ignored. For topic exchanges, wildcards * and # can be used.
        "routing_key_for_publish": None,
        # for headers exchange
        "headers_for_bind": {},
        "x_match_for_bind": "all",  # all or any
        "exchange_declare_durable": True,
    },
)


register_broker_exclusive_config_default(
    BrokerEnum.REDIS,
    {
        "redis_bulk_push": 1,
        "pull_msg_batch_size": 100,
    },
)  # redis_bulk_push whether to use redis bulk push


register_broker_exclusive_config_default(
    BrokerEnum.REDIS_ACK_ABLE, {
    "pull_msg_batch_size": 100,  # redis_ack_able broker can set the number of messages to pull in batch

    "pull_base_interval": 0.01, # If there were no messages last time, the initial interval for the next pull, doubles each time (exponential backoff)
    "pull_max_interval": 2, # If there were no messages last time, the maximum interval for the next pull, prevents exponential backoff from growing indefinitely. Less pressure on redis than a fixed 0.1s sleep.
    }
)

# RedisConsumerAckUsingTimeout's ack timeout means how many seconds after a message is taken out without being acked it will automatically return to the queue. This must be greater than the function execution time, otherwise messages will keep returning to the queue.
"""
Usage: how to set ack_timeout, pass it in broker_exclusive_config to override the default 3600, no need to modify BROKER_EXCLUSIVE_CONFIG_DEFAULT source code.
@boost(BoosterParams(queue_name='test_redis_ack__use_timeout', broker_kind=BrokerEnum.REIDS_ACK_USING_TIMEOUT,
                        concurrent_num=5, log_level=20, broker_exclusive_config={'ack_timeout': 30}))
"""
register_broker_exclusive_config_default(
    BrokerEnum.REIDS_ACK_USING_TIMEOUT, {"ack_timeout": 3600}
)


register_broker_exclusive_config_default(
    BrokerEnum.REDIS_PRIORITY, {"x-max-priority": None}
)  # x-max-priority is the RabbitMQ priority queue config, must be an integer, strongly recommended to be less than 5. None means the queue does not support priority.


register_broker_exclusive_config_default(
    BrokerEnum.REDIS_STREAM,
    {
        "group": "funboost_group",
        "pull_msg_batch_size": 100,
    },
)


register_broker_exclusive_config_default(
    BrokerEnum.TCP,
    {
        "host": "127.0.0.1",
        "port": None,
        "bufsize": 10240,
    },
)


register_broker_exclusive_config_default(
    BrokerEnum.UDP,
    {
        "host": "127.0.0.1",
        "port": None,
        "bufsize": 10240,
    },
)

register_broker_exclusive_config_default(BrokerEnum.ZEROMQ, {"port": None})


# High-performance memory queue exclusive configuration
# pull_msg_batch_size: number of messages to pull in batch, default 1 (single pull)
# ultra_fast_mode: ultra-fast mode, skips most framework overhead, 3-10x performance improvement
#   Note: ultra-fast mode does not support retry, filtering, delayed tasks, RPC, result persistence, etc.
register_broker_exclusive_config_default(
    BrokerEnum.FASTEST_MEM_QUEUE,
    {
        "pull_msg_batch_size": 1,  # Default single pull, recommended 100-5000 for batch mode
        "ultra_fast_mode": False,  # Ultra-fast mode, skips framework overhead
    },
)


# AWS SQS exclusive configuration
# wait_time_seconds: long polling wait time (seconds), max 20 seconds, 0 for short polling
# max_number_of_messages: max messages per receive_message call, range 1-10
# visibility_timeout: message visibility timeout (seconds), messages are invisible to other consumers during this time
# message_retention_period: message retention period (seconds), default 14 days (1209600 seconds), range 60-1209600
# content_based_deduplication: whether to enable content-based deduplication for FIFO queues, default True
register_broker_exclusive_config_default(
    BrokerEnum.SQS,
    {
        "wait_time_seconds": 20,  # Long polling wait time, max 20 seconds
        "max_number_of_messages": 10,  # Max messages per pull, max 10
        "visibility_timeout": 300,  # Visibility timeout, default 5 minutes
        "message_retention_period": 1209600,  # Message retention period, default 14 days
        "content_based_deduplication": True,  # Whether to enable content-based deduplication for FIFO queues
    },
)


# PostgreSQL native queue exclusive configuration
# Fully utilizes PostgreSQL's FOR UPDATE SKIP LOCKED and LISTEN/NOTIFY features
register_broker_exclusive_config_default(
    BrokerEnum.POSTGRES,
    {
        "use_listen_notify": True,  # Whether to use LISTEN/NOTIFY for real-time push, more efficient than polling
        "poll_interval": 30,  # Polling/notification wait timeout (seconds)
        "timeout_minutes": 10,  # Tasks not acknowledged within this time automatically return to queue (minutes)
        "min_connections": 2,  # Connection pool minimum connections
        "max_connections": 20,  # Connection pool maximum connections
        "priority": 0,  # Default task priority
    },
)


# Memory queue (MEMORY_QUEUE/LOCAL_PYTHON_QUEUE) exclusive configuration
# maxsize: maximum queue capacity, 0 means unbounded queue (default), positive integer means bounded queue
#   When the queue is full, put operations will block until there is space
register_broker_exclusive_config_default(
    BrokerEnum.MEMORY_QUEUE,
    {
        "maxsize": 0,  # Maximum queue capacity, 0 means unbounded queue
    },
)


# RocketMQ 5.x exclusive configuration
# Uses rocketmq-python-client package (pip install rocketmq-python-client)
# Based on gRPC protocol, pure Python implementation, supports Windows/Linux/macOS
# SimpleConsumer mode: supports out-of-order single message ACK, does not depend on offset
register_broker_exclusive_config_default(
    BrokerEnum.ROCKETMQ5,
    {
        "endpoints": "127.0.0.1:8081",  # RocketMQ 5.x gRPC Proxy endpoint address
        "consumer_group": "funboost_consumer_group",  # Consumer group name
        "access_key": None,  # Access key (optional, required for Alibaba Cloud etc.)
        "secret_key": None,  # Secret key (optional)
        "namespace": None,  # Namespace (optional)
        "invisible_duration": 15,  # Message invisible duration (seconds), messages are invisible to other consumers during this time
        "max_message_num": 32,  # Max messages per pull
        "tag": "*",  # Message filter tag, '*' means no filtering
        "namesrv_addr": None,  # NameServer address, used for auto-creating Topics, defaults to inferring from endpoints
        "cluster_name": "DefaultCluster",  # Cluster name, used for auto-creating Topics
    },
)