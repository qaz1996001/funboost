# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/18
"""
PostgreSQL Consumer - Native high-performance implementation
Leveraging PostgreSQL-specific features:
1. FOR UPDATE SKIP LOCKED - High-concurrency lock-free competition
2. LISTEN/NOTIFY - Real-time message push, avoiding unnecessary polling
"""
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.queues.postgres_queue import PostgresQueue


class PostgresConsumer(AbstractConsumer):
    """
    PostgreSQL native consumer

    Advantages over SQLAlchemy generic implementation:
    1. FOR UPDATE SKIP LOCKED: Lock-free competition during multi-consumer concurrency, significant performance improvement
    2. LISTEN/NOTIFY: Real-time notification mechanism, more efficient than polling
    3. Uses native psycopg2 connection pool
    """

    BROKER_KIND = None  # Will be automatically set by the framework

    def custom_init(self):
        self._use_listen_notify = self.consumer_params.broker_exclusive_config['use_listen_notify']
        self._poll_interval = self.consumer_params.broker_exclusive_config['poll_interval']
        self._timeout_minutes = self.consumer_params.broker_exclusive_config['timeout_minutes']
        
        self._queue = PostgresQueue(
            queue_name=self._queue_name,
            dsn=BrokerConnConfig.POSTGRES_DSN,
            min_conn=self.consumer_params.broker_exclusive_config['min_connections'],
            max_conn=self.consumer_params.broker_exclusive_config['max_connections'],
        )
        self.logger.info(
            f"PostgreSQL Consumer initialization complete, queue: {self._queue_name}, "
            f"LISTEN/NOTIFY: {self._use_listen_notify}"
        )

    def _dispatch_task(self):
        """
        Core dispatch method.
        Uses FOR UPDATE SKIP LOCKED to fetch tasks, achieving high-concurrency lock-free competition.
        Optionally enables LISTEN/NOTIFY for real-time push.
        """
        # Start timeout task recovery thread
        self._start_timeout_recovery()

        while True:
            try:
                if self._use_listen_notify:
                    # Use LISTEN/NOTIFY mechanism (recommended)
                    task = self._queue.get_with_listen(timeout=self._poll_interval)
                else:
                    # Use polling mechanism
                    task = self._queue.get(timeout=self._poll_interval)

                if task:
                    self._print_message_get_from_broker('PostgreSQL', task)
                    kw = {
                        'body': task['body'],
                        'job_id': task['job_id'],
                        'priority': task.get('priority', 0),
                    }
                    self._submit_task(kw)
            except Exception as e:
                self.logger.error(f"Error fetching message: {e}", exc_info=True)
                import time
                time.sleep(1)

    def _start_timeout_recovery(self):
        """Start background thread for timeout task recovery"""
        import threading

        def recovery_loop():
            import time
            while True:
                try:
                    recovered = self._queue.recover_timeout_tasks(self._timeout_minutes)
                    if recovered:
                        self.logger.info(f"Recovered {recovered} timed-out tasks")
                except Exception as e:
                    self.logger.error(f"Error recovering timed-out tasks: {e}")
                time.sleep(60)  # Check every minute

        t = threading.Thread(target=recovery_loop, daemon=True, name=f"pg_recovery_{self._queue_name}")
        t.start()

    def _confirm_consume(self, kw):
        """Confirm successful consumption, delete message"""
        self._queue.ack(kw['job_id'], delete=True)

    def _requeue(self, kw):
        """Requeue the message"""
        self._queue.requeue(kw['job_id'])
