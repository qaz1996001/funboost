# Funboost Task Chain Tracing Implementation Plan

## I. Is This a Common Requirement?

**Very common**, especially in following scenarios:

1. **Microservices Architecture**: One request may trigger multiple queue tasks, need to trace complete call chain
2. **RPC Chain Calls**: Function A calls B, B calls C, need to know complete path
3. **Problem Diagnosis**: When task fails, need to know who triggered it, who was affected
4. **Performance Analysis**: Analyze entire call chain latency bottlenecks

Mature industry solutions like **Jaeger**, **Zipkin**, **SkyWalking**, **Alibaba Eagle Eye** all do this.

---

## II. Implementation Plan

### Plan Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Chain Tracing Architecture                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Task A (root)                                             │
│   trace_id: abc123                                          │
│   task_id: task_001                                         │
│   parent_task_id: null                                      │
│        │                                                    │
│        ├──────────────┬──────────────┐                      │
│        ▼              ▼              ▼                      │
│   Task B          Task C          Task D                    │
│   trace_id: abc123  trace_id: abc123  trace_id: abc123      │
│   task_id: task_002  task_id: task_003  task_id: task_004   │
│   parent: task_001   parent: task_001   parent: task_001    │
│        │                                                    │
│        ▼                                                    │
│   Task E                                                    │
│   trace_id: abc123                                          │
│   task_id: task_005                                         │
│   parent: task_002                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Core Concepts

| Field | Notes |
|------|------|
| `trace_id` | Unique identifier for entire call chain, passed from root task to endpoint |
| `task_id` | Current task's unique identifier (funboost already has) |
| `parent_task_id` | Parent task's task_id, for building call tree |
| `span_id` | Optional, finer-grained tracing (e.g., multiple calls within function) |
| `depth` | Call depth, limit chain level to prevent infinite recursion |

---

## III. Implementation Steps

### Step 1: Data Model Extension

Extend fields in message body and result persistence:

```python
# Message body extension
{
    "task_id": "task_001",
    "trace_id": "trace_abc123",      # New: Chain tracing ID
    "parent_task_id": "task_000",    # New: Parent task ID
    "depth": 2,                       # New: Call depth
    # ... original fields
}
```

### Step 2: Context Passing Mechanism

```python
# Approach: Use contextvars to pass tracing context during function execution
import contextvars

# Current task's tracing context
_trace_context = contextvars.ContextVar('trace_context', default=None)

class TraceContext:
    trace_id: str
    task_id: str
    depth: int
```

When consumer executes function:
1. Extract `trace_id`, `parent_task_id` from message
2. Set to `contextvars`
3. If function internally calls other funboost queue, automatically inject tracing info

### Step 3: Automatic Injection Mechanism

Modify `publisher.publish()` method:

```python
def publish(self, msg_body, task_id=None, ...):
    # Get current tracing context
    ctx = _trace_context.get()
    
    if ctx:
        # Sub-task inherits parent task's trace_id
        trace_id = ctx.trace_id
        parent_task_id = ctx.task_id
        depth = ctx.depth + 1
    else:
        # Root task, generate new trace_id
        trace_id = generate_trace_id()
        parent_task_id = None
        depth = 0
    
    # Inject into message body
    full_msg = {
        **msg_body,
        '_trace_id': trace_id,
        '_parent_task_id': parent_task_id,
        '_depth': depth,
    }
```

### Step 4: Storage Extension

Add indexes to MongoDB result table:

```python
# Index design
db.collection.create_index([('trace_id', 1)])
db.collection.create_index([('parent_task_id', 1)])
db.collection.create_index([('trace_id', 1), ('depth', 1)])
```

### Step 5: Web Page Implementation

#### 1. Chain Tracing Query Page

```
┌─────────────────────────────────────────────────────────┐
│  🔍 Chain Tracing Query                                 │
├─────────────────────────────────────────────────────────┤
│  Trace ID: [_______________]  or  Task ID: [__________] │
│                                        [🔍 Query]        │
└─────────────────────────────────────────────────────────┘
```

#### 2. Call Chain Visualization (Tree Structure)

```
📍 trace_id: abc123  Total Time: 2.5s  Task Count: 5

├─ ✅ my_consuming_function [task_001]
│     └─ Time: 0.3s | Queue: queue_a | Start: 14:30:01
│
├─── ✅ process_data [task_002]
│       └─ Time: 1.2s | Queue: queue_b | Start: 14:30:02
│
│     ├─── ✅ save_to_db [task_005]
│     │       └─ Time: 0.5s | Queue: queue_c | Start: 14:30:03
│
├─── ✅ send_notification [task_003]
│       └─ Time: 0.2s | Queue: queue_d | Start: 14:30:02
│
└─── ❌ update_cache [task_004]
        └─ Time: 0.8s | Queue: queue_e | Failed: Redis connection timeout
```

#### 3. Timeline View (Gantt Chart)

```
Timeline ─────────────────────────────────────────────►
        0s        1s        2s        3s
        │         │         │         │
task_001 ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
task_002 ░░░░██████████████░░░░░░░░░░░░░░░
task_005 ░░░░░░░░░░░░░░████████░░░░░░░░░░░
task_003 ░░░░██░░░░░░░░░░░░░░░░░░░░░░░░░░░
task_004 ░░░░████████░░░░░░░░░░░░░░░░░░░░░ ❌
```

---

## IV. Query API Design

```python
# 1. Get complete call chain by trace_id
GET /funboost/trace/{trace_id}
# Returns: All tasks in trace, sorted by depth and time

# 2. Get belonging call chain by task_id
GET /funboost/trace/by_task/{task_id}
# Returns: First find trace_id, then return complete call chain

# 3. Get sub-tasks of task
GET /funboost/task/{task_id}/children
# Returns: All tasks with parent_task_id = task_id
```

---

## V. Implementation Difficulty Assessment

| Module | Difficulty | Effort | Notes |
|------|------|--------|------|
| Data Model Extension | ⭐ | 1 day | Add fields, compatible with old data |
| Context Passing | ⭐⭐ | 2 days | contextvars + consumer modification |
| Publisher Auto-Inject | ⭐⭐ | 1 day | Modify publish method |
| MongoDB Storage | ⭐ | 0.5 day | Index optimization |
| Web Query Page | ⭐⭐ | 2 days | Basic table display |
| Visualization Call Graph | ⭐⭐⭐ | 3 days | Needs frontend graphics library (D3.js/AntV) |

**Total approximately 1-2 weeks**

---

## VI. Recommended Implementation Order

### Phase 1 (MVP)
- Add `trace_id`, `parent_task_id` fields
- Manual passing (user can optionally pass in publish)
- Web page supports query by trace_id

### Phase 2 (Auto-Inject)
- Use `contextvars` for automatic context passing
- Sub-tasks auto-inherit parent task's trace_id

### Phase 3 (Visualization)
- Call chain tree display
- Timeline Gantt chart
- Performance analysis (bottleneck identification)

---

## VII. Relation to Existing Code

### Existing current_task Module

Funboost already has `funboost/core/current_task.py` providing ability to get current task information during function execution:

```python
from funboost import current_task

# Can get inside decorated function
task_id = current_task.task_id
queue_name = current_task.queue_name
```

Chain tracing can extend this module to add:
- `current_task.trace_id`
- `current_task.parent_task_id`
- `current_task.depth`

### Existing Result Persistence

`funboost/core/function_result_status_saver.py` already implements task status and result MongoDB persistence.

Chain tracing needs to add `trace_id` and `parent_task_id` fields when saving.
