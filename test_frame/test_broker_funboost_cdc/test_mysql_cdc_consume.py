# coding=utf-8
from typing import Dict, Any
import dataset

from funboost import boost, BrokerEnum, ConcurrentModeEnum, BoosterParams, BoostersManager, PublisherParams
from pymysqlreplication.row_event import (DeleteRowsEvent, UpdateRowsEvent, WriteRowsEvent, )

from funboost.contrib.cdc.mysql2mysql import MySql2Mysql  # Import MySql2Mysql class from funboost's contrib folder.

bin_log_stream_reader_config = dict(
    # All parameters of BinLogStreamReaderConfig are native parameters of pymysqlreplication.BinLogStreamReader
    connection_settings={"host": "127.0.0.1", "port": 3306, "user": "root", "passwd": "123456"},
    server_id=104,
    only_events=[DeleteRowsEvent, UpdateRowsEvent, WriteRowsEvent, ],
    blocking=True,  # 1. Set to blocking mode to keep waiting for new events
    resume_stream=True,  # 2. (Recommended) Allow automatic resumption from last position after disconnection
    only_schemas=['testdb6'],  # 3. Only listen to the testdb6 database
    only_tables=['users'],  # 4. Only listen to the users table
)

sink_db = dataset.connect('mysql+pymysql://root:123456@127.0.0.1:3306/testdb7')  # Use CDC to sync testdb6.users table data to the users table in another database testdb7


@boost(BoosterParams(
    queue_name='test_queue_no_use_for_mysql_cdc',
    broker_exclusive_config={'BinLogStreamReaderConfig': bin_log_stream_reader_config},
    broker_kind=BrokerEnum.MYSQL_CDC, ))
def consume_binlog(event_type: str,
                   schema: str,
                   table: str,
                   timestamp: int,
                   **row_data: Any):
    full_cdc_msg = locals()
    print(full_cdc_msg)
    # UPDATE event output looks like this:
    """
    {
    "event_type": "UPDATE",
    "row_data": {
        "after_none_sources": {},
        "after_values": {
            "email": "wangshier@example.com",
            "id": 10,
            "name": "wangbadan2b16"
        },
        "before_none_sources": {},
        "before_values": {
            "email": "wangshier@example.com",
            "id": 10,
            "name": "wangbadan2b15"
        }
    },
    "schema": "testdb6",
    "table": "users",
    "timestamp": 1756207785
}
    """
    # Demonstrates effortless mysql2mysql table synchronization; you can also clean data before inserting into MySQL.
    # This example syncs the entire table as-is, without needing to set up a Flink CDC big data cluster — achievable in under 5 lines of code.
    m2m = MySql2Mysql(primary_key='id', target_table_name='users', target_sink_db=sink_db, )
    m2m.sync_data(event_type, schema, table, timestamp, row_data)  # Just one line of code to sync CDC data to a table in another database instance.

    # You can also send messages to rabbitmq, kafka, redis — your choice. Use funboost's publisher.send_msg to publish raw content without adding extra keys like taskid.
    # No need to wrap various message publishing tools yourself; use funboost's universal feature to publish to any message queue in one line of code.

    # Demonstrate sending messages to redis
    pb_redis = BoostersManager.get_cross_project_publisher(PublisherParams(queue_name='test_queue_mysql_cdc_dest1', broker_kind=BrokerEnum.REDIS))
    pb_redis.send_msg(full_cdc_msg)

    # Demonstrate sending messages to kafka
    pb_kafka = BoostersManager.get_cross_project_publisher(PublisherParams(queue_name='test_queue_mysql_cdc_dest2', broker_kind=BrokerEnum.KAFKA,
                                                                           broker_exclusive_config={'num_partitions': 10, 'replication_factor': 1}))
    pb_kafka.send_msg(full_cdc_msg)


if __name__ == '__main__':
    # When MYSQL_CDC is used as funboost's broker, manual push is disabled. It automatically listens to binlog as the message source, so no manual message publishing is needed.
    # Any insert, delete, or update on the database will trigger binlog, which indirectly serves as the message source for the funboost consumer.
    consume_binlog.consume()
