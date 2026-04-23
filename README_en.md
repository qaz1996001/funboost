
[English](README_en.md) | [简体中文](README.md) | [繁體中文](README_zh-TW.md)

# 1. Funboost - Python Distributed Function Scheduling Platform

[![pZf68L6.png](https://s41.ax1x.com/2026/01/30/pZf68L6.png)](https://imgchr.com/i/pZf68L6)

**Funboost** is a Python distributed function scheduling platform. Here are your core learning resources:

| Resource | Link | Description |
| :--- | :--- | :--- |
| **Quick Preview** | [View Demo](https://ydf0509.github.io/funboost_git_pages/funboost_promo.html) | See the framework in action |
| **Full Tutorial** | [ReadTheDocs](https://funboost.readthedocs.io/zh-cn/latest/index.html) | Includes principles, API & advanced usage |
| **AI Tutor** | [AI Learning Guide](https://funboost.readthedocs.io/zh-cn/latest/articles/c14.html) | **[Must Read]** The fastest way to master the framework with AI |
| **Super AI Context Doc** | [funboost_all_docs_and_codes.md](https://github.com/ydf0509/funboost/blob/master/funboost_all_docs_and_codes.md) | ~900K context with Rules, Skills, full tutorial, source code & demos. Feed it directly to AI to help you write code |


## 1.0 Framework Overview

`funboost` is a versatile, powerful, simple, and flexible full-featured `python` distributed scheduling framework. It is a Python distributed function scheduling platform that empowers any function in any project.

**Funboost's core value proposition: Leave the complexity to the framework, leave the simplicity to the user.**

<iframe src="https://ydf0509.github.io/funboost_git_pages/index2.html" width="100%" height="2400" style="border:none;"></iframe>


<h4>Watch funboost video</h4>
<video controls width="800" 
      src="https://ydf0509.github.io/funboost_git_pages/%E8%A7%86%E9%A2%91-Funboost_%E8%A7%86%E9%A2%91.mp4">
   Your browser does not support video playback.
</video>

<h4>Listen to funboost audio</h4>
<audio controls 
      src="https://ydf0509.github.io/funboost_git_pages/%E9%9F%B3%E9%A2%91-funboost_%E9%9F%B3%E9%A2%91.mp4">
   Your browser does not support audio playback.
</audio>

### 1.0.1 Diagrams


#### 1.0.1.1 Funboost Execution Flow

Funboost adopts the classic **Producer -> Broker -> Consumer** architecture, with optional RPC mode (Consumer -> Producer).

Although funboost's feature richness far exceeds specialized frameworks like scrapy, its architecture remains extremely concise and clear at a glance.

![funboost execution flow](img_95.png)

#### 1.0.1.2 Funboost Feature Mind Map

Funboost is extremely simple to use — just one line `@boost` — yet it has every feature you can think of. Its well-designed architecture allows infinite extensibility.

From the mind map: funboost supports 40+ message queues, 30+ task control features, all Python concurrency modes, RPC, micro-batch consumption, CDC event-driven, web management visualization, distributed scheduled tasks, FaaS hot-reload, workflow orchestration, boost_spider crawler, Prometheus metrics monitoring, OpenTelemetry full-chain tracing, and more.

![funboost feature mind map](mermaid-diagram0311e.png)



### 1.0.2 Quick Start: Jump directly to [1.3 Examples](#13--quick-start-your-first-funboost-program)


### 1.0.3 Installation

```shell
pip install funboost --upgrade

# Or install all optional dependencies at once
pip install funboost[all]
```


### 1.0.4 Features & Capabilities

- **Universal Distributed Scheduling**: With a single `@boost` decorator, funboost instantly upgrades ordinary functions into super computing units with distributed execution, FaaS microservices, and CDC event-driven capabilities.
- **All-in-One Support**: Automatically supports **40+** message queues + **30+** task control features + **all** Python concurrency modes.
- **FaaS Capability**: Through `funboost.faas`, you can quickly implement **FaaS (Function as a Service)** with one click, turning functions into auto-discovered microservices.

- **Heavy on Features, Light on Usage**:
   Funboost's features are **comprehensive and heavyweight** — 99% of features you can think of are included. But the usage is **extremely lightweight** — just one line of `@boost` code.

- **Disruptive Design**:
   The magic of funboost is that it simultaneously has a "**lightweight usage**" and a "**heavyweight feature set**", completely overturning the traditional mindset of "powerful = complex".
   
   Just one line of `@boost` code enables distributed execution of any Python function. 99% of funboost users feel: **convenient, fast, powerful, free**.



#### 1.0.4.1 Use Cases

`funboost` is the **universal accelerator for Python functions**. It encompasses everything, unifying programming paradigms, encapsulating the classic **Producer + Message Broker + Consumer** pattern to the extreme.

Whether new or existing projects, Funboost integrates seamlessly:

*   **Need distributed?**
    No problem! Funboost supports **40+** message queue middlewares. Any MQ you can name (even databases and file systems) is supported.

*   **Need FaaS (Function as a Service)?**
    **Highlight!** With `funboost.faas`, you can convert ordinary functions into HTTP microservice endpoints with one click. Auto-discovery, message publishing, result retrieval, task management — instant Serverless experience.

*   **Need concurrency?**
    All Python concurrency modes (**threading, coroutines, multiprocessing**) at your choice, even supporting **stacking** to maximize CPU performance.

*   **Need reliability?**
    Rock solid! **Consumer ACK**, auto-retry, Dead Letter Queue (DLQ), breakpoint resume... Even if the server crashes, tasks are never lost.

*   **Need control?**
    Precise! **QPS rate limiting**, distributed throttling, scheduled tasks, delayed tasks, timeout circuit-breaking, task deduplication... 30+ control weapons at your disposal.

*   **Need monitoring?**
    Crystal clear! Out-of-the-box **funweb (Funboost Web Manager)** gives you full visibility into task status, queue backlog, consumer instances, and more.

*   **Need freedom?**
    Zero intrusion! It doesn't hijack your code or dictate your project structure. **Use it anytime, leave anytime**, pure Python programming experience.


#### 1.0.4.2 What Exactly Is Funboost?

**Funboost's features are extremely rich — you could describe it as "feature overkill" or "all-capable beast".**

> **Funboost has long surpassed the traditional definition of "task queue framework" — it has evolved into a next-generation "Universal Function Computing Platform".**
>
> If Celery is the "tool" for async tasks, then Funboost is the "infrastructure" for function computing. It not only perfectly covers Celery's core capabilities, but breaks technology stack boundaries, with **"function"** as the atomic core, greedily absorbing **FaaS, RPC, microservice architecture, web crawlers, real-time data sync (CDC/ETL), IoT (MQTT), distributed scheduled tasks, deployment, operations; with full support for Event-Driven Architecture (EDA) & full-chain observability (OpenTelemetry)**.

> **Answer**: It's hard to define in one sentence. Funboost is a **universal framework** covering nearly all Python programming business scenarios.

#### 1.0.4.3 Is It Worth Learning?

> **Answer**: **Absolutely**. Choosing a narrow-use, mediocre-performance, restrictive framework is truly a waste of time. Funboost is completely different.

#### 1.0.4.4 Funboost vs Celery: Philosophy Differences

> **Core Metaphor**:
> The relationship between `funboost` and `celery` is like **iPhone** vs **Nokia Symbian**.

**1. Commonality**
Both are essentially distributed message queue-based async task scheduling frameworks, following the classic pattern:
*   `Producer` -> `Broker` -> `Consumer`

**2. Key Differences**

| Dimension | **Celery (Heavy Framework)** | **Funboost (Function Enhancer)** |
| :--- | :--- | :--- |
| **Design Philosophy** | **Framework slavery**: Code must be organized around Celery's architecture and App instance. | **Free empowerment**: Non-intrusive design, giving any function distributed wings. |
| **First-Class Citizen** | `Celery App` instance (Tasks are second-class) | **User functions** (No need to care about App instances) |
| **Core Syntax** | Must define App, use `@app.task` | Directly use **`@boost`** decorator |
| **Ease of Use** | Requires planning specific project structure, high barrier to entry. | Minimal — add decorator to any new or existing function. |
| **Performance** | Traditional performance baseline. | **Orders of magnitude ahead**: Publish performance is **22x** Celery, consume performance is **46x**. |
| **Feature Breadth** | Supports mainstream middlewares. | Supports **40+** middlewares with more fine-grained task control features. |
| **AI-Assisted Coding** | Official docs require manual reading, high learning cost. | **Super AI Context Doc**: `funboost_all_docs_and_codes.md` (~900K context), feed directly to AI for code generation. |


#### 1.0.4.5 Supported Concurrency Modes

`funboost` fully covers Python ecosystem concurrency modes with flexible combinations:

*   **Basic Concurrency Modes**: `threading`, `asyncio`, `gevent`, `eventlet`, and `single_thread` modes.
*   **Stacked Enhancement**: Supports **Multi-Processing** stacked on top of any fine-grained concurrency mode (e.g., multithreading or coroutines) to maximize multi-core CPU utilization.

#### 1.0.4.6 Supported Message Queue Brokers

Thanks to its powerful architecture, in funboost **"anything can be a Broker"**:

*   **Traditional MQ**: RabbitMQ, Kafka, NSQ, RocketMQ, MQTT, NATS, Pulsar, etc.
*   **Database as Broker**:
    *   **NoSQL**: Redis (List, Pub/Sub, Stream, etc.), MongoDB.
    *   **SQL**: MySQL, PostgreSQL, Oracle, SQL Server, SQLite (via SQLAlchemy/Peewee).
*   **Network Protocols**: TCP, UDP, HTTP, gRPC (no MQ deployment needed).
*   **File Systems**: Local files/folders, SQLite (for single-machine or simple scenarios).
*   **Event-Driven (CDC)**: Supports **MySQL CDC** (Binlog change capture), giving Funboost event-driven capabilities far beyond traditional task queues.
*   **Third-Party Framework Integration**: Can directly use Celery, Dramatiq, Huey, RQ, Nameko as underlying Brokers, leveraging Funboost's unified API.


#### 1.0.4.7 Is Funboost Hard to Learn?

**Answer: Extremely easy. Funboost is an "anti-framework" framework.**

*   **Core Simplicity**
    You only need to master **`@boost`** — one decorator and its parameters (`BoosterParams`). Almost all usage follows the pattern in **Section 1.3**.

*   **Zero Code Intrusion**
    *   **No "framework slavery"**: Unlike `Celery`, `Django`, or `Scrapy`, it doesn't force specific directory structures.
    *   **Plug and play**: Funboost has **zero requirements** on your project file structure.

*   **Flexible Dual-Mode Operation**
    After adding `@boost`, your function remains pure:
    *   Call `fun(x, y)`: **Direct execution** (synchronous, no queue involvement).
    *   Call `fun.push(x, y)`: **Send to message queue** (distributed async execution).

*   **AI-Powered Super Context Doc**
    Funboost provides **`funboost_all_docs_and_codes.md`** (~900K context) with complete tutorials, source code, and examples. Feed it directly to AI (DeepSeek, Gemini, etc.) for ultimate AI-assisted coding.

#### 1.0.4.8 Visual Monitoring & Management
Funboost includes a powerful **funweb (Funboost Web Manager)** system.
*   **Full Control**: Comprehensive viewing, monitoring, and management of task consumption.
*   **Out-of-the-Box**: No need to deploy complex monitoring components.

#### 1.0.4.9 Performance: Orders of Magnitude Ahead
Funboost vs Celery performance (controlled variable testing):
*   **Publish Performance**: **22x** Celery.
*   **Consume Performance**: **46x** Celery.

#### 1.0.4.10 User Reputation
**95% of users** say "wish I found it sooner" after initial use:
*   **Ultimate Freedom**: Zero intrusion on user code.
*   **No Refactoring Required**: Unlike other frameworks, Funboost respects your original code structure.
*   **Core Experience**: Simple, powerful, rich.



## 1.1 Core Resources & Documentation

### 1.1.1 Documentation

> **Quick Start Guide**
>
> *   **Note**: The documentation is lengthy, focusing on principles and framework comparisons (`How` & `Why`).
> *   **Shortcut**: **You only need to focus on the [1.3 Section] example!** Other examples only modify `BoosterParams` parameters in the `@boost` decorator.
> *   **Key Point**: `funboost` is extremely easy — just one line of `@boost` code.
> *   **AI Assist**: Strongly recommended to read **[Chapter 14]** on using AI to quickly master `funboost`.

**Online Documentation**: [ReadTheDocs - Funboost Latest](https://funboost.readthedocs.io/zh-cn/latest/index.html)
**Super AI Context Doc**: [funboost_all_docs_and_codes.md](https://github.com/ydf0509/funboost/blob/master/funboost_all_docs_and_codes.md)


#### Documentation Chapter Overview

| Basics & Core Concepts | Advanced Features & Scenarios | AI Assist & Troubleshooting |
| :--- | :--- | :--- |
| [1. Framework Introduction](https://funboost.readthedocs.io/zh-cn/latest/articles/c1.html) | [4b. Code Examples (**Advanced**)](https://funboost.readthedocs.io/zh-cn/latest/articles/c4b.html) | [**14. AI Learning Guide (Must Read)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c14.html) |
| [2. Funboost vs Celery](https://funboost.readthedocs.io/zh-cn/latest/articles/c2.html) | [8. Crawler: Free Coding vs Framework Slavery](https://funboost.readthedocs.io/zh-cn/latest/articles/c8.html) | [6. FAQ](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html) |
| [3. Detailed Framework Introduction](https://funboost.readthedocs.io/zh-cn/latest/articles/c3.html) | [9. Easy Remote Server Deployment](https://funboost.readthedocs.io/zh-cn/latest/articles/c9.html) | [10. Common Errors & Feedback](https://funboost.readthedocs.io/zh-cn/latest/articles/c10.html) |
| [4. **Code Examples (Core)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c4.html) | [11. Third-Party Framework Integration](https://funboost.readthedocs.io/zh-cn/latest/articles/c11.html) | [7. Changelog](https://funboost.readthedocs.io/zh-cn/latest/articles/c7.html) |
| [5. Runtime Screenshots](https://funboost.readthedocs.io/zh-cn/latest/articles/c5.html) | [12. Command Line Console](https://funboost.readthedocs.io/zh-cn/latest/articles/c12.html) | [20. Gemini AI Generated Framework Summary](https://funboost.readthedocs.io/zh-cn/latest/articles/c20.html) |
| | [13. funweb Visual Management](https://funboost.readthedocs.io/zh-cn/latest/articles/c13.html) | |
| | [**15. FaaS Serverless Microservices (Strategic Core)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c15.html) | |

---

### 1.1.2 Source Code & Dependencies

*   **GitHub**: [ydf0509/funboost](https://github.com/ydf0509/funboost)
*   **nb_log Documentation**: [NB-Log Documentation](https://nb-log-doc.readthedocs.io/zh_CN/latest/articles/c9.html#id2)
   
---

## 1.2 Feature Introduction

With `funboost`, developers gain "god-mode" scheduling capabilities:
*   **No More Tedium**: No need to manually write low-level process, thread, or coroutine concurrency code.
*   **Universal Connectivity**: No need to write connection code for `Redis`, `RabbitMQ`, `Kafka`, `Socket`, etc.
*   **All-In-One Control**: Instantly get 30+ enterprise-grade task control features.

**Funboost diagram:**  
![funboost diagram](https://s21.ax1x.com/2024/04/29/pkFFghj.png)


**Same concept in a simpler flow chart:**  
![funboost diagram](https://s21.ax1x.com/2024/04/29/pkFFcNQ.png)

### 1.2.1 Comparison: Funboost Replaces Traditional Thread Pools

Both approaches run function `f` with **10 concurrent workers**. Funboost is more concise and extensible.

#### Method A: Manual Thread Pool (Traditional)
```python
import time
from concurrent.futures import ThreadPoolExecutor

def f(x):
    time.sleep(3)
    print(x)

pool = ThreadPoolExecutor(10)

if __name__ == '__main__':
    for i in range(100):
        pool.submit(f, i)
```

#### Method B: Funboost (Recommended)
```python
import time
from funboost import BoosterParams, BrokerEnum

# One decorator = 10-thread concurrency + message queue capability
@BoosterParams(queue_name="test_insteda_thread_queue", 
               broker_kind=BrokerEnum.MEMORY_QUEUE, 
               concurrent_num=10, 
               is_auto_start_consuming_message=True)
def f(x):
    time.sleep(3)
    print(x)

if __name__ == '__main__':
    for i in range(100):
        f.push(i)
```

### 1.2.2 Task Control Feature Matrix

Funboost encapsulates distributed system complexity in its core, shielding infrastructure differences below and providing standardized scheduling primitives above. Here is a **7-dimension panoramic view**:

#### Dimension 1: Connectivity & Architecture

| Module | Technical Details |
| :--- | :--- |
| **Broker Adapters** | **40+ protocols**: RabbitMQ, Kafka, RocketMQ, Pulsar, NATS, Redis (List/Stream/PubSub), SQL/NoSQL, file systems, TCP/UDP/HTTP. |
| **FaaS Microservices** | **Auto-routing**: Consumer functions auto-register as FastAPI/Flask/Django endpoints; supports **service discovery** & **hot-reload**. |
| **CDC Event-Driven** | **Binlog Listening**: Supports `MYSQL_CDC` for real-time database change triggers, lightweight alternative to Canal/Flink. |
| **Framework Hosting** | **Seamless Compatibility**: Supports Celery, Dramatiq, RQ, Huey as underlying drivers with unified API. |
| **Heterogeneous Communication** | **Multi-Protocol**: gRPC bidirectional communication & MQTT IoT protocol integration. |
| **Super Decorator** | Even without message queues, `@boost` provides extremely rich function control features. |

#### Dimension 2: Concurrency & Throughput

*   **Hybrid Concurrency Model**: Native support for `Threading`, `Gevent`, `Eventlet`, `Asyncio`, `Single_thread`.
*   **Multi-Process Stacking**: `mp_consume(n)` stacks **multi-processing** on top of any concurrency mode, breaking GIL limits.
*   **Micro-Batch Processing**: `MicroBatchConsumerMixin` auto-buffers and aggregates single messages for batch processing (e.g., bulk DB writes).
*   **Zero-Copy Mode**: Memory queue `Ultra-Fast` mode skips serialization overhead for microsecond-level in-process communication.

#### Dimension 3: Reliability

*   **Heartbeat ACK**: Heartbeat-based ACK mechanism detects zombie/crashed processes, reclaims and re-sends unacknowledged tasks within **seconds**.
*   **Exception Retry**: Supports exponential backoff and exception-type-specific retry configuration.
*   **Dead Letter Queue (DLQ)**: After retries are exhausted, messages automatically move to DLQ, preserving data.
*   **Full Persistence**: Supports auto-persisting function parameters, results, duration, and exception stacks to MongoDB/MySQL.
*   **Multi-Dimensional Alerting**: Five built-in alert methods (Alert Mixin, circuit breaker hooks, Prometheus metrics, Mongo polling, ELK logging) with DingTalk, WeChat Work, Feishu, Webhook channels; auto-recovery notifications.

#### Dimension 4: Traffic Governance

*   **Precise QPS Control**: Native QPS rate limiting from 0.00001/s to 50,000/s with **even-interval** execution.
*   **Periodic Quota**: Limit total executions within a period (e.g., "max 100 per minute"), tasks execute on-arrival (non-uniform). See **Section 4b.12**.
*   **Distributed Rate Limiting**: Redis heartbeat-based coordination for **global traffic control** across servers/containers.
*   **Group Consumption**: `consume_group` for resource isolation by business group.
*   **Manual Circuit Breaking**: Runtime dynamic commands to **pause/resume** specific queue consumption.
*   **Auto Circuit Breaking**: `CircuitBreakerConsumerMixin` for auto circuit-break, half-open, and recovery; supports blocking and degradation modes.
*   **Batch Flow Control**: `wait_for_possible_has_finish_all_tasks` for script-level **task drain waiting**.

#### Dimension 5: Scheduling & Orchestration

*   **Workflow Orchestration**: Built-in declarative primitives for **Chain (serial)**, **Group (parallel)**, **Chord (callback)** patterns.
*   **Distributed Scheduling**: Integrated `APScheduler` with Crontab/Interval/Date triggers and distributed locks.
*   **Delayed Tasks**: Native `countdown` (relative) and `eta` (absolute) delay scheduling.
*   **Task Deduplication**: Fingerprint-based deduplication with TTL, immune to URL random parameters.

#### Dimension 6: Observability

*   **Distributed Tracing**: Native **OpenTelemetry** integration with Jaeger/SkyWalking support, auto Context injection for full-chain tracing.
*   **Metrics Monitoring**: Built-in **Prometheus** Exporter (Pull and PushGateway modes) with Grafana dashboards.
*   **Web Console**: Built-in visualization UI for queue backlog, QPS curves, consumer metadata.
*   **Remote Operations**: `RemoteTaskKiller` for terminating specific running tasks; `fabric_deploy` for hot deployment. funweb supports script updates, deployment/process monitoring/log viewing.

#### Dimension 7: Developer Experience

*   **FCT Context**: `from funboost import fct` global object for accessing TaskID, retry count, etc. anywhere in the call chain.
*   **Full Syntax Support**: Complete support for **classmethods**, **instance methods**, **async def** as consumers.
*   **Lifecycle Hooks**: `consumer_override_cls` interface for overriding message cleaning, result callbacks, etc. Supports **non-standard format messages** and **overriding any parent class method**.
*   **Object Transport**: Pickle serialization option for passing custom Python objects as task parameters.
*   **Super Decorator**: Even without distributed/MQ needs, `@boost` with **MEMORY_QUEUE** provides concurrency control, QPS limiting, auto-retry, deduplication, and 10+ features — equivalent to 10 regular decorators combined.



## 1.3 Quick Start: Your First Funboost Program

> **Environment Setup (Important)**
>
> Before running the code, make sure you understand the concept of **`PYTHONPATH`**.
> On Windows cmd or Linux, it's recommended to set `PYTHONPATH` to your project root directory.
> [Learn about PYTHONPATH](https://github.com/ydf0509/pythonpathdemo)

### 1.3.1 Hello World: Simplest Task Scheduling

This example demonstrates how to turn an ordinary sum function into a distributed task.

**Code Logic:**
1.  **Define task**: Use `@boost` decorator, specify queue name `task_queue_name1` and QPS `5`.
2.  **Publish tasks**: Call `task_fun.push(x, y)` to send messages.
3.  **Consume tasks**: Call `task_fun.consume()` to start background processing.

```python
import time
from funboost import boost, BrokerEnum, BoosterParams

# Core config: Use local SQLite as message queue, QPS limit of 5
@boost(BoosterParams(
    queue_name="task_queue_name1", 
    qps=5, 
    broker_kind=BrokerEnum.SQLITE_QUEUE
))
def task_fun(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3)  # Simulates delay; framework auto-handles concurrency

if __name__ == "__main__":
    # 1. Producer: Publish 100 tasks
    for i in range(100):
        task_fun.push(i, y=i * 2)
    
    # 2. Consumer: Start scheduling loop
    task_fun.consume()
```

> **Tips**
> If using `SQLITE_QUEUE` on Linux/Mac and getting `read-only` errors, modify `SQLLITE_QUEUES_PATH` in `funboost_config.py` to a writable directory (see docs 10.3).

**Runtime Screenshots:**

**Publishing tasks:**
![Publish screenshot](https://s21.ax1x.com/2024/04/29/pkFkP4H.png) 

**Consuming tasks:**
![Consume screenshot](https://s21.ax1x.com/2024/04/29/pkFkCUe.png)



### 1.3.2 Advanced: RPC, Scheduled Tasks & Smooth Chaining

A comprehensive example showcasing Funboost's core capabilities:
*   Parameter reuse via `BoosterParams` inheritance.
*   RPC mode: Publisher synchronously gets consumer results.
*   Non-blocking sequential startup of multiple consumers.
*   Scheduled tasks powered by `APScheduler`.

```python
import time
from funboost import boost, BrokerEnum, BoosterParams, ctrl_c_recv, ConcurrentModeEnum, ApsJobAdder

# 1. Define a common config base class
class MyBoosterParams(BoosterParams):
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    max_retry_times: int = 3
    concurrent_mode: str = ConcurrentModeEnum.THREADING 

# 2. Consumer function step1: RPC mode demo
@boost(MyBoosterParams(
    queue_name='s1_queue', 
    qps=1,   
    is_using_rpc_mode=True  # Enable RPC for result retrieval
))
def step1(a: int, b: int):
    print(f'step1: a={a}, b={b}')
    time.sleep(0.7)
    # Publish tasks to step2 from within
    for j in range(10):
        step2.push(c=a+b+j, d=a*b+j, e=a-b+j)
    return a + b

# 3. Consumer function step2: Parameter override demo
@boost(MyBoosterParams(
    queue_name='s2_queue', 
    qps=3, 
    max_retry_times=5  # Override base class default
)) 
def step2(c: int, d: int, e: int=666):
    time.sleep(3)
    print(f'step2: c={c}, d={d}, e={e}')
    return c * d * e

if __name__ == '__main__':
    # --- Start consuming ---
    step1.consume()  # Non-blocking start
    step2.consume()
    step2.multi_process_consume(3)  # Stack 3 additional processes

    # --- RPC call demo ---
    async_result = step1.push(100, b=200)
    print('RPC result:', async_result.result)  # Block until result

    # --- Batch publish demo ---
    for i in range(100):
        step1.push(i, i*2)
        # publish method supports advanced parameters (e.g., task_id)
        step1.publish({'a':i, 'b':i*2}, task_id=f'task_{i}')

    # --- Scheduled task demo (APScheduler) ---
    # Method 1: Execute at specific date
    ApsJobAdder(step2, job_store_kind='redis', is_auto_start=True).add_push_job(
        trigger='date', run_date='2025-06-30 16:25:40', args=(7, 8, 9), id='job1'
    )
    # Method 2: Execute at intervals
    ApsJobAdder(step2, job_store_kind='redis').add_push_job(
        trigger='interval', seconds=30, args=(4, 6, 10), id='job2'
    )

    # Block main thread to keep program running
    ctrl_c_recv()
```

> **Design Philosophy**
> Funboost promotes **"anti-framework"** thinking: You are the protagonist, the framework is just a plugin.
> `task_fun(1, 2)` runs the function directly, `task_fun.push(1, 2)` publishes to the queue.
> You can remove `@boost` anytime — the code remains a pure Python function.

---

### 1.3.3 Simplified Syntax: Omitting `@boost`

For ultimate brevity, you can use `@BoosterParams` directly as a decorator, equivalent to `@boost(BoosterParams(...))`.

```python
# Simplified syntax
@BoosterParams(queue_name="task_queue_simple", qps=5)
def task_fun(a, b):
    return a + b
```

### 1.3.4 Deprecated Syntax: Passing config params directly to `@boost` (Not Recommended)
Passing parameters directly to `@boost` without using `BoosterParams` is the old style and not recommended, as IDE code completion won't work.
```python
# Deprecated: Old syntax, not recommended!
@boost(queue_name="task_queue_simple", qps=5)
def task_fun(a, b):
    return a + b
```


## funweb (Funboost Web Manager) UI Preview

The visual management dashboard provides powerful monitoring and operations capabilities:

Function consumption results: View and search real-time consumption status and results  
[![Function result table](https://s41.ax1x.com/2025/12/19/pZ1L5h4.png)](https://imgchr.com/i/pZ1L5h4)

Queue operations: View and operate queues, including clear, pause, resume, adjust QPS and concurrency  
[![Queue operations 1](https://s41.ax1x.com/2025/12/17/pZlrYPH.png)](https://imgchr.com/i/pZlrYPH)
[![Queue operations 2](https://s41.ax1x.com/2025/12/17/pZlrUxI.png)](https://imgchr.com/i/pZlrUxI)

Queue consumption charts: View consumption curves, various metrics (historical runs, failures, recent 10s completed/failed, avg duration, remaining messages, etc.)  
[![Queue consumption chart](https://s41.ax1x.com/2025/12/19/pZ104HS.png)](https://imgchr.com/i/pZ104HS) 

RPC calls: Publish messages to 30+ message queues via web and get function execution results; query results by task_id  
[![RPC call success](https://s41.ax1x.com/2025/12/19/pZ10RjP.png)](https://imgchr.com/i/pZ10RjP)

Scheduled task management: List view  
[![Scheduled task list](https://s41.ax1x.com/2025/12/17/pZlrNRA.png)](https://imgchr.com/i/pZlrNRA)



## 1.4 Why Python Desperately Needs Distributed Function Computing

Python's characteristics make it more dependent on distributed scheduling frameworks than Java/Go. Two main reasons:

### Pain Point 1: GIL Lock Limitations (Low Multi-Core Utilization)
> **Problem**: Due to the GIL (Global Interpreter Lock), ordinary Python scripts cannot utilize multi-core CPUs. On a 16-core machine, maximum CPU utilization is only **6.25% (1/16)**.
> **Difficulty**: Manually writing `multiprocessing` code is extremely cumbersome, involving complex IPC, task distribution, and state sharing.

**Funboost's Solution**:
*   **Natural Decoupling**: Uses middleware (Redis/RabbitMQ, etc.) to decouple tasks — no need to manually write multi-process task assignment or IPC.
*   **Transparent Multi-Process**: Single-process and multi-process scripts are written identically, **no need** for manual `multiprocessing`, automatically maximizing multi-core performance.

### Pain Point 2: Native Performance Bottleneck (Dynamic Language)
> **Problem**: As a dynamic language, Python's single-thread speed is typically slower than static languages.
> **Need**: Must achieve **horizontal scaling** to compensate.

**Funboost's Solution**:
*   **Seamless Scaling**: Code requires zero modifications to adapt to various environments:
    *   **Multi-Interpreter**: Start multiple Python processes on the same machine.
    *   **Containerized**: Deploy across multiple Docker containers.
    *   **Cross-Machine**: Deploy across multiple physical servers.
*   **Unified Driver**: Funboost as the scheduling core enables Python to run on clusters for higher system throughput.


## 1.5 Best Learning Path

Funboost's design philosophy is **"minimalism"**. No need for lengthy reading — just master the core through practice:

1.  **Experiment-Based Learning**:
    *   Use the **Section 1.3** sum code as your template.
    *   Modify `@boost` decorator parameters (e.g., `qps`, `concurrent_num`).
    *   Add `time.sleep()` to simulate delays.
    *   **Observe**: Watch the console output to experience distributed, concurrent, and rate-limited execution.

2.  **One-Line Code Principle**:
    *   This is the simplest framework: the core is just one line of `@boost` code.
    *   If you can master this decorator, you've mastered the entire framework — much simpler than frameworks requiring multiple class inheritances and config files.

> **AI Tutor**
> Strongly recommended to check **[Chapter 14]** on using AI LLMs to quickly master advanced `funboost` usage.

---

## 1.6 Funboost Absorbs Celery's Power

**Funboost's minimalist moves + Celery's deep power = Unmatched**

Celery has dominated the Python async landscape for over a decade. Its power runs deep, but its complex moves and strict rules (tedious configuration) have deterred countless developers.

Now Funboost wields the **"Absorption Technique"** — with just one move `BrokerEnum.CELERY`, Celery instantly becomes a **subordinate**. From this point on, Celery becomes a **subset** of Funboost, following its commands!

### Dimensional Reduction: Simplifying the Complex

By driving Celery through Funboost, like mastering the "Nine Swords of Dugu" — breaking through all tedious moves, striking at the heart:

| Battle | Celery (Old School Constraints) | Funboost (New Master's Elegance) |
| :--- | :--- | :--- |
| **Startup** (Deploy) | Must memorize lengthy `worker/beat` CLI commands. | Code IS startup — no commands to memorize, just `python xx.py`. |
| **Rules** (Structure) | Forces specific directory structure; misplace a file and it breaks. | Any directory, any file can be the battlefield — zero constraints. |
| **Configuration** (Barrier) | Must manually configure `includes` and `task_routes`; error-prone. | Auto-discovery and registration of tasks — seamless and automatic. |
| **Insight** (Experience) | `@app.task` parameters are opaque; IDE can't help. | `BoosterParams` enables full IDE autocomplete — what you see is what you get. |

> **Code Examples**
> See **[Section 11.1]** for implementation details.

Note: Funboost's performance already far exceeds Celery. Absorbing Celery as a broker is to address concerns about Funboost's scheduling core stability from some users.
> See docs Section 2.6 **funboost vs celery controlled variable performance comparison**, and Section 2.9 **Why is funboost dozens of times faster than celery?**


[View Full Funboost Tutorial](https://funboost.readthedocs.io/)  

![](https://visitor-badge.glitch.me/badge?page_id=distributed_framework)  

<div> </div>
