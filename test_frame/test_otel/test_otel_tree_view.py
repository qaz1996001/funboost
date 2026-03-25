# -*- coding: utf-8 -*-
"""
Funboost OpenTelemetry Distributed Tracing Demo - Tree view version

Uses TreeSpanExporter to display a tree-structured trace diagram directly in the console,
without needing to install Jaeger or other middleware.
For production environments, it is strongly recommended to use a professional OpenTelemetry
tracing backend such as Jaeger/Zipkin/SkyWalking.
"""

# Perfect tree-structured diagram showing the message flow clearly.
# task_entry publishes 2 tasks to otel_tree_task_process, which then publishes 1 task to otel_tree_task_notify.
"""
================================================================================
Distributed Tracing Tree View
================================================================================

Trace ID: f50f7a80f0b8f88b97788093157c4ae2
------------------------------------------------------------
└── otel_tree_task_entry send [PRODUCER] OK 11.0ms
       span_id: 0x1c167373656fdc13    parent_id: null
       task_id: 019b4ed4-144d-76b2-86b0-7d4939fc94dc
    └── otel_tree_task_entry process [CONSUMER] OK 323.2ms
           span_id: 0xbc7fa8b030d5f600    parent_id: 0x1c167373656fdc13
           task_id: 019b4ed4-144d-76b2-86b0-7d4939fc94dc
        ├── otel_tree_task_process send [PRODUCER] OK 2.0ms
        │      span_id: 0xc1a5e958ffd61344    parent_id: 0xbc7fa8b030d5f600
        │      task_id: 019b4ed4-1a6d-7be3-8516-192449685f6d
        │   └── otel_tree_task_process process [CONSUMER] OK 215.9ms
        │          span_id: 0x575c4f47a70564b9    parent_id: 0xc1a5e958ffd61344
        │          task_id: 019b4ed4-1a6d-7be3-8516-192449685f6d
        │       └── otel_tree_task_notify send [PRODUCER] OK 2.0ms
        │              span_id: 0x81e9758e44a4ba61    parent_id: 0x575c4f47a70564b9
        │              task_id: 019b4ed4-4118-79fd-965c-c080bb0ca775
        │           └── otel_tree_task_notify process [CONSUMER] OK 118.5ms
        │                  span_id: 0x669734d0fa7eae20    parent_id: 0x81e9758e44a4ba61
        │                  task_id: 019b4ed4-4118-79fd-965c-c080bb0ca775
        └── otel_tree_task_process send [PRODUCER] OK 2.3ms
               span_id: 0x986af7dffd837e77    parent_id: 0xbc7fa8b030d5f600
               task_id: 019b4ed4-1a70-7d62-99cd-7e6e0f9038bf
            └── otel_tree_task_process process [CONSUMER] OK 212.6ms
                   span_id: 0xdb03f7288701f9bd    parent_id: 0x986af7dffd837e77
                   task_id: 019b4ed4-1a70-7d62-99cd-7e6e0f9038bf
                └── otel_tree_task_notify send [PRODUCER] OK 2.0ms
                       span_id: 0x5ad4e057be91c960    parent_id: 0xdb03f7288701f9bd
                       task_id: 019b4ed4-4120-7c53-8a5f-4f653d4e486f
                    └── otel_tree_task_notify process [CONSUMER] OK 107.7ms
                           span_id: 0xff4fd0fdf38fed92    parent_id: 0x5ad4e057be91c960
                           task_id: 019b4ed4-4120-7c53-8a5f-4f653d4e486f

================================================================================
"""


import asyncio

import time
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

from funboost import boost, BrokerEnum, BoosterParams, ConcurrentModeEnum,fct
from funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin import (
    AutoOtelPublisherMixin,
    AutoOtelConsumerMixin,
    OtelBoosterParams
)
from funboost.contrib.override_publisher_consumer_cls.otel_tree_span_exporter import (
    TreeSpanExporter,
    print_trace_tree
)


# =============================================================================
# Step 1: Initialize OpenTelemetry (using TreeSpanExporter)
# =============================================================================
tree_exporter = None  # Global variable for convenience when manually calling print


def init_opentelemetry():
    """
    Initialize OpenTelemetry configuration
    Uses TreeSpanExporter to display tree view in console
    """
    global tree_exporter

    # Create resource identifier
    resource = Resource.create({
        "service.name": "funboost-otel-demo",
        "service.version": "1.0.0",
    })

    # Create TracerProvider
    provider = TracerProvider(resource=resource)

    # Use TreeSpanExporter - manually call print_tree() after tasks complete to print tree view
    tree_exporter = TreeSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(tree_exporter))

    # Set global TracerProvider
    trace.set_tracer_provider(provider)

    print("OpenTelemetry initialized successfully (using TreeSpanExporter)")


# =============================================================================
# Step 2: Define task functions with OTEL tracing
# =============================================================================

@boost(OtelBoosterParams(
    queue_name='otel_tree_task_entry',
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=2,

))
def task_entry(order_id: int, user_name: str):
    """Entry task: process order entry"""

    print(fct.full_msg)
    print(f"[Task entry] Starting to process order #{order_id}, user: {user_name}")
    time.sleep(0.3)

    # Trigger downstream tasks
    aio_task_process.push(order_id=order_id, step="Verify inventory")
    aio_task_process.push(order_id=order_id, step="Calculate price")

    print(f"[Task entry] Order #{order_id} has been dispatched")
    return {"status": "dispatched", "order_id": order_id}


@boost(OtelBoosterParams(
    queue_name='otel_tree_task_process',
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=3,
    concurrent_mode=ConcurrentModeEnum.ASYNC,

))
async def aio_task_process(order_id: int, step: str):
    """Processing task: execute specific order processing steps"""
    print(fct.full_msg)
    print(f"[Processing task] Order #{order_id} - Executing step: {step}")
    await asyncio.sleep(0.2)

    # Trigger notification task
    task_notify.push(order_id=order_id, message=f"Step '{step}' completed")

    print(f"[Processing task] Order #{order_id} - Step '{step}' completed")
    return {"order_id": order_id, "step": step, "status": "completed"}


@boost(OtelBoosterParams(
    queue_name='otel_tree_task_notify',
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=2,

))
def task_notify(order_id: int, message: str):
    """Notification task: send notification"""
    print(fct.full_msg)
    print(f"[Notification task] Order #{order_id} - Sending notification: {message}")
    time.sleep(0.1)
    print(f"[Notification task] Order #{order_id} - Notification sent successfully")
    return {"order_id": order_id, "notified": True}


# =============================================================================
# Main entry point
# =============================================================================
if __name__ == '__main__':
    # Initialize OpenTelemetry
    init_opentelemetry()

    print("\n" + "=" * 60)
    print("Funboost OpenTelemetry Distributed Tracing Demo - Tree view version")
    print("=" * 60 + "\n")

    # Publish tasks
    print("[Publish tasks]")
    task_entry.push(order_id=1, user_name="Zhang San")
    task_entry.push(order_id=2, user_name="Li Si")

    print("\n" + "-" * 60)
    print("Starting task consumption...")
    print("-" * 60 + "\n")

    # Start all consumers (non-blocking)
    task_notify.consume()
    aio_task_process.consume()
    task_entry.consume()

    # Use wait_for_possible_has_finish_all_tasks to determine when all tasks are consumed
    # This is more accurate than a fixed sleep
    from funboost.consumers.base_consumer import wait_for_possible_has_finish_all_tasks_by_conusmer_list

    print("Waiting for all tasks to be consumed...")

    # Get consumer instance list
    consumer_list = [
        task_entry.consumer,
        aio_task_process.consumer,
        task_notify.consumer,
    ]

    # Wait for all consumers to finish tasks (considered done when no new tasks for 2 consecutive minutes and queue is empty)
    # wait_for_possible_has_finish_all_tasks_by_conusmer_list(consumer_list, minutes=2)
    time.sleep(30)

    print("\nAll tasks consumed successfully!")

    # Print tree view
    print("\n" + "=" * 60)
    print("Distributed Tracing Tree View")
    print("=" * 60)
    tree_exporter.print_tree()

    print("\nDemo completed!")

    # Exit program
    import os
    os._exit(0)
