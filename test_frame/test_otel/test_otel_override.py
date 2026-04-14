# -*- coding: utf-8 -*-
"""
Funboost OpenTelemetry Distributed Tracing Demo

Demonstrates how to use AutoOtelPublisherMixin and AutoOtelConsumerMixin
to implement distributed tracing.

Before running, install dependencies:
    pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-exporter-jaeger

You can use Jaeger or other OpenTelemetry-compatible backends to view trace data.
Start Jaeger container (optional):
    docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 14250:14250 \
  -p 14268:14268 \
  -p 14269:14269 \
  -p 9411:9411 \
  jaegertracing/all-in-one:latest

Then visit http://localhost:16686 to view trace data.
"""

import os
import time

from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Optional: if Jaeger exporter is installed, use the following import
# from opentelemetry.exporter.jaeger.thrift import JaegerExporter

from funboost import boost, BrokerEnum, fct
from funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin import (
    OtelBoosterParams
)

# Load .env file (change to your own path as needed)
load_dotenv('/my_dotenv.env')


# =============================================================================
# Step 1: Initialize OpenTelemetry
# =============================================================================
def init_opentelemetry():
    """
    Initialize OpenTelemetry configuration
    - Configure TracerProvider
    - Add SpanProcessor (console output or send to Jaeger)
    """
    # Create resource identifier
    resource = Resource.create({
        "service.name": "funboost-otel-demo",
        "service.version": "1.0.0",
    })

    # Create TracerProvider
    provider = TracerProvider(resource=resource)

    # Option 1: Console output (for development/debugging)
    # console_exporter = ConsoleSpanExporter()
    # provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # Option 2: Jaeger exporter (recommended for production)
    # Requires: pip install opentelemetry-exporter-jaeger
    # Recommended: pip install opentelemetry-exporter-otlp
    # In opentelemetry-python, the class is OTLPSpanExporter (uppercase OTLP)
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    # jaeger_exporter = JaegerExporter(
    #     agent_host_name="localhost",
    #     agent_port=6831,
    # )
    otlp_exporter = OTLPSpanExporter(
    endpoint=f"{os.getenv('TENXUNYUN__HOST')}:4317",
    insecure=True
    )
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set global TracerProvider
    trace.set_tracer_provider(provider)

    print("OpenTelemetry initialized successfully")


# =============================================================================
# Step 2: Define task functions with OTEL tracing
# =============================================================================

# Task 1: Entry task, will call Task 2
@boost(OtelBoosterParams(
    queue_name='otel_demo_task_entry',
    broker_kind=BrokerEnum.REDIS,  # Using SQLite queue for easy local testing
    concurrent_num=2,
))
def task_entry(order_id: int, user_name: str):
    """
    Entry task: process order entry
    Automatically creates a Span and propagates trace context to downstream tasks
    """
    print(fct.queue_name,fct.full_msg)

    print(f"[Task entry] Starting to process order #{order_id}, user: {user_name}")
    time.sleep(3)  # Simulate business processing

    # Trigger downstream tasks (trace context propagates automatically)
    task_process.push(order_id=order_id, step="Verify inventory")
    task_process.push(order_id=order_id, step="Calculate price")

    print(f"[Task entry] Order #{order_id} has been dispatched to processing queue")
    return {"status": "dispatched", "order_id": order_id}


# Task 2: Processing task
@boost(OtelBoosterParams(
    queue_name='otel_demo_task_process',
    broker_kind=BrokerEnum.REDIS,
    concurrent_num=3,
))
def task_process(order_id: int, step: str):
    """
    Processing task: execute specific order processing steps
    Appears as a child Span of task_entry in the trace
    """

    print(fct.queue_name,fct.full_msg)

    print(f"[Processing task] Order #{order_id} - Executing step: {step}")
    time.sleep(2)  # Simulate processing time

    # Trigger notification task
    task_notify.push(order_id=order_id, message=f"Step '{step}' completed")

    print(f"[Processing task] Order #{order_id} - Step '{step}' completed")
    return {"order_id": order_id, "step": step, "status": "completed"}


# Task 3: Notification task
@boost(OtelBoosterParams(
    queue_name='otel_demo_task_notify',
    broker_kind=BrokerEnum.REDIS,
    concurrent_num=2,
))
def task_notify(order_id: int, message: str):
    """
    Notification task: send notification
    Appears as a child Span of task_process in the trace
    """

    print(fct.queue_name,fct.full_msg)

    print(f"[Notification task] Order #{order_id} - Sending notification: {message}")
    time.sleep(1)  # Simulate sending notification
    print(f"[Notification task] Order #{order_id} - Notification sent successfully")
    return {"order_id": order_id, "notified": True}


# =============================================================================
# Step 3: Demonstrate manually creating a parent Span (same process)
# =============================================================================
def demo_with_manual_parent_span():
    """
    Demonstrates creating a root Span from an HTTP request or other entry point,
    then propagating the trace context to the task queue
    """
    tracer = trace.get_tracer("funboost-demo")

    # Simulate an HTTP request entry point
    with tracer.start_as_current_span("HTTP POST /orders") as span:
        span.set_attribute("http.method", "POST")
        span.set_attribute("http.url", "/orders")

        print("\n[HTTP Request] Received create order request")

        # Publish tasks (OTEL Mixin automatically captures current context and propagates it)
        for i in range(3):
            order_id = 1000 + i
            task_entry.push(order_id=order_id, user_name=f"User_{i}")
            print(f"   Pushed order #{order_id} to queue")

        print("[HTTP Request] Request processing completed\n")


# =============================================================================
# Step 4: Demonstrate cross-machine/cross-service context propagation (pseudo-code)
# =============================================================================
"""
[Scenario description]
When a request comes from an external service (e.g., a Java/Go service on another machine),
the trace context is passed via HTTP Headers and cannot be obtained automatically.
It must be manually extracted from the headers and then passed to funboost.

Typical HTTP Headers format (W3C Trace Context standard):
    traceparent: 00-<trace_id>-<span_id>-<flags>
    tracestate: <vendor-specific data>

Example:
    traceparent: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
"""

def demo_cross_service_context_propagation():
    """
    Pseudo-code example: cross-machine/cross-service trace context propagation

    Scenario:
    - Machine A (Java service) sends HTTP request to Machine B (Python Web)
    - Machine B's Web API receives the request, extracts trace context from headers
    - Then pushes tasks to funboost message queue, keeping the trace chain intact
    """
    from opentelemetry.propagate import extract

    # =========================================================================
    # [Pseudo-code] Flask / FastAPI API example
    # =========================================================================

    # ----- Flask example -----
    """
    from flask import Flask, request

    app = Flask(__name__)

    @app.route('/api/orders', methods=['POST'])
    def create_order():
        # 1. Extract trace context from HTTP headers
        #    Flask's request.headers is a dict-like object
        carrier = dict(request.headers)
        parent_ctx = extract(carrier)

        # 2. Option A: Create a new span with the extracted context, then push
        #    This way, OtelMixin automatically gets the context when pushing
        tracer = trace.get_tracer("order-service")
        with tracer.start_as_current_span("create_order", context=parent_ctx):
            order_data = request.json
            task_entry.push(order_id=order_data['id'], user_name=order_data['user'])

        # 2. Option B: Manually pass carrier into extra.otel_context (lower-level approach)
        #    Suitable when you don't want to create an intermediate span
        task_entry.publish(
            msg={'order_id': 123, 'user_name': 'Zhang San'},
            # The publish method will check extra.otel_context and use it as parent context
        )
        # Note: if headers contain traceparent, OtelMixin.publish handles it automatically
        # since publish internally calls context.get_current(), which uses it if you extracted and set the context first

        return {'status': 'ok'}
    """

    # ----- FastAPI example -----
    """
    from fastapi import FastAPI, Request

    app = FastAPI()

    @app.post('/api/orders')
    async def create_order(request: Request):
        # 1. Extract trace context from HTTP headers
        carrier = dict(request.headers)
        parent_ctx = extract(carrier)

        # 2. Create span under extracted context and push task
        tracer = trace.get_tracer("order-service")
        with tracer.start_as_current_span("create_order", context=parent_ctx):
            body = await request.json()
            task_entry.push(order_id=body['id'], user_name=body['user'])

        return {'status': 'ok'}
    """

    # =========================================================================
    # [Actual runnable simulation code] Simulate HTTP headers from external service
    # =========================================================================

    # Simulate HTTP headers from an external service (e.g., a Java gateway)
    # These headers contain the trace context from the upstream service
    incoming_headers = {
        # W3C Trace Context format
        'traceparent': '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01',
        'tracestate': 'rojo=00f067aa0ba902b7',
        # Other common business headers
        'X-Request-ID': 'req-12345',
        'Content-Type': 'application/json',
    }

    print("\n[Cross-service] Received request from external service")
    print(f"   traceparent: {incoming_headers.get('traceparent')}")

    # Extract trace context from headers
    parent_ctx = extract(incoming_headers)

    # Create local span under extracted context and push tasks
    tracer = trace.get_tracer("funboost-demo")
    with tracer.start_as_current_span("handle_external_request", context=parent_ctx) as span:
        span.set_attribute("http.method", "POST")
        span.set_attribute("http.url", "/api/orders")
        span.set_attribute("external.request_id", incoming_headers.get('X-Request-ID', ''))

        # Push task - OtelMixin automatically injects current span's context into the message
        task_entry.push(order_id=9999, user_name="External service user")
        print("   Task pushed to queue, trace context passed")

    print("[Cross-service] Request processing completed\n")


# =============================================================================
# Step 5: Demonstrate aio_publish cross-thread scenario (auto context propagation)
# =============================================================================
"""
[Scenario description]
aio_publish uses run_in_executor to execute publish in a thread pool,
but Python's contextvars do not propagate across threads by default, so OTEL context is lost.

AutoOtelPublisherMixin's solution (handled automatically; no user intervention needed):
1. aio_publish captures OTel context in the current asyncio thread first
2. Automatically injects it into message's extra.otel_context
3. Then calls the parent class's aio_publish (executed in executor thread)
4. publish detects that otel_context already exists and uses it as parent context

Users just call aio_publish normally; no extra steps needed!
"""

async def demo_aio_publish_auto_context():
    """
    Demonstrates automatic OTel context propagation in aio_publish scenarios.

    AutoOtelPublisherMixin already handles cross-thread context propagation automatically.
    Users just call aio_publish normally; no manual context injection needed.

    This scenario closely resembles: external request -> FastAPI -> aio_publish to message queue.
    """
    from opentelemetry.propagate import extract
    from opentelemetry.trace import SpanKind

    # Simulate HTTP headers from an external service (e.g., a Java gateway)
    # These headers contain the trace context from the upstream service
    incoming_headers = {
        # W3C Trace Context format
        'traceparent': '00-0af8151916cd43dd8448eb211c80319c-b7ad6b7169203331-01',
        'tracestate': 'rojo=00f067aa0ba902b7',
        # Other common business headers
        'X-Request-ID': 'req-12345',
        'Content-Type': 'application/json',
    }

    print("\n[Cross-service] Received request from external service")
    print(f"   traceparent: {incoming_headers.get('traceparent')}")

    # Extract trace context from headers
    parent_ctx = extract(incoming_headers)

    tracer = trace.get_tracer("funboost-fastapi-aio-publish-demo")

    print("\n[aio_publish] Demonstrating automatic context propagation in async publish")

    # Create a parent span (simulating a FastAPI request handler)
    with tracer.start_as_current_span("async_order_handler", context=parent_ctx, kind=SpanKind.SERVER) as span:
        span.set_attribute("handler.type", "async")
        span.set_attribute("external.request_id", incoming_headers.get('X-Request-ID', ''))

        # Call aio_publish directly; no manual otel_context passing needed
        # AutoOtelPublisherMixin automatically:
        # 1. Captures OTel context in the current thread
        # 2. Injects it into message's extra.otel_context
        # 3. Passes it to the publish method in the executor thread
        await task_entry.aio_publish(
            msg={
                'order_id': 8888,
                'user_name': 'aio_publish user',
            },
        )
        print("   aio_publish context propagated automatically (no manual steps needed)")

    print("[aio_publish] Async publish demo completed\n")


# Synchronous wrapper for calling from main
def demo_aio_publish_wrapper():
    """Synchronous wrapper for running demo in non-async environment"""
    import asyncio
    asyncio.run(demo_aio_publish_auto_context())


# =============================================================================
# Main entry point
# =============================================================================
if __name__ == '__main__':
    # Initialize OpenTelemetry
    init_opentelemetry()



    # Start all consumers
    task_notify.consume()
    task_process.consume()
    task_entry.consume()

    time.sleep(5)


    print("\n" + "=" * 60)
    print("Funboost OpenTelemetry Distributed Tracing Demo")
    print("=" * 60 + "\n")

    # # Option 1: Publish tasks directly (uses current thread context automatically)
    # print("[Test 1] Publish tasks directly:")
    # task_entry.push(order_id=1, user_name="Zhang San")

    # # Option 2: Publish tasks from a context with a parent Span (same process)
    # print("\n[Test 2] Publish tasks from HTTP request context:")
    # demo_with_manual_parent_span()

    # # Option 3: Cross-machine/cross-service context propagation (simulated external headers)
    # print("\n[Test 3] Cross-service trace context propagation:")
    # demo_cross_service_context_propagation()

    # Option 4: aio_publish cross-thread scenario (manual context propagation)
    print("\n[Test 4] aio_publish cross-thread manual context propagation:")
    demo_aio_publish_wrapper()

    print("\n" + "-" * 60)
    print("Starting task consumption (observe Span info in console output)")
    print("-" * 60 + "\n")
