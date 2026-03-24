# -*- coding: utf-8 -*-
"""
TreeSpanExporter - Display a tree-structured distributed trace in the console

No need to install Jaeger or other middleware; view the tree-structured trace directly in the console.
This is intended for use in test environments by developers — do not use this in production.
In production, strongly recommended to use professional OpenTelemetry backends such as Jaeger/Zipkin/SkyWalking.

See usage demo at test_frame/test_otel/test_otel_tree_view.py
"""

# A perfect tree-structure diagram that clearly shows the message flow process.
# task_entry publishes 2 tasks to otel_tree_task_process, which then publishes 1 task to otel_tree_task_notify
"""
================================================================================
🌳 Distributed Trace Tree Structure
================================================================================

📍 Trace ID: f50f7a80f0b8f88b97788093157c4ae2
------------------------------------------------------------
└── 📤 otel_tree_task_entry send [PRODUCER] ✅ 11.0ms
       🆔 span_id: 0x1c167373656fdc13    parent_id: null
       📋 task_id: 019b4ed4-144d-76b2-86b0-7d4939fc94dc
    └── 📥 otel_tree_task_entry process [CONSUMER] ✅ 323.2ms
           🆔 span_id: 0xbc7fa8b030d5f600    parent_id: 0x1c167373656fdc13
           📋 task_id: 019b4ed4-144d-76b2-86b0-7d4939fc94dc
        ├── 📤 otel_tree_task_process send [PRODUCER] ✅ 2.0ms
        │      🆔 span_id: 0xc1a5e958ffd61344    parent_id: 0xbc7fa8b030d5f600
        │      📋 task_id: 019b4ed4-1a6d-7be3-8516-192449685f6d
        │   └── 📥 otel_tree_task_process process [CONSUMER] ✅ 215.9ms
        │          🆔 span_id: 0x575c4f47a70564b9    parent_id: 0xc1a5e958ffd61344
        │          📋 task_id: 019b4ed4-1a6d-7be3-8516-192449685f6d
        │       └── 📤 otel_tree_task_notify send [PRODUCER] ✅ 2.0ms
        │              🆔 span_id: 0x81e9758e44a4ba61    parent_id: 0x575c4f47a70564b9      
        │              📋 task_id: 019b4ed4-4118-79fd-965c-c080bb0ca775
        │           └── 📥 otel_tree_task_notify process [CONSUMER] ✅ 118.5ms
        │                  🆔 span_id: 0x669734d0fa7eae20    parent_id: 0x81e9758e44a4ba61  
        │                  📋 task_id: 019b4ed4-4118-79fd-965c-c080bb0ca775
        └── 📤 otel_tree_task_process send [PRODUCER] ✅ 2.3ms
               🆔 span_id: 0x986af7dffd837e77    parent_id: 0xbc7fa8b030d5f600
               📋 task_id: 019b4ed4-1a70-7d62-99cd-7e6e0f9038bf
            └── 📥 otel_tree_task_process process [CONSUMER] ✅ 212.6ms
                   🆔 span_id: 0xdb03f7288701f9bd    parent_id: 0x986af7dffd837e77
                   📋 task_id: 019b4ed4-1a70-7d62-99cd-7e6e0f9038bf
                └── 📤 otel_tree_task_notify send [PRODUCER] ✅ 2.0ms
                       🆔 span_id: 0x5ad4e057be91c960    parent_id: 0xdb03f7288701f9bd      
                       📋 task_id: 019b4ed4-4120-7c53-8a5f-4f653d4e486f
                    └── 📥 otel_tree_task_notify process [CONSUMER] ✅ 107.7ms
                           🆔 span_id: 0xff4fd0fdf38fed92    parent_id: 0x5ad4e057be91c960  
                           📋 task_id: 019b4ed4-4120-7c53-8a5f-4f653d4e486f

📍 Trace ID: 6b0053464b0d8649a7ff5a09e34a6813
------------------------------------------------------------
└── 📤 otel_tree_task_entry send [PRODUCER] ✅ 6.5ms
       🆔 span_id: 0xe0d40211831caab2    parent_id: null
       📋 task_id: 019b4ed4-145b-7dcf-8e0b-ff2e334ec309
    └── 📥 otel_tree_task_entry process [CONSUMER] ✅ 321.0ms
           🆔 span_id: 0x607c15d155921877    parent_id: 0xe0d40211831caab2
           📋 task_id: 019b4ed4-145b-7dcf-8e0b-ff2e334ec309
        ├── 📤 otel_tree_task_process send [PRODUCER] ✅ 2.3ms
        │      🆔 span_id: 0xb7e76886ba6b0ab0    parent_id: 0x607c15d155921877
        │      📋 task_id: 019b4ed4-1a6e-7a1d-ad82-5231ec9bc56e
        │   └── 📥 otel_tree_task_process process [CONSUMER] ✅ 214.6ms
        │          🆔 span_id: 0x9a1d938da26d9eb8    parent_id: 0xb7e76886ba6b0ab0
        │          📋 task_id: 019b4ed4-1a6e-7a1d-ad82-5231ec9bc56e
        │       └── 📤 otel_tree_task_notify send [PRODUCER] ✅ 1.8ms
        │              🆔 span_id: 0x6e66697fcee92094    parent_id: 0x9a1d938da26d9eb8      
        │              📋 task_id: 019b4ed4-411d-775c-b592-84396f0857b4
        │           └── 📥 otel_tree_task_notify process [CONSUMER] ✅ 115.8ms
        │                  🆔 span_id: 0xd1d7235f6b247456    parent_id: 0x6e66697fcee92094  
        │                  📋 task_id: 019b4ed4-411d-775c-b592-84396f0857b4
        └── 📤 otel_tree_task_process send [PRODUCER] ✅ 1.5ms
               🆔 span_id: 0xa22a5683b764f63b    parent_id: 0x607c15d155921877
               📋 task_id: 019b4ed4-1a71-741a-ad95-5cf65ce9b8f0
            └── 📥 otel_tree_task_process process [CONSUMER] ✅ 220.8ms
                   🆔 span_id: 0x14963a0749d609b8    parent_id: 0xa22a5683b764f63b
                   📋 task_id: 019b4ed4-1a71-741a-ad95-5cf65ce9b8f0
                └── 📤 otel_tree_task_notify send [PRODUCER] ✅ 5.1ms
                       🆔 span_id: 0x6056d9ba300a795f    parent_id: 0x14963a0749d609b8      
                       📋 task_id: 019b4ed4-41ff-7146-8766-7e2bbe5e97fd
                    └── 📥 otel_tree_task_notify process [CONSUMER] ✅ 106.6ms
                           🆔 span_id: 0x911ac90dd90b901d    parent_id: 0x6056d9ba300a795f  
                           📋 task_id: 019b4ed4-41ff-7146-8766-7e2bbe5e97fd
================================================================================
"""

import atexit
import threading
from collections import defaultdict
from typing import Sequence, Dict, List, Optional

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from nb_log import print_raw


class TreeSpanExporter(SpanExporter):
    """
    Tree-structured Span Exporter

    Collects all Spans and prints the distributed trace in a tree structure
    when the program ends or when print_tree() is called manually.

    Usage:
        tree_exporter = TreeSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(tree_exporter))

        # Prints automatically on program exit, or call manually:
        tree_exporter.print_tree()
    """

    def __init__(self, auto_print_on_exit: bool = False):
        """
        Initialize TreeSpanExporter

        Args:
            auto_print_on_exit: Whether to automatically print the tree on program exit, default False.
                               (funboost consumers run indefinitely, so atexit usually does not trigger.
                                It is recommended to call print_tree() manually after
                                wait_for_possible_has_finish_all_tasks returns.)
        """
        self._spans: Dict[str, List[ReadableSpan]] = defaultdict(list)  # trace_id -> spans
        self._lock = threading.Lock()
        self._shutdown = False

        if auto_print_on_exit:
            atexit.register(self.print_tree)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export Spans (collect into memory)"""
        if self._shutdown:
            return SpanExportResult.SUCCESS

        with self._lock:
            for span in spans:
                trace_id = format(span.context.trace_id, '032x')
                self._spans[trace_id].append(span)

        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        """Shut down the exporter"""
        self._shutdown = True

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush"""
        return True

    def print_tree(self) -> None:
        """Print the tree-structured trace diagram for all collected traces"""
        with self._lock:
            if not self._spans:
                print_raw("\n📭 No distributed tracing data collected\n")
                return

            print_raw("\n" + "=" * 80)
            print_raw("🌳 Distributed Trace Tree Structure")
            print_raw("=" * 80)

            for trace_id, spans in self._spans.items():
                self._print_trace_tree(trace_id, spans)

            print_raw("=" * 80 + "\n")

    def _print_trace_tree(self, trace_id: str, spans: List[ReadableSpan]) -> None:
        """Print the tree structure for a single trace"""
        print_raw(f"\n📍 Trace ID: {trace_id}")
        print_raw("-" * 60)

        # Build span_id -> span mapping
        span_map: Dict[str, ReadableSpan] = {}
        for span in spans:
            span_id = format(span.context.span_id, '016x')
            span_map[span_id] = span

        # Build parent_id -> children mapping
        children_map: Dict[Optional[str], List[str]] = defaultdict(list)
        for span in spans:
            span_id = format(span.context.span_id, '016x')
            parent_id = format(span.parent.span_id, '016x') if span.parent else None
            children_map[parent_id].append(span_id)

        # Find root nodes (those with no parent or whose parent is not in the current trace)
        root_spans = []
        for span in spans:
            span_id = format(span.context.span_id, '016x')
            parent_id = format(span.parent.span_id, '016x') if span.parent else None
            if parent_id is None or parent_id not in span_map:
                root_spans.append(span_id)

        # Sort root nodes by time
        root_spans.sort(key=lambda sid: span_map[sid].start_time)

        # Recursively print tree
        for root_id in root_spans:
            self._print_span_tree(span_map, children_map, root_id, prefix="", is_last=True)

    def _print_span_tree(
        self,
        span_map: Dict[str, ReadableSpan],
        children_map: Dict[Optional[str], List[str]],
        span_id: str,
        prefix: str,
        is_last: bool
    ) -> None:
        """Recursively print the Span tree"""
        span = span_map[span_id]

        # Calculate duration
        duration_ns = span.end_time - span.start_time if span.end_time else 0
        duration_ms = duration_ns / 1_000_000

        # Determine icon
        kind = str(span.kind).split('.')[-1]
        if kind == "PRODUCER":
            icon = "📤"
        elif kind == "CONSUMER":
            icon = "📥"
        else:
            icon = "⚡"

        # Get status
        status = span.status.status_code.name if span.status else "UNSET"
        status_icon = "✅" if status in ("UNSET", "OK") else "❌"

        # Build connector line
        connector = "└── " if is_last else "├── "

        # Print current node
        print_raw(f"{prefix}{connector}{icon} {span.name} [{kind}] {status_icon} {duration_ms:.1f}ms")

        # Print span_id / parent_id (for debugging parent-child relationships in the trace)
        parent_span_id = format(span.parent.span_id, '016x') if span.parent else None
        child_prefix = prefix + ("    " if is_last else "│   ")
        print_raw(
            f"{child_prefix}   🆔 span_id: 0x{span_id}    parent_id: "
            f"{('null' if parent_span_id is None else ('0x' + parent_span_id))}"
        )

        # Print attributes (simplified)
        if span.attributes:
            msg_id = span.attributes.get("messaging.message_id", "")
            if msg_id:
                print_raw(f"{child_prefix}   📋 task_id: {msg_id}")

        # Recursively print child nodes
        children = children_map.get(span_id, [])
        # Sort by time
        children.sort(key=lambda sid: span_map[sid].start_time)

        for i, child_id in enumerate(children):
            child_prefix = prefix + ("    " if is_last else "│   ")
            child_is_last = (i == len(children) - 1)
            self._print_span_tree(span_map, children_map, child_id, child_prefix, child_is_last)

    def clear(self) -> None:
        """Clear all collected Span data"""
        with self._lock:
            self._spans.clear()


# Global singleton for convenient access
_global_tree_exporter: Optional[TreeSpanExporter] = None


def get_tree_exporter(auto_print_on_exit: bool = False) -> TreeSpanExporter:
    """Get the global TreeSpanExporter singleton"""
    global _global_tree_exporter
    if _global_tree_exporter is None:
        _global_tree_exporter = TreeSpanExporter(auto_print_on_exit=auto_print_on_exit)
    return _global_tree_exporter


def print_trace_tree() -> None:
    """Print the trace tree collected in the global TreeSpanExporter"""
    if _global_tree_exporter:
        _global_tree_exporter.print_tree()
    else:
        print_raw("⚠️ TreeSpanExporter has not been initialized yet")

