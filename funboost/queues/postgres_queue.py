# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/18
"""
Native PostgreSQL message queue implementation
Leveraging PostgreSQL's unique advantages over MySQL:
1. FOR UPDATE SKIP LOCKED - Lock-free task acquisition under high concurrency, multiple consumers don't block
2. LISTEN/NOTIFY - Native pub/sub mechanism, real-time push without polling
3. RETURNING - Returns data directly after insert/update, reducing queries
4. Stronger transaction isolation and concurrency control
"""
import json
import time


import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

from funboost.core.loggers import FunboostFileLoggerMixin, LoggerLevelSetterMixin
from funboost.utils import decorators


class TaskStatus:
    TO_BE_CONSUMED = 'to_be_consumed'
    PENDING = 'pending'
    FAILED = 'failed'
    SUCCESS = 'success'
    REQUEUE = 'requeue'


@decorators.flyweight
class PostgresQueue(FunboostFileLoggerMixin, LoggerLevelSetterMixin):
    """
    Native PostgreSQL queue implementation, leveraging PostgreSQL-specific features:
    - FOR UPDATE SKIP LOCKED: Lock-free competition among multiple consumers under high concurrency
    - LISTEN/NOTIFY: Real-time message notification, avoiding polling
    - RETURNING: Reduces extra queries
    """

    def __init__(self, queue_name: str, dsn: str, min_conn: int = 2, max_conn: int = 20):
        """
        :param queue_name: Queue name (used as table name)
        :param dsn: PostgreSQL connection string, e.g. "host=localhost dbname=funboost user=postgres password=xxx"
        :param min_conn: Minimum number of connections in the pool
        :param max_conn: Maximum number of connections in the pool
        """
        self.queue_name = queue_name
        self._dsn = dsn
        self._table_name = f"funboost_queue_{queue_name}"
        self._notify_channel = f"funboost_notify_{queue_name}"

        # Create thread-safe connection pool
        self._pool = ThreadedConnectionPool(min_conn, max_conn, dsn)
        self._create_table()
        self._listen_conn = None
        self._is_listening = False

        self.logger.info(f"PostgreSQL queue [{queue_name}] initialization complete, using SKIP LOCKED + LISTEN/NOTIFY")

    def _get_conn(self):
        return self._pool.getconn()

    def _put_conn(self, conn):
        self._pool.putconn(conn)

    def _create_table(self):
        """Create the queue table with necessary indexes"""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                # Create table
                cur.execute(sql.SQL("""
                    CREATE TABLE IF NOT EXISTS {} (
                        job_id BIGSERIAL PRIMARY KEY,
                        body TEXT NOT NULL,
                        status VARCHAR(20) DEFAULT 'to_be_consumed',
                        priority INTEGER DEFAULT 0,
                        publish_time TIMESTAMP DEFAULT NOW(),
                        consume_start_time TIMESTAMP,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """).format(sql.Identifier(self._table_name)))

                # Create index: status + priority + publish time (for efficient task retrieval)
                cur.execute(sql.SQL("""
                    CREATE INDEX IF NOT EXISTS {} ON {} (status, priority DESC, publish_time ASC)
                    WHERE status IN ('to_be_consumed', 'requeue')
                """).format(
                    sql.Identifier(f"idx_{self._table_name}_status_priority"),
                    sql.Identifier(self._table_name)
                ))

                conn.commit()
        finally:
            self._put_conn(conn)

    def push(self, body: str, priority: int = 0) -> int:
        """
        Publish a message to the queue
        Uses RETURNING to directly return job_id without extra queries
        """
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("""
                        INSERT INTO {} (body, status, priority)
                        VALUES (%s, %s, %s)
                        RETURNING job_id
                    """).format(sql.Identifier(self._table_name)),
                    (body, TaskStatus.TO_BE_CONSUMED, priority)
                )
                job_id = cur.fetchone()[0]
                conn.commit()

                # Send NOTIFY to inform consumers of new messages
                cur.execute(sql.SQL("NOTIFY {}, %s").format(sql.Identifier(self._notify_channel)), (str(job_id),))
                conn.commit()

                return job_id
        finally:
            self._put_conn(conn)

    def bulk_push(self, items: list) -> list:
        """
        Batch publish messages
        :param items: [{'body': str, 'priority': int}, ...]
        :return: List of job_ids
        """
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                job_ids = []
                for item in items:
                    body = item.get('body') if isinstance(item, dict) else item
                    priority = item.get('priority', 0) if isinstance(item, dict) else 0
                    cur.execute(
                        sql.SQL("""
                            INSERT INTO {} (body, status, priority)
                            VALUES (%s, %s, %s)
                            RETURNING job_id
                        """).format(sql.Identifier(self._table_name)),
                        (body, TaskStatus.TO_BE_CONSUMED, priority)
                    )
                    job_ids.append(cur.fetchone()[0])
                conn.commit()

                # Batch notification
                cur.execute(sql.SQL("NOTIFY {}, %s").format(sql.Identifier(self._notify_channel)), ('bulk',))
                conn.commit()

                return job_ids
        finally:
            self._put_conn(conn)

    def get(self, timeout: float = None) -> dict:
        """
        Get one message (core method)

        Leverages PostgreSQL's FOR UPDATE SKIP LOCKED:
        - Multiple consumers fetching concurrently won't block each other
        - Rows already locked by other consumers are skipped
        - Significantly improves throughput in high-concurrency scenarios
        """
        conn = self._get_conn()
        try:
            start_time = time.time()
            while True:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Use FOR UPDATE SKIP LOCKED for lock-free task acquisition
                    # Get by priority descending, publish time ascending
                    cur.execute(
                        sql.SQL("""
                            UPDATE {} SET
                                status = %s,
                                consume_start_time = NOW()
                            WHERE job_id = (
                                SELECT job_id FROM {}
                                WHERE status IN ('to_be_consumed', 'requeue')
                                ORDER BY priority DESC, publish_time ASC
                                FOR UPDATE SKIP LOCKED
                                LIMIT 1
                            )
                            RETURNING job_id, body, status, priority, publish_time, consume_start_time
                        """).format(
                            sql.Identifier(self._table_name),
                            sql.Identifier(self._table_name)
                        ),
                        (TaskStatus.PENDING,)
                    )
                    row = cur.fetchone()
                    conn.commit()

                    if row:
                        return dict(row)

                # No messages, briefly wait then retry
                if timeout and (time.time() - start_time) >= timeout:
                    return None

                time.sleep(0.1)  # Polling interval
        finally:
            self._put_conn(conn)

    def get_with_listen(self, timeout: float = 30) -> dict:
        """
        Get messages using LISTEN/NOTIFY mechanism (recommended)

        PostgreSQL-specific feature:
        - Producer sends NOTIFY on push
        - Consumer LISTENs and waits for notifications
        - More efficient than polling, with better real-time performance
        """
        # First try to get directly
        task = self.get(timeout=0.01)
        if task:
            return task

        # No messages, use LISTEN to wait for notifications
        if not self._listen_conn:
            self._listen_conn = psycopg2.connect(self._dsn)
            self._listen_conn.autocommit = True
            with self._listen_conn.cursor() as cur:
                cur.execute(sql.SQL("LISTEN {}").format(sql.Identifier(self._notify_channel)))

        import select
        start_time = time.time()
        while True:
            # Wait for notification
            if select.select([self._listen_conn], [], [], min(1.0, timeout)) == ([], [], []):
                # Timeout, try to get one more time
                if (time.time() - start_time) >= timeout:
                    return self.get(timeout=0.01)
                continue

            # Received notification, consume it and get the task
            self._listen_conn.poll()
            while self._listen_conn.notifies:
                self._listen_conn.notifies.pop()

            task = self.get(timeout=0.01)
            if task:
                return task

            if (time.time() - start_time) >= timeout:
                return None

    def ack(self, job_id: int, delete: bool = True):
        """Acknowledge successful consumption"""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                if delete:
                    cur.execute(
                        sql.SQL("DELETE FROM {} WHERE job_id = %s").format(sql.Identifier(self._table_name)),
                        (job_id,)
                    )
                else:
                    cur.execute(
                        sql.SQL("UPDATE {} SET status = %s WHERE job_id = %s").format(sql.Identifier(self._table_name)),
                        (TaskStatus.SUCCESS, job_id)
                    )
                conn.commit()
        finally:
            self._put_conn(conn)

    def requeue(self, job_id: int):
        """Requeue the message"""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("""
                        UPDATE {} SET status = %s, consume_start_time = NULL
                        WHERE job_id = %s
                    """).format(sql.Identifier(self._table_name)),
                    (TaskStatus.REQUEUE, job_id)
                )
                conn.commit()
                # Notify other consumers
                cur.execute(sql.SQL("NOTIFY {}, %s").format(sql.Identifier(self._notify_channel)), (str(job_id),))
                conn.commit()
        finally:
            self._put_conn(conn)

    def clear(self):
        """Clear the queue"""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql.SQL("TRUNCATE TABLE {}").format(sql.Identifier(self._table_name)))
                conn.commit()
        finally:
            self._put_conn(conn)

    def get_message_count(self) -> int:
        """Get the number of messages pending consumption"""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("""
                        SELECT COUNT(*) FROM {}
                        WHERE status IN ('to_be_consumed', 'requeue')
                    """).format(sql.Identifier(self._table_name))
                )
                return cur.fetchone()[0]
        finally:
            self._put_conn(conn)

    def recover_timeout_tasks(self, timeout_minutes: int = 10):
        """
        Recover tasks that timed out without acknowledgment
        Resets PENDING tasks older than timeout_minutes back to TO_BE_CONSUMED
        """
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("""
                        UPDATE {} SET status = %s, consume_start_time = NULL
                        WHERE status = %s
                        AND consume_start_time < NOW() - INTERVAL '%s minutes'
                        RETURNING job_id
                    """).format(sql.Identifier(self._table_name)),
                    (TaskStatus.TO_BE_CONSUMED, TaskStatus.PENDING, timeout_minutes)
                )
                recovered = cur.fetchall()
                conn.commit()
                if recovered:
                    self.logger.info(f"Recovered {len(recovered)} timed-out tasks")
                    cur.execute(sql.SQL("NOTIFY {}, %s").format(sql.Identifier(self._notify_channel)), ('recover',))
                    conn.commit()
                return len(recovered)
        finally:
            self._put_conn(conn)

    def close(self):
        """Close the connection pool"""
        if self._listen_conn:
            self._listen_conn.close()
        self._pool.closeall()


if __name__ == '__main__':
    # Test code
    dsn = "host=localhost dbname=funboost user=postgres password=123456"
    queue = PostgresQueue('test_queue', dsn)

    # Publish messages
    for i in range(10):
        job_id = queue.push(json.dumps({'x': i, 'y': i * 2}), priority=i % 3)
        print(f"Published job_id: {job_id}")

    # Consume messages
    while True:
        task = queue.get(timeout=5)
        if not task:
            break
        print(f"Got task: {task}")
        queue.ack(task['job_id'])

    queue.close()
    