# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/4
"""
The most important purpose of this file is to demonstrate how to use register_custom_broker
to extend a brand new broker middleware.

DuckDB Message Queue Middleware Implementation

DuckDB features:
1. Embedded database, no need to deploy additional services, works out of the box
2. Columnar storage, high-performance OLAP queries
3. Supports standard SQL, easy to use
4. Very suitable for single-machine scenarios, excellent performance
5. Flexible choice between file storage or in-memory mode

Use cases:
- Single-machine development and testing
- Lightweight task queues
- Scenarios where you don't want to deploy external services like Redis/RabbitMQ
- Scenarios that need persistence but don't want a heavyweight database

Usage:
    from funboost.contrib.register_custom_broker_contrib.duckdb_broker import BROKER_KIND_DUCKDB

    @boost(BoosterParams(queue_name='my_queue', broker_kind=BROKER_KIND_DUCKDB))
    def my_func(x):
        print(x)
"""

import json
import threading
import time
from pathlib import Path
from typing import Optional

try:
    import duckdb
except ImportError:
    raise ImportError("Please install duckdb: pip install duckdb")

from funboost import register_custom_broker, AbstractConsumer, AbstractPublisher
from funboost.core.loggers import FunboostFileLoggerMixin, LoggerLevelSetterMixin
from funboost.utils import decorators


class TaskStatus:
    """Task status constants"""
    TO_BE_CONSUMED = 'to_be_consumed'  # Pending consumption
    PENDING = 'pending'                 # Being consumed
    SUCCESS = 'success'                 # Consumed successfully
    REQUEUE = 'requeue'                 # Re-queued


# Global lock to ensure concurrent safety for DuckDB single-file access
_duckdb_locks = {}
_lock_for_locks = threading.Lock()


def _get_lock(db_path: str) -> threading.Lock:
    """Get the lock for the specified database file"""
    with _lock_for_locks:
        if db_path not in _duckdb_locks:
            _duckdb_locks[db_path] = threading.Lock()
        return _duckdb_locks[db_path]


@decorators.flyweight
class DuckDBQueue(FunboostFileLoggerMixin, LoggerLevelSetterMixin):
    """
    DuckDB queue implementation

    Features:
    1. Uses file storage, messages are persistent
    2. Supports in-memory mode for higher performance
    3. Thread-safe, uses locks to protect concurrent operations
    4. Supports priority queues
    5. Supports message acknowledgment and re-queuing
    """

    def __init__(self, queue_name: str, db_path: str = ':memory:',
                 wal_autocheckpoint: int = 1000):
        """
        :param queue_name: Queue name
        :param db_path: Database file path, ':memory:' for in-memory mode
        :param wal_autocheckpoint: WAL auto-checkpoint threshold (deprecated, DuckDB does not use this parameter)
        """
        self.queue_name = queue_name
        self._db_path = db_path
        self._table_name = f"funboost_queue_{queue_name.replace('-', '_').replace('.', '_')}"
        self._lock = _get_lock(db_path)

        # Create connection
        self._conn = duckdb.connect(db_path)

        # Create table
        self._create_table()
        self.logger.info(f"DuckDB queue [{queue_name}] initialized, database: {db_path}")

    def _create_table(self):
        """Create queue table"""
        with self._lock:
            self._conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    job_id BIGINT PRIMARY KEY,
                    body VARCHAR NOT NULL,
                    status VARCHAR DEFAULT 'to_be_consumed',
                    priority INTEGER DEFAULT 0,
                    publish_time TIMESTAMP DEFAULT current_timestamp,
                    consume_start_time TIMESTAMP
                )
            """)
            # Create sequence (if not exists)
            try:
                self._conn.execute(f"CREATE SEQUENCE IF NOT EXISTS seq_{self._table_name}")
            except Exception:
                pass  # DuckDB may not support IF NOT EXISTS for SEQUENCE

            # Create index
            try:
                self._conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self._table_name}_status
                    ON {self._table_name} (status, priority DESC, publish_time ASC)
                """)
            except Exception:
                pass  # Index may already exist

    def _next_job_id(self) -> int:
        """Generate next job_id"""
        try:
            result = self._conn.execute(f"SELECT nextval('seq_{self._table_name}')").fetchone()
            return result[0]
        except Exception:
            # If sequence does not exist, use timestamp + random number
            import random
            return int(time.time() * 1000000) + random.randint(0, 999999)

    def push(self, body: str, priority: int = 0) -> int:
        """
        Publish message to queue
        :param body: Message body (JSON string)
        :param priority: Priority (higher value = higher priority)
        :return: job_id
        """
        with self._lock:
            job_id = self._next_job_id()
            self._conn.execute(f"""
                INSERT INTO {self._table_name} (job_id, body, status, priority, publish_time)
                VALUES (?, ?, ?, ?, current_timestamp)
            """, [job_id, body, TaskStatus.TO_BE_CONSUMED, priority])
            return job_id

    def bulk_push(self, items: list) -> list:
        """
        Bulk publish messages
        :param items: [{'body': str, 'priority': int}, ...] or [str, ...]
        :return: list of job_ids
        """
        job_ids = []
        with self._lock:
            for item in items:
                if isinstance(item, dict):
                    body = item.get('body', item)
                    priority = item.get('priority', 0)
                else:
                    body = item
                    priority = 0

                job_id = self._next_job_id()
                self._conn.execute(f"""
                    INSERT INTO {self._table_name} (job_id, body, status, priority, publish_time)
                    VALUES (?, ?, ?, ?, current_timestamp)
                """, [job_id, body, TaskStatus.TO_BE_CONSUMED, priority])
                job_ids.append(job_id)
        return job_ids

    def get(self, timeout: float = None) -> Optional[dict]:
        """
        Get one pending message
        :param timeout: Timeout in seconds, None means wait indefinitely
        :return: {'job_id': int, 'body': str, 'priority': int} or None
        """
        start_time = time.time()
        while True:
            with self._lock:
                # Find pending messages (sorted by priority descending, publish time ascending)
                result = self._conn.execute(f"""
                    SELECT job_id, body, priority, publish_time
                    FROM {self._table_name}
                    WHERE status IN ('{TaskStatus.TO_BE_CONSUMED}', '{TaskStatus.REQUEUE}')
                    ORDER BY priority DESC, publish_time ASC
                    LIMIT 1
                """).fetchone()

                if result:
                    job_id, body, priority, publish_time = result
                    # Update status to processing
                    self._conn.execute(f"""
                        UPDATE {self._table_name}
                        SET status = ?, consume_start_time = current_timestamp
                        WHERE job_id = ?
                    """, [TaskStatus.PENDING, job_id])
                    return {
                        'job_id': job_id,
                        'body': body,
                        'priority': priority,
                        'publish_time': publish_time,
                    }

            # No messages, check timeout
            if timeout is not None and (time.time() - start_time) >= timeout:
                return None

            # Wait briefly before retrying
            time.sleep(0.05)

    def ack(self, job_id: int, delete: bool = True):
        """
        Acknowledge successful consumption
        :param job_id: Task ID
        :param delete: Whether to delete the message (True = delete, False = update status to success)
        """
        with self._lock:
            if delete:
                self._conn.execute(f"DELETE FROM {self._table_name} WHERE job_id = ?", [job_id])
            else:
                self._conn.execute(f"""
                    UPDATE {self._table_name} SET status = ? WHERE job_id = ?
                """, [TaskStatus.SUCCESS, job_id])

    def requeue(self, job_id: int):
        """Re-queue a message"""
        with self._lock:
            self._conn.execute(f"""
                UPDATE {self._table_name}
                SET status = ?, consume_start_time = NULL
                WHERE job_id = ?
            """, [TaskStatus.REQUEUE, job_id])

    def clear(self):
        """Clear the queue"""
        with self._lock:
            self._conn.execute(f"DELETE FROM {self._table_name}")

    def get_message_count(self) -> int:
        """Get the number of pending messages"""
        with self._lock:
            result = self._conn.execute(f"""
                SELECT COUNT(*) FROM {self._table_name}
                WHERE status IN ('{TaskStatus.TO_BE_CONSUMED}', '{TaskStatus.REQUEUE}')
            """).fetchone()
            return result[0] if result else 0

    def recover_timeout_tasks(self, timeout_minutes: int = 10) -> int:
        """
        Recover tasks that timed out without acknowledgment
        :param timeout_minutes: Timeout threshold (minutes)
        :return: Number of recovered tasks
        """
        with self._lock:
            # DuckDB time calculation syntax
            self._conn.execute(f"""
                UPDATE {self._table_name}
                SET status = ?, consume_start_time = NULL
                WHERE status = ?
                AND consume_start_time < current_timestamp - INTERVAL '{timeout_minutes} minutes'
            """, [TaskStatus.TO_BE_CONSUMED, TaskStatus.PENDING])

            # Since DuckDB doesn't directly return updated row count, query it here
            result = self._conn.execute(f"""
                SELECT COUNT(*) FROM {self._table_name}
                WHERE status = '{TaskStatus.TO_BE_CONSUMED}'
            """).fetchone()
            return result[0] if result else 0

    def close(self):
        """Close connection"""
        if self._conn:
            self._conn.close()
            self._conn = None


# ============================================================================
# Publisher and Consumer implementations
# ============================================================================

class DuckDBPublisher(AbstractPublisher):
    """DuckDB message publisher"""

    def custom_init(self):
        # Get configuration from broker_exclusive_config
        db_path = self.publisher_params.broker_exclusive_config['db_path']
        priority = self.publisher_params.broker_exclusive_config['priority']

        self._priority = priority
        self._queue = DuckDBQueue(
            queue_name=self._queue_name,
            db_path=db_path,
        )
        self.logger.info(f"DuckDB Publisher initialized, queue: {self._queue_name}, database: {db_path}")

    def _publish_impl(self, msg: str):
        """Publish message"""
        priority = self._priority
        # Try to get priority from message
        try:
            msg_dict = json.loads(msg)
            if 'extra' in msg_dict:
                extra = msg_dict.get('extra', {})
                if isinstance(extra, dict):
                    other_extra = extra.get('other_extra_params', {})
                    if isinstance(other_extra, dict) and 'priority' in other_extra:
                        priority = other_extra['priority']
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        self._queue.push(msg, priority=priority)

    def clear(self):
        """Clear the queue"""
        self._queue.clear()

    def get_message_count(self):
        """Get the number of pending messages"""
        return self._queue.get_message_count()

    def close(self):
        """Close connection"""
        self._queue.close()


class DuckDBConsumer(AbstractConsumer):
    """DuckDB message consumer"""

    BROKER_KIND = None  # Will be automatically set by the framework

    def custom_init(self):
        # Get configuration from broker_exclusive_config
        db_path = self.consumer_params.broker_exclusive_config['db_path']
        self._poll_interval = self.consumer_params.broker_exclusive_config['poll_interval']
        self._timeout_minutes = self.consumer_params.broker_exclusive_config['timeout_minutes']
        self._delete_after_ack = self.consumer_params.broker_exclusive_config['delete_after_ack']

        self._queue = DuckDBQueue(
            queue_name=self._queue_name,
            db_path=db_path,
        )
        self.logger.info(
            f"DuckDB Consumer initialized, queue: {self._queue_name}, "
            f"database: {db_path}, poll interval: {self._poll_interval}s, delete after ack: {self._delete_after_ack}"
        )

    def _dispatch_task(self):
        """
        Core dispatch method
        Loops to fetch messages from DuckDB and submit for execution
        """
        # Start timeout task recovery thread
        self._start_timeout_recovery()

        while True:
            try:
                task = self._queue.get(timeout=self._poll_interval)
                if task:
                    self._print_message_get_from_broker('DuckDB', task)
                    kw = {
                        'body': task['body'],
                        'job_id': task['job_id'],
                        'priority': task.get('priority', 0),
                    }
                    self._submit_task(kw)
            except Exception as e:
                self.logger.error(f"Exception fetching message: {e}", exc_info=True)
                time.sleep(1)

    def _start_timeout_recovery(self):
        """Start background thread for timeout task recovery"""
        def recovery_loop():
            while True:
                try:
                    recovered = self._queue.recover_timeout_tasks(self._timeout_minutes)
                    if recovered:
                        self.logger.info(f"Recovered {recovered} timed-out tasks")
                except Exception as e:
                    self.logger.error(f"Exception recovering timed-out tasks: {e}")
                time.sleep(60)  # Check every minute

        t = threading.Thread(
            target=recovery_loop,
            daemon=True,
            name=f"duckdb_recovery_{self._queue_name}"
        )
        t.start()

    def _confirm_consume(self, kw):
        """Acknowledge successful consumption, delete message or update status based on configuration"""
        self._queue.ack(kw['job_id'], delete=self._delete_after_ack)

    def _requeue(self, kw):
        """Re-queue message"""
        self._queue.requeue(kw['job_id'])


# ============================================================================
# Register Broker
# ============================================================================

# Define broker kind (use string for easy identification)
BROKER_KIND_DUCKDB = 'duckdb'

# Register default configuration
from funboost.core.broker_kind__exclusive_config_default_define import register_broker_exclusive_config_default

register_broker_exclusive_config_default(
    BROKER_KIND_DUCKDB,
    {
        'db_path': 'funboost_duckdb.db',  # Database file path, ':memory:' for in-memory mode
        'poll_interval': 1.0,              # Poll interval (seconds)
        'timeout_minutes': 10,             # Timeout recovery threshold (minutes)
        'priority': 0,                     # Default message priority
        'delete_after_ack': True,          # Whether to delete message after ack, False = update status to success
    }
)

# Register with funboost
register_custom_broker(BROKER_KIND_DUCKDB, DuckDBPublisher, DuckDBConsumer)


# ============================================================================
# Test code
# ============================================================================

if __name__ == '__main__':
    from funboost import boost, BoosterParams

    @boost(BoosterParams(
        queue_name='test_duckdb_queue',
        broker_kind=BROKER_KIND_DUCKDB,
        qps=5,
        concurrent_num=3,
        broker_exclusive_config={
            'db_path': Path(__file__).parent / 'test_funboost_duckdb.db',  # Use file storage
            # 'db_path': ':memory:',        # Or use in-memory mode
        }
    ))
    def test_func(x, y):
        print(f"Calculating: {x} + {y} = {x + y}")
        time.sleep(0.5)
        return x + y

    # Publish messages
    for i in range(20):
        test_func.push(i, y=i * 2)

    print(f"Queue message count: {test_func.publisher.get_message_count()}")

    # Start consuming
    test_func.consume()
