# -*- coding: utf-8 -*-
import logging
from pathlib import Path
from funboost.utils.simple_data_class import DataClassBase
from nb_log import nb_log_config_default
from urllib.parse import quote_plus

'''
The funboost_config.py file is automatically generated in your project root directory on the first run of the framework. Users do not need to create it manually.
You can write any Python code in this file. For example, broker credentials/passwords can be fetched from a configuration center like Apollo or from environment variables.
'''

'''
Configurations modified in the funboost_config.py file auto-generated in your project root directory will be automatically read.
Users should not modify the framework source code in funboost/funboost_config_deafult.py; the variables in this module will be automatically overridden by funboost_config.py.
The configuration override logic in funboost/funboost_config_deafult.py can be seen in the code of funboost/set_frame_config.py.

The framework documentation is at https://funboost.readthedocs.io/zh_CN/latest/
'''


class BrokerConnConfig(DataClassBase):
    """
    Broker connection configuration.
    Modify this file as needed. For example, if you use Redis as the message queue middleware, you don't need to worry about the RabbitMQ, MongoDB, or Kafka configurations.
    However, there are 3 exceptions: if you need to use RPC mode, distributed frequency control, or task filtering, you must configure the Redis connection regardless of which message queue middleware you use.
    If the @boost decorator sets is_using_rpc_mode=True, is_using_distributed_frequency_control=True, or do_task_filtering=True, you need to configure the Redis connection. The default is False, so users are not forced to install Redis.
    """

    MONGO_CONNECT_URL = f'mongodb://127.0.0.1:27017'  # If connecting with a password: 'mongodb://myUserAdmin:XXXXX@192.168.199.202:27016/'   authSource specifies the authentication db, e.g. MONGO_CONNECT_URL = 'mongodb://root:123456@192.168.64.151:27017?authSource=admin'

    RABBITMQ_USER = 'rabbitmq_user'
    RABBITMQ_PASS = 'rabbitmq_pass'
    RABBITMQ_HOST = '127.0.0.1'
    RABBITMQ_PORT = 5672
    RABBITMQ_VIRTUAL_HOST = '/'  # my_host # This is the RabbitMQ virtual sub-host created by the user. If you want to use the RabbitMQ root host directly instead of a virtual sub-host, set this to an empty string.
    RABBITMQ_URL = f'amqp://{RABBITMQ_USER}:{quote_plus(RABBITMQ_PASS)}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VIRTUAL_HOST}'

    REDIS_HOST = '127.0.0.1'
    REDIS_USERNAME = ''
    REDIS_PASSWORD = ''
    REDIS_PORT = 6379
    REDIS_DB = 7  # The Redis DB used for the message queue. Please do not put too many other key-value pairs in this DB, and use a dedicated DB for easy visual inspection of your Redis DB.
    REDIS_DB_FILTER_AND_RPC_RESULT = 8  # If the function performs task parameter filtering or uses RPC to get results, use this DB, because it has many key-value pairs and should be kept separate from the Redis message queue DB.
    REDIS_SSL = False  # Whether to use SSL encryption, default is False
    REDIS_URL = f'{"rediss" if REDIS_SSL else "redis"}://{REDIS_USERNAME}:{quote_plus(REDIS_PASSWORD)}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

    NSQD_TCP_ADDRESSES = ['127.0.0.1:4150']
    NSQD_HTTP_CLIENT_HOST = '127.0.0.1'
    NSQD_HTTP_CLIENT_PORT = 4151

    KAFKA_BOOTSTRAP_SERVERS = ['127.0.0.1:9092']
    KFFKA_SASL_CONFIG = {
        "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
        "sasl_plain_username": "",
        "sasl_plain_password": "",
        "sasl_mechanism": "SCRAM-SHA-256",
        "security_protocol": "SASL_PLAINTEXT",
    }

    SQLACHEMY_ENGINE_URL = 'sqlite:////sqlachemy_queues/queues.db'

    # If broker_kind uses the peewee middleware mode, the MySQL configuration will be used
    MYSQL_HOST = '127.0.0.1'
    MYSQL_PORT = 3306
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '123456'
    MYSQL_DATABASE = 'testdb6'

    # When using the persist_queue middleware with local SQLite, this is the location where the database file is generated. If the Linux account does not have permission to create folders in the root directory, change to a different folder.
    SQLLITE_QUEUES_PATH = '/sqllite_queues'

    TXT_FILE_PATH = Path(__file__).parent / 'txt_queues'  # It is not recommended to use this txt-simulated message queue middleware; prefer the PERSIST_QUEUE middleware for local persistence.

    # RocketMQ 4.x legacy configuration (deprecated, kept for backward compatibility only)
    ROCKETMQ_NAMESRV_ADDR = '192.168.199.202:9876'

    # RocketMQ 5.x new configuration (recommended)
    # Uses the gRPC protocol, default port 8081
    ROCKETMQ_ENDPOINTS = '127.0.0.1:8081'
    ROCKETMQ_ACCESS_KEY = ''  # Used when AK/SK authentication is required, e.g. for Alibaba Cloud
    ROCKETMQ_SECRET_KEY = ''

    MQTT_HOST = '127.0.0.1'
    MQTT_TCP_PORT = 1883

    HTTPSQS_HOST = '127.0.0.1'
    HTTPSQS_PORT = 1218
    HTTPSQS_AUTH = '123456'

    NATS_URL = 'nats://192.168.6.134:4222'

    KOMBU_URL = 'redis://127.0.0.1:6379/9'  # This is the message queue format used by Celery's dependency package kombu, so funboost supports all message queue types that Celery supports.
    # KOMBU_URL =  'sqla+sqlite:////dssf_kombu_sqlite.sqlite'  # Four slashes //// means generating a file at the disk root. Absolute paths are recommended. Three slashes /// is a relative path.

    CELERY_BROKER_URL = 'redis://127.0.0.1:6379/12'  # Use Celery as the middleware. funboost added support for the Celery framework to run functions; the URL content follows the Celery broker format.
    CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/13'  # Celery result storage, can be None

    DRAMATIQ_URL = RABBITMQ_URL

    PULSAR_URL = 'pulsar://192.168.70.128:6650'

    # AWS SQS configuration
    SQS_REGION_NAME = 'us-east-1'  # AWS region, e.g. 'us-east-1', 'ap-northeast-1', 'cn-north-1'
    SQS_AWS_ACCESS_KEY_ID = ''  # AWS Access Key ID; leave empty to use the default AWS credentials chain (environment variables, ~/.aws/credentials, etc.)
    SQS_AWS_SECRET_ACCESS_KEY = ''  # AWS Secret Access Key
    SQS_ENDPOINT_URL = ''  # Optional, for LocalStack local testing or S3-API-compatible services, e.g. 'http://localhost:4566'

    # PostgreSQL native queue configuration (using FOR UPDATE SKIP LOCKED + LISTEN/NOTIFY)
    POSTGRES_DSN = 'host=127.0.0.1 port=5432 dbname=funboost user=postgres password=123456'



class FunboostCommonConfig(DataClassBase):
    # Which log template index from the nb_log package to use. There are 7 built-in templates; you can extend them in the nb_log_config.py file in your project root directory.
    # NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER = 11  # 7 is a short non-clickable format, 5 is a clickable format, 11 is a template showing IP, process, and thread. You can also set your own log template instead of passing a number.
    NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER = logging.Formatter(
        f'%(asctime)s-({nb_log_config_default.computer_ip},{nb_log_config_default.computer_name})-[p%(process)d_t%(thread)d] - %(name)s - "%(filename)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(task_id)s - %(message)s',
        "%Y-%m-%d %H:%M:%S",)   # This is a log template that includes task_id, allowing logs to display the task_id so users can trace all logs for a specific task message.

    TIMEZONE = 'Asia/Shanghai'  # Timezone

    # The following configurations modify some namespaces of funboost and the log level at startup. Beginners should avoid suppressing logs until familiar with the framework.
    SHOW_HOW_FUNBOOST_CONFIG_SETTINGS = True  # Set this to suppress the message "The distributed function scheduling framework will automatically import the funboost_config module. When the script is run for the first time, the framework will create a file named funboost_config.py in the root directory of your Python project ...".
    FUNBOOST_PROMPT_LOG_LEVEL = logging.DEBUG  # Startup prompt messages for funboost. Users can adjust the log level for this namespace.
    KEEPALIVETIMETHREAD_LOG_LEVEL = logging.DEBUG  # The auto-shrinking adaptive thread pool invented by the funboost author. Users who are not interested in thread creation and destruction in the variable thread pool can raise the log level.
