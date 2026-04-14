"""
1.
```md
🚀 Funboost: The only Python task queue framework with native OpenTelemetry distributed tracing support

✅ Integrate distributed tracing with 1 line of code (BoosterParams → OtelBoosterParams)
✅ Full trace visualization across queues and services
✅ Seamless integration with Jaeger/Zipkin/SkyWalking
✅ Production-grade observability — troubleshoot issues with ease
```

2.
An excellent OpenTelemetry distributed tracing mixin that perfectly integrates with well-known OpenTelemetry
tracing backends such as Jaeger/Zipkin/SkyWalking.

3.
See usage demo at test_frame/test_otel/test_otel_override.py

4. The OTel Mixin implemented in funboost is truly a lifesaver in production. Without it, debugging distributed
infinite loops is basically guesswork. For example, if fa publishes to fb, fb publishes to fc, and fc publishes
back to fa, you get an infinite loop — traditional task ID tracking is not enough to trace where messages originate.

fa -> fb -> fc -> fa -> ...

#### Visual effect in Jaeger / SkyWalking / Funboost TreeExporter:
You will see a **"Staircase to Hell"**:

```text
└── 📤 fa send
    └── 📥 fa process
        └── 📤 fb send
            └── 📥 fb process
                └── 📤 fc send
                    └── 📥 fc process
                        └── 📤 fa send  <-- fa called again
                            └── 📥 fa process

"""



from opentelemetry import trace, context
from opentelemetry.propagate import inject, extract
from opentelemetry.trace import Status, StatusCode, SpanKind
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.serialization import Serialization
from funboost.core.func_params_model import BoosterParams
import copy
import typing

tracer = trace.get_tracer("funboost")


def extract_otel_context_from_funboost_msg(msg: dict):
    """
    Extract OTel context from msg's extra.otel_context field — shared logic for Publisher and Consumer

    :param msg: Message dictionary containing the extra.otel_context field
    :return: OTel Context object

    Usage scenarios:
    - Publisher: extract_otel_context_from_funboost_msg(msg)
    - Consumer: extract_otel_context_from_funboost_msg(kw['body'])
    """
    carrier = msg.get('extra', {}).get('otel_context')
    if carrier:
        # [Explicit]: carrier exists, extract context from it (resolves cross-thread / manual propagation issues)
        return extract(carrier)
    else:
        # [Implicit]: carrier does not exist, use current thread context
        return context.get_current()


class AutoOtelPublisherMixin(AbstractPublisher):
    """
    Smart OTel Publisher:
    1. First checks whether the message already carries an otel_context (user-manually provided)
    2. If not, automatically uses the current thread's context
    3. Generates a Producer Span and injects/overwrites it into the message
    """

    def _get_parent_context(self, msg: dict):
        """Determine the parent context (Parent Context)"""
        return extract_otel_context_from_funboost_msg(msg)

    def _inject_otel_context_to_msg(self, msg: dict):
        """
        Inject the current thread's OTel context into the message's extra.otel_context field.
        Used for aio_publish scenarios: capture the context in the asyncio thread first,
        then pass it through the message to the executor thread.
        """
        if 'extra' not in msg:
            msg['extra'] = {}

        # Only inject if the user has not manually provided otel_context
        if not msg['extra'].get('otel_context'):
            carrier = {}
            inject(carrier)  # Inject the current thread's context into carrier
            msg['extra']['otel_context'] = carrier

    def publish(self, msg, task_id=None, task_options=None):
        msg = copy.deepcopy(msg)  # dict is mutable — do not modify the caller's dict. The user may continue to use it.
        msg, msg_function_kw, extra_params, task_id = self._convert_msg(msg, task_id, task_options)

        # -------------------------------------------------------
        # 2. Determine the parent context (Parent Context)
        # -------------------------------------------------------
        parent_ctx = self._get_parent_context(msg)

        # -------------------------------------------------------
        # 3. Start Producer Span (linked to parent_ctx)
        # -------------------------------------------------------
        span_name = f"{self.queue_name} send"

        with tracer.start_as_current_span(
            span_name,
            context=parent_ctx,  # Key: use the parent context determined above
            kind=SpanKind.PRODUCER
        ) as span:

            span.set_attribute("messaging.system", "funboost")
            span.set_attribute("messaging.destination", self.queue_name)

            # ---------------------------------------------------
            # 4. Inject new Context
            # ---------------------------------------------------
            # Regardless of whether a context existed before, inject the current Producer Span's context here.
            # This ensures the downstream consumer's parent node is this Producer Span, keeping the trace complete:
            # Upstream -> Producer(Send) -> Consumer(Process)

            carrier = {}
            inject(carrier)  # Inject current Span (Producer) into carrier

            if 'extra' not in msg:
                msg['extra'] = {}

            # Overwrite/write the latest trace info
            msg['extra']['otel_context'] = carrier

            # Record Task ID
            span.set_attribute("messaging.message_id", task_id)

            try:
                return super().publish(msg, task_id, task_options)
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR))
                raise e

    async def aio_publish(self, msg, task_id=None, task_options=None):
        """
        OTel distributed tracing publish in asyncio context.

        Key problem: the parent class aio_publish runs publish in a thread pool via run_in_executor,
        but OTel context is thread-local and will be lost across threads.

        Solution:
        1. Capture the OTel context in the current asyncio thread first
        2. Inject it into the message's extra.otel_context field
        3. Then call the parent class's aio_publish (which executes publish in an executor thread)
        4. The publish method detects that otel_context already exists and uses it as the parent context
        """
        msg = copy.deepcopy(msg)  # dict is mutable — do not modify the caller's dict

        # Capture OTel context in the current asyncio thread and inject it into the message.
        # This way, when publish executes in an executor thread, it can recover the correct parent context from the message.
        self._inject_otel_context_to_msg(msg)  # This is the core step

        # Call the parent class's aio_publish, which calls self.publish in an executor.
        # The publish method will detect msg['extra']['otel_context'] and use it.
        return await super().aio_publish(msg, task_id, task_options)


class AutoOtelConsumerMixin(AbstractConsumer):
    """
    Consumer OTEL Mixin: extracts Context from the message and uses it as Parent context.
    Supports both synchronous (_run) and asynchronous (_async_run) consuming functions.
    """

    def _extract_otel_context(self, kw: dict):
        """Extract OTEL context"""
        return extract_otel_context_from_funboost_msg(kw['body'])

    def _set_span_attributes(self, span, kw: dict):
        """Set Span attributes (shared logic)"""
        span.set_attribute("messaging.system", "funboost")
        span.set_attribute("messaging.destination", self.queue_name)
        span.set_attribute("messaging.message_id", kw['body']['extra']['task_id'])
        span.set_attribute("messaging.operation", "process")
        span.set_attribute("funboost.function_params", Serialization.to_json_str(kw['function_only_params'])[:200])

    def _run(self, kw: dict):
        """Distributed tracing for synchronous consuming functions"""
        ctx = self._extract_otel_context(kw)
        span_name = f"{self.queue_name} process"

        with tracer.start_as_current_span(span_name, context=ctx, kind=SpanKind.CONSUMER) as span:
            self._set_span_attributes(span, kw)
            try:
                return super()._run(kw)
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR))
                raise
                # raise e is worse than a bare raise — bare raise preserves the original traceback

    async def _async_run(self, kw: dict):
        """Distributed tracing for asynchronous consuming functions"""
        ctx = self._extract_otel_context(kw)
        span_name = f"{self.queue_name} process"

        with tracer.start_as_current_span(span_name, context=ctx, kind=SpanKind.CONSUMER) as span:
            self._set_span_attributes(span, kw)
            try:
                return await super()._async_run(kw)
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR))
                raise




class OtelBoosterParams(BoosterParams):
    """
    BoosterParams pre-configured with OTEL distributed tracing.
    Using this class avoids the need to manually specify consumer_override_cls and publisher_override_cls each time.
    """
    consumer_override_cls: typing.Type[AutoOtelConsumerMixin] = AutoOtelConsumerMixin
    publisher_override_cls: typing.Type[AutoOtelPublisherMixin] = AutoOtelPublisherMixin