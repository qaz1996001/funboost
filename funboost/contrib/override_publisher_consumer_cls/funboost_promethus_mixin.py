# -*- coding: utf-8 -*-
"""
Funboost Prometheus Monitoring Metrics Mixin

Provides Prometheus metrics collection capability, automatically reporting task execution status, latency, and other metrics.

Supports two modes:
1. HTTP Server mode (single process) — Prometheus scrapes metrics actively
2. Push Gateway mode (multi-process) — actively pushes metrics to Pushgateway

Usage 1: HTTP Server mode (single process)
```python
from funboost import boost
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusBoosterParams,
    start_prometheus_http_server
)

# Start Prometheus HTTP server (default port 8000)
start_prometheus_http_server(port=8000)

@boost(PrometheusBoosterParams(queue_name='my_task'))
def my_task(x):
    return x * 2

my_task.consume()
```

Usage 2: Push Gateway mode (recommended for multi-process)
```python
from funboost import boost
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusPushGatewayBoosterParams,
)

@boost(PrometheusPushGatewayBoosterParams(
    queue_name='my_task',
    user_options={
        'prometheus_pushgateway_url': 'localhost:9091',  # Pushgateway address
        'prometheus_push_interval': 10.0,                # Push interval (seconds)
        'prometheus_job_name': 'my_app',                 # Prometheus job name
    }
))
def my_task(x):
    return x * 2

my_task.consume()
```

Metrics description:
- funboost_task_total: Task counter (labels: queue, status)
- funboost_task_latency_seconds: Task execution latency histogram (labels: queue)
- funboost_task_retries_total: Task retry counter (labels: queue)
- funboost_queue_msg_count: Number of messages remaining in the queue (labels: queue)
- funboost_publish_total: Published message counter (labels: queue)
"""

import os
import time
import socket
import threading
import typing
import atexit

from prometheus_client import (
    Counter, Histogram, Gauge,
    start_http_server, 
    push_to_gateway, delete_from_gateway,
    REGISTRY
)

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.core.func_params_model import BoosterParams
from funboost.core.function_result_status_saver import FunctionResultStatus


# ============================================================
# Prometheus Metrics Definitions
# ============================================================

# Task counter (grouped by queue and status)
TASK_TOTAL = Counter(
    'funboost_task_total',
    'Total number of tasks processed',
    ['queue', 'status']  # status: success, fail, requeue, dlx
)

# Task latency histogram (grouped by queue)
TASK_LATENCY = Histogram(
    'funboost_task_latency_seconds',
    'Task execution latency in seconds',
    ['queue'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, float('inf'))
)

# Retry counter (grouped by queue)
TASK_RETRIES = Counter(
    'funboost_task_retries_total',
    'Total number of task retries',
    ['queue']
)

# Number of messages remaining in queue (grouped by queue)
QUEUE_MSG_COUNT = Gauge(
    'funboost_queue_msg_count',
    'Number of messages remaining in the queue',
    ['queue']
)

# Published message counter (grouped by queue)
PUBLISH_TOTAL = Counter(
    'funboost_publish_total',
    'Total number of messages published',
    ['queue']
)


# ============================================================
# Prometheus Publisher Mixin (publisher metrics collection)
# ============================================================

class PrometheusPublisherMixin(AbstractPublisher):
    """
    Prometheus Metrics Collection Publisher Mixin

    Automatically collects the count metric for published messages.
    """

    def _after_publish(self, msg: dict, msg_function_kw: dict, task_id: str):
        """
        Hook method called after publishing a message, records Prometheus publish metric
        """
        PUBLISH_TOTAL.labels(queue=self.queue_name).inc()
        super()._after_publish(msg, msg_function_kw, task_id)


# ============================================================
# Prometheus Consumer Mixin (basic version - HTTP Server mode)
# ============================================================

class PrometheusConsumerMixin(AbstractConsumer):
    """
    Prometheus Metrics Collection Consumer Mixin (HTTP Server mode)

    Automatically collects the following metrics:
    - Task success/failure count
    - Task execution latency
    - Retry count

    Implemented via the framework-provided _both_sync_and_aio_frame_custom_record_process_info_func hook,
    which is called for both synchronous and asynchronous tasks — no need to implement separately.
    """

    def _both_sync_and_aio_frame_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus, kw: dict):
        """
        Framework callback method, called after both synchronous and asynchronous task execution to collect Prometheus metrics
        """
        self._record_prometheus_metrics(current_function_result_status)
        super()._both_sync_and_aio_frame_custom_record_process_info_func(current_function_result_status, kw)

    def _record_prometheus_metrics(self, function_result_status: FunctionResultStatus):
        """
        Record Prometheus metrics

        :param function_result_status: Function execution status, contains time_start, time_cost, etc.
        """
        queue_name = self.queue_name

        # Determine task status
        if function_result_status is None:
            status = 'unknown'
            latency = 0.0
        else:
            # Use framework-provided time_cost; calculate if not available
            latency = function_result_status.time_cost if function_result_status.time_cost else (time.time() - function_result_status.time_start)

            if function_result_status._has_requeue:
                status = 'requeue'
            elif function_result_status._has_to_dlx_queue:
                status = 'dlx'
            elif function_result_status.success:
                status = 'success'
            else:
                status = 'fail'

        # Record task count
        TASK_TOTAL.labels(queue=queue_name, status=status).inc()

        # Record task latency
        TASK_LATENCY.labels(queue=queue_name).observe(latency)

        # Record retry count (if retries occurred)
        if function_result_status and function_result_status.run_times > 1:
            retry_count = function_result_status.run_times - 1
            TASK_RETRIES.labels(queue=queue_name).inc(retry_count)

        # Record number of messages remaining in the queue
        msg_num_in_broker = self.metric_calculation.msg_num_in_broker
        if msg_num_in_broker is not None and msg_num_in_broker >= 0:
            QUEUE_MSG_COUNT.labels(queue=queue_name).set(msg_num_in_broker)


# ============================================================
# Push Gateway Consumer Mixin (recommended for multi-process)
# ============================================================

class PrometheusPushGatewayConsumerMixin(PrometheusConsumerMixin):
    """
    Prometheus Push Gateway mode Consumer Mixin

    Suitable for multi-process scenarios; automatically pushes metrics to Pushgateway at regular intervals.

    Features:
    - Background thread pushes metrics periodically
    - Automatically generates instance identifier (hostname_pid)
    - Automatically cleans up metrics on process exit
    """

    # Class-level variables to ensure only one push thread is started per process
    _push_thread_started: typing.ClassVar[bool] = False
    _push_thread_lock: typing.ClassVar[threading.Lock] = threading.Lock()

    def custom_init(self):
        """Start Push Gateway background thread on initialization"""
        super().custom_init()
        self._start_push_gateway_thread_if_needed()

    def _start_push_gateway_thread_if_needed(self):
        """Start Push Gateway push thread (ensure it is only started once)"""
        # Get Prometheus configuration from user_options
        user_options = self.consumer_params.user_options or {}
        pushgateway_url = user_options.get('prometheus_pushgateway_url', None)
        if not pushgateway_url:
            raise ValueError('prometheus_pushgateway_url is required')

        with self._push_thread_lock:
            if PrometheusPushGatewayConsumerMixin._push_thread_started:
                return
            PrometheusPushGatewayConsumerMixin._push_thread_started = True

        # Get configuration from user_options
        push_interval = user_options.get('prometheus_push_interval', 10.0)
        job_name = user_options.get('prometheus_job_name', 'funboost')

        # Generate instance identifier
        hostname = socket.gethostname()
        pid = os.getpid()
        instance_id = f'{hostname}_{pid}'

        grouping_key = {'instance': instance_id}

        # Start background push thread
        def push_loop():
            while True:
                try:
                    push_to_gateway(
                        pushgateway_url,
                        job=job_name,
                        grouping_key=grouping_key,
                        registry=REGISTRY
                    )
                except Exception as e:
                    # Silently handle push failures to avoid affecting the main business
                    pass
                time.sleep(push_interval)

        push_thread = threading.Thread(target=push_loop, daemon=True, name='prometheus_push_thread')
        push_thread.start()

        # Register cleanup on exit
        def cleanup():
            try:
                delete_from_gateway(
                    pushgateway_url,
                    job=job_name,
                    grouping_key=grouping_key
                )
            except Exception:
                pass

        atexit.register(cleanup)

        self.logger.info(f'🔥 Prometheus Push Gateway started: {pushgateway_url}, interval={push_interval}s, instance={instance_id}')


# ============================================================
# Pre-configured BoosterParams
# ============================================================

class PrometheusBoosterParams(BoosterParams):
    """
    BoosterParams pre-configured with Prometheus metrics collection (HTTP Server mode)

    Suitable for single-process scenarios; must be used together with start_prometheus_http_server().
    Automatically collects metrics for both consumer and publisher.
    """
    consumer_override_cls: typing.Type[PrometheusConsumerMixin] = PrometheusConsumerMixin
    publisher_override_cls: typing.Type[PrometheusPublisherMixin] = PrometheusPublisherMixin


class PrometheusPushGatewayBoosterParams(BoosterParams):
    """
    BoosterParams pre-configured with Prometheus Push Gateway (recommended for multi-process)

    Suitable for multi-process scenarios; automatically pushes metrics to Pushgateway.
    Automatically collects metrics for both consumer and publisher.

    Prometheus configuration is passed via user_options, supporting the following keys:
    - prometheus_pushgateway_url: Pushgateway address, e.g. 'localhost:9091' (required)
    - prometheus_push_interval: Push interval in seconds, default 10.0
    - prometheus_job_name: Prometheus job name, default 'funboost'

    Usage:
    ```python
    @boost(PrometheusPushGatewayBoosterParams(
        queue_name='my_task',
        user_options={
            'prometheus_pushgateway_url': 'localhost:9091',
            'prometheus_push_interval': 10.0,
            'prometheus_job_name': 'my_app',
        }
    ))
    def my_task(x):
        return x * 2
    ```
    """
    consumer_override_cls: typing.Type[PrometheusPushGatewayConsumerMixin] = PrometheusPushGatewayConsumerMixin
    publisher_override_cls: typing.Type[PrometheusPublisherMixin] = PrometheusPublisherMixin


# ============================================================
# Helper functions
# ============================================================

def start_prometheus_http_server(port: int = 8000, addr: str = '0.0.0.0'):
    """
    Start Prometheus HTTP server (single-process mode)

    After starting, metrics can be accessed at http://<addr>:<port>/metrics

    :param port: HTTP port, default 8000
    :param addr: Bind address, default 0.0.0.0
    """
    start_http_server(port, addr)
    print(f'🔥 Prometheus metrics server started at http://{addr}:{port}/metrics')


# ============================================================
# Exports
# ============================================================

__all__ = [
    # Mixin
    'PrometheusConsumerMixin',
    'PrometheusPushGatewayConsumerMixin',
    'PrometheusPublisherMixin',
    
    # Params
    'PrometheusBoosterParams',
    'PrometheusPushGatewayBoosterParams',
    
    # Helper
    'start_prometheus_http_server',
    
    # Metrics
    'TASK_TOTAL',
    'TASK_LATENCY',
    'TASK_RETRIES',
    'QUEUE_MSG_COUNT',
    'PUBLISH_TOTAL',
]
