
[English](README_en.md) | [简体中文](README.md) | [繁體中文](README_zh-TW.md)

# 1. Introduction to Funboost, the Python Distributed Function Scheduling Platform

[![pZf68L6.png](https://s41.ax1x.com/2026/01/30/pZf68L6.png)](https://imgchr.com/i/pZf68L6)

**Funboost** is a Python distributed function scheduling platform. Here is a guide to the core learning resources:

| Resource | Link | Description |
| :--- | :--- | :--- |
| ⚡ **Quick Preview** | [👉 View the demo](https://ydf0509.github.io/funboost_git_pages/funboost_promo.html) | See the framework in action at a glance |
| 📖 **Full Tutorial** | [👉 ReadTheDocs](https://funboost.readthedocs.io/zh-cn/latest/index.html) | Principles, API and advanced usage |
| 🤖 **AI Tutor** | [👉 AI Learning Guide](https://funboost.readthedocs.io/zh-cn/latest/articles/c14.html) | **[Must read]** The fastest way to master the framework with AI |
| 📄 **Super AI Context Document** | [👉 funboost_all_docs_and_codes.md](https://github.com/ydf0509/funboost/blob/master/funboost_all_docs_and_codes.md) | About 900K of context, including Rules, Skills, the full tutorial, source code and demos. Feed it straight to an AI and let it write code for you |


## 1.0 About the funboost Framework

`funboost` is a universal, powerful, simple and unrestrictive full-featured distributed scheduling framework for `python`. It is a Python distributed function scheduling platform whose purpose is to empower any function in any of your projects.

**Funboost's core value proposition: leave the complexity to the framework, and the simplicity to the user.**

<iframe src="https://ydf0509.github.io/funboost_git_pages/index2.html" width="100%" height="2400" style="border:none;"></iframe>


<h4>📹 Watch the funboost video</h4>
<video controls width="800" 
      src="https://ydf0509.github.io/funboost_git_pages/%E8%A7%86%E9%A2%91-Funboost_%E8%A7%86%E9%A2%91.mp4">
   Your browser does not support video playback.
</video>

<h4>🎧 Listen to the funboost audio</h4>
<audio controls 
      src="https://ydf0509.github.io/funboost_git_pages/%E9%9F%B3%E9%A2%91-funboost_%E9%9F%B3%E9%A2%91.mp4">
   Your browser does not support audio playback.
</audio>

### 1.0.1 funboost Diagrams


#### 1.0.1.1 funboost Execution Flow

funboost uses the classic **Producer → Broker → Consumer** architecture, with an optional RPC mode (Consumer → Producer).

Although funboost is far richer in features than specialized frameworks such as scrapy, its architecture stays extremely simple, and the core flow is clear at a glance.

![funboost execution flow](img_95.png)

#### 1.0.1.2 funboost Feature Mind Map

funboost is extremely easy to use: just one line of @boost, yet it has every feature you can think of. A sound software architecture lets the funboost framework extend in unlimited directions.

As the mind map shows, funboost supports 40+ message queues, 30+ task control features, all Python concurrency modes, RPC, micro-batch consumption, CDC event driving, a visual management console, distributed scheduled tasks, FaaS hot reloading, workflow orchestration, the boost_spider crawler, Prometheus metrics, OpenTelemetry end-to-end task tracing and more. It covers half of all Python programming scenarios.

The mind map image is high resolution; we recommend downloading it and viewing it with a local image viewer.
<!-- ![funboost feature mind map](img_94.png) -->
![funboost feature mind map](mermaid-diagram0311e.png)



### 1.0.2 To get to know and start using funboost quickly, go straight to [the 1.3 example](#13--quick-start-your-first-funboost-program)


### 1.0.3 Installing funboost

```shell
pip install funboost --upgrade  

or pip install funboost[all]  # install all niche third-party middleware dependencies at once  
```  


### 1.0.4 What funboost Does

- **Universal distributed scheduling**: with a single @boost decorator, `funboost` instantly upgrades an ordinary function into a super computing unit capable of distributed execution, FaaS microservices and CDC event driving. It connects everything and schedules everything.
- **All-round support**: automatically supports **40+** message queues + **30+** task control features + **all** concurrency modes in `python`.
- **FaaS capability**: with `funboost.faas`, you can implement **FaaS (Function as a Service)** in one step, turning functions into auto-discovered microservices instantly.

- **Heavy on features, light in use**:
   `funboost`'s feature set is **comprehensive and heavyweight**: 99% of the features you can think of are there. Yet its usage is **extremely lightweight**: the only code you need to write is one line of `@boost`.

- **Disruptive design**:
   The magic of `funboost` is that it has both a "**lightweight way of use**" and a "**heavyweight feature set**", completely overturning the traditional belief that "powerful = complicated". It is a clever leap beyond traditional Python framework design.
   
   A single line of `@boost` is all it takes to execute any `python` function in a distributed way. The core impression of 99% of `pythoner`s who have used `funboost` is: **convenient, fast, powerful and free**.  



#### 1.0.4.1 Where Funboost Fits

`funboost` is a **universal accelerator for Python functions**. It is all-encompassing, unifies the programming mindset, and encapsulates the classic **Producer + Message Broker + Consumer** pattern to the extreme.

Whether in new or legacy projects, Funboost blends in seamlessly and gives you these core capabilities:

*   🌐 **Need distribution?**
    No problem! Funboost supports **40+** message queue brokers. Any MQ you can name (even databases and file systems) is supported.

*   ⚡ **Need FaaS (Function as a Service)?**
    **This is a highlight!** With `funboost.faas`, you can turn an ordinary function into an HTTP microservice endpoint in one step. Functions are discovered automatically; publishing messages, fetching results and managing tasks give you a Serverless-like experience instantly.

*   🚀 **Need concurrency?**
    You got it! Every Python concurrency mode (**threads, coroutines, multiprocessing**) is available, and they can even be **stacked** to squeeze every bit of CPU performance.

*   🛡️ **Need reliability?**
    Rock solid! **Consumer acknowledgement (ACK)**, automatic retries, dead letter queues (DLQ), resumable crawling... Tasks are never lost, even if a server goes down.

*   🎛️ **Need control?**
    Total command! **Precise QPS rate control**, distributed rate limiting, scheduled tasks, delayed tasks, timeout circuit breaking, task filtering... over thirty control weapons at your disposal.

*   📊 **Need monitoring?**
    Everything at a glance! The out-of-the-box **funweb (Funboost Web Manager)** keeps you fully informed about task status, queue backlog, consumer instances and more.

*   🦅 **Need freedom?**
    Zero intrusion! It does not hijack your code or dictate your project structure. **Use it any time, drop it any time**, and keep the purest Python programming experience.


#### 1.0.4.2 🤔 The Big Question: What Exactly Is Funboost?

**Funboost is so feature-rich that it could fairly be called "feature overkill" or an "all-round monster".**

> **Funboost has long outgrown the traditional definition of a "task queue framework" and has evolved into a new-generation "Universal Function Computing Platform".**
>
> If Celery is a "tool" for asynchronous tasks, Funboost is "infrastructure" for function computing. It not only fully covers Celery's core capabilities, but also breaks through technology stack boundaries. With the **"function"** as its atomic core, it greedily absorbs and fuses **FaaS, RPC, microservice architecture, web crawling, real-time data sync (CDC/ETL), IoT (MQTT), distributed scheduled tasks, deployment and operations; and fully supports event-driven architecture (EDA) and end-to-end observability (OpenTelemetry)**.
>
> In the world of Funboost, the goal is no longer to benchmark against Celery, but to redefine the productivity limits of Python functions.

> **Answer**: It is hard to define in one sentence. Funboost is a **universal framework** that covers nearly every Python programming scenario. The answer is open-ended, with unlimited possibilities.

👉 **[See the open-ended answer (docs section 6.0b)](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html#b-funboost)**

#### 1.0.4.3 💖 The Key Concern: Is It Worth My Time to Learn?

> **Answer**: **Absolutely**. Choosing a framework that is narrow in purpose, mediocre in performance and restrictive in style really is a waste of your life. Funboost is completely different.

👉 **[See the detailed evaluation (docs section 6.0)](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html#funboost)**


#### 1.0.4.4 The Philosophical Difference Between Funboost and Celery

> **Core analogy**:
> The relationship between `funboost` and `celery` is like that between the **iPhone** and **Nokia Symbian**.
> Both are fundamentally about communication (task scheduling), but overlapping functionality does not make it reinventing the wheel. Just as the iPhone redefined the phone, **Funboost is redefining distributed task scheduling and making "framework enslavement" a thing of the past.**

**1. What they have in common**
Both are essentially asynchronous task scheduling frameworks built on distributed message queues, following the classic programming model:
*   `Producer` -> `Broker` -> `Consumer`

**2. Key differences**

| Dimension | **Celery (heavyweight framework)** | **Funboost (function enhancer)** |
| :--- | :--- | :--- |
| **Design philosophy** | **Framework enslavement**: code must be organized around Celery's architecture and App instance. | **Free empowerment**: non-intrusive design that gives distributed wings to any function. |
| **First-class citizen** | The `Celery App` instance (Tasks are second-class citizens) | **User functions** (no need to care about an App instance) |
| **Core syntax** | Define an App and use `@app.task` | Use the **`@boost`** decorator directly |
| **Ease of use** | Requires a specific project structure; steeper learning curve. | Minimal: add the decorator to any new or old function anywhere. |
| **Performance** | Traditional baseline. | **Leaps ahead**: publishing is **22x** faster than Celery, consuming **46x** faster. |
| **Feature breadth** | Supports mainstream brokers. | Supports **40+** brokers, with many more fine-grained task controls. |
| **AI-assisted programming** | Official docs must be read manually; high learning cost. | **Super AI context document**: `funboost_all_docs_and_codes.md`<br>(about 900K of context). Feed it to an AI to write code and answer questions, no painful doc reading needed. |


#### 1.0.4.5 Concurrency Modes Supported by Funboost

`funboost` covers every concurrency approach in the Python ecosystem and supports flexible combinations:

*   **Basic concurrency modes**: `threading` (multithreading), `asyncio` (async IO), `gevent` (coroutines), `eventlet` (coroutines) and `single thread` mode.
*   **Stacked enhancement mode**: **multiprocessing** can be stacked on top of any of the finer-grained modes above (such as multithreading or coroutines) to make the most of multi-core CPUs.

#### 1.0.4.6 Message Queue Brokers Supported by Funboost

Thanks to its powerful architecture, in `funboost` **"anything can be a Broker"**. It covers not only traditional MQs, but also databases, network protocols and third-party frameworks.

*   **Traditional message queues**: RabbitMQ, Kafka, NSQ, RocketMQ, MQTT, NATS, Pulsar, etc.
*   **Databases as brokers**:
    *   **NoSQL**: Redis (List, Pub/Sub, Stream and other modes), MongoDB.
    *   **SQL**: MySQL, PostgreSQL, Oracle, SQL Server, SQLite (via SQLAlchemy/Peewee).
*   **Direct network protocols**: TCP, UDP, HTTP, gRPC (queue communication without deploying an MQ service).
*   **File system**: local files/folders, SQLite (good for single-machine or simple scenarios).
*   **Event driven (CDC)**: supports **MySQL CDC** (binlog-based change capture), giving Funboost event-driven capability with a design philosophy far beyond traditional task queues.
*   **Third-party framework integration**: frameworks such as Celery, Dramatiq, Huey, RQ and Nameko can be used directly as underlying brokers, scheduled through Funboost's unified interface.





#### 1.0.4.7 **Is funboost hard to learn?**   


**The answer: it is extremely easy to pick up. Funboost is an "anti-framework" framework.**

*   🎯 **Minimal core**
    The whole framework only requires mastering the **`@boost`** decorator and its parameters (`BoosterParams`). Almost every usage follows the pattern of the example in **section 1.3**: learn one, and you know them all.

*   🛡️ **Zero code intrusion**
    *   **No "framework enslavement"**: unlike `Celery`, `Django` or `Scrapy`, it does not force you to organize your code in a specific directory structure (which often means a major rewrite once you stop using them).
    *   **Plug and play**: Funboost has **zero requirements** on your project file structure; you can bring it into any new or legacy project at any time.

*   🔄 **Freedom to come and go (dual-mode execution)**
    Even after adopting Funboost, you don't need to worry about your code being locked in. With the `@boost` decorator added, your function remains pure:
    *   Calling `fun(x, y)`: **runs the function directly** (synchronously, without going through a queue; with the decorator it behaves exactly as without it).
    *   Calling `fun.push(x, y)`: **sends it to the message queue** (distributed asynchronous execution).

*   🤖 **A super AI context document built for AI programming**
    Funboost provides **`funboost_all_docs_and_codes.md`** (about 900K of context), containing the full tutorial, source code and examples. You can feed it directly to an AI (such as DeepSeek, Gemini or other million-token-context models) to quickly generate Funboost code, answer questions or build custom extensions, for the ultimate AI-assisted programming experience.

👉 *For a detailed, in-depth answer to "Is Funboost hard to learn and use?", see docs section **`6.0.c`**.*


#### 1.0.4.8 📊 Visual Monitoring and Management
Funboost has a powerful built-in **funweb (Funboost Web Manager)** management system.
*   **Full control**: view, monitor and manage task consumption comprehensively.
*   **Out of the box**: track core metrics such as queue backlog and consumer status without deploying complex monitoring components.

#### 1.0.4.9 🚀 Performance: Leaps Ahead
Compared with Celery, Funboost has an **order-of-magnitude** advantage (based on controlled-variable testing):
*   **Publishing performance**: **22x** that of Celery.
*   **Consuming performance**: **46x** that of Celery.
> *Note: for the detailed controlled-variable benchmark report, see docs **section 2.6**.*

#### 1.0.4.10 ⭐ User Reputation and Feedback
**95% of users** say after first using it that they "wish they had found it sooner". Key feedback:
*   **Ultimate freedom**: Funboost has **zero intrusion** on how users think about and write their code.
*   **No forced refactoring**: unlike other frameworks that require users to restructure code around framework logic, Funboost respects your native code structure.
*   **Core experience**: simple, powerful, rich.






## 1.1 📚 Core Resources and Documentation

### 1.1.1 📝 Project Documentation

> **🚀 Quick Start Guide**
>
> *   **About the docs**: the docs are long, mainly covering principles and framework comparisons (`How` & `Why`).
> *   **Shortcut**: **you only need to study the single example in [section 1.3]!** The other examples merely change the `BoosterParams` arguments of the `@boost` decorator.
> *   **Key point**: `funboost` is extremely easy to use; you only need to master one line of `@boost`.
> *   **🤖 AI assistance**: we strongly recommend reading **[Chapter 14]** to learn how to master `funboost` quickly with large AI models.

**🔗 Online docs**: [ReadTheDocs - Funboost Latest](https://funboost.readthedocs.io/zh-cn/latest/index.html)
**Super AI context document**: [funboost_all_docs_and_codes.md](https://github.com/ydf0509/funboost/blob/master/funboost_all_docs_and_codes.md)


#### 📖 Chapter Overview

| 🔰 Basics & Core Concepts | 🚀 Advanced Features & Practice | 🤖 AI Assistance & Troubleshooting |
| :--- | :--- | :--- |
| [1. Introduction to funboost](https://funboost.readthedocs.io/zh-cn/latest/articles/c1.html) | [4b. Code examples (**advanced**)](https://funboost.readthedocs.io/zh-cn/latest/articles/c4b.html) | [**14. AI-assisted learning guide (must read)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c14.html) |
| [2. funboost vs Celery](https://funboost.readthedocs.io/zh-cn/latest/articles/c2.html) | [8. Crawler in practice: free programming vs framework enslavement](https://funboost.readthedocs.io/zh-cn/latest/articles/c8.html) | [6. FAQ](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html) |
| [3. Framework in detail](https://funboost.readthedocs.io/zh-cn/latest/articles/c3.html) | [9. Easy remote server deployment](https://funboost.readthedocs.io/zh-cn/latest/articles/c9.html) | [10. Common errors and issue reporting](https://funboost.readthedocs.io/zh-cn/latest/articles/c10.html) |
| [4. **Code examples (core)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c4.html) | [11. Integrating third-party frameworks (Celery/Kombu, etc.)](https://funboost.readthedocs.io/zh-cn/latest/articles/c11.html) | [7. Changelog](https://funboost.readthedocs.io/zh-cn/latest/articles/c7.html) |
| [5. Runtime screenshots](https://funboost.readthedocs.io/zh-cn/latest/articles/c5.html) | [12. Command-line console support](https://funboost.readthedocs.io/zh-cn/latest/articles/c12.html) | [20. Framework core ideas generated by Gemini AI](https://funboost.readthedocs.io/zh-cn/latest/articles/c20.html) |
| | [13. funweb visual management](https://funboost.readthedocs.io/zh-cn/latest/articles/c13.html) | |
| | [⚡ **15. FaaS Serverless microservices (strategic core)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c15.html) | |

---

### 1.1.2 📦 Source Code and Dependencies

*   **GitHub project page**: [ydf0509/funboost](https://github.com/ydf0509/funboost)
*   **nb_log logging docs**: [NB-Log Documentation](https://nb-log-doc.readthedocs.io/zh_CN/latest/articles/c9.html#id2)
   
---

## 1.2 Framework Features  

With `funboost`, developers gain "god's-eye view" scheduling power:
*   🚫 **No more tedium**: no need to hand-write low-level process, thread or coroutine concurrency code.
*   🔌 **Universal connectivity**: no need to write connection code for `Redis`, `RabbitMQ`, `Kafka`, `Socket` or other brokers yourself.
*   🧰 **Full control**: 30+ enterprise-grade task control features out of the box.

**funboost diagram:**  
![funboost diagram](https://s21.ax1x.com/2024/04/29/pkFFghj.png)


**The same idea as a very ordinary flowchart:**  
![funboost diagram](https://s21.ax1x.com/2024/04/29/pkFFcNQ.png)

### 1.2.1 🆚 Comparison: Funboost Replacing a Traditional Thread Pool

Both approaches below run function `f` with **10-way concurrency**. Funboost is more concise and more extensible.

#### ❌ Approach A: manually creating a thread pool (traditional)
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

#### ✅ Approach B: Funboost (recommended)
```python
import time
from funboost import BoosterParams, BrokerEnum

# Just one decorator line gives you 10-thread concurrency + message queue capability
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

### 1.2.2 🚀 Task Control Feature Matrix

Funboost encapsulates the complexity of distributed systems in its kernel, hiding infrastructure differences below and providing standardized scheduling primitives above. Here is a **7-dimension panoramic view** of the framework's core capabilities:

#### 🌌 Dimension 1: Connectivity & Architecture

| Capability | Technical Details |
| :--- | :--- |
| **Broker adaptation** | **40+ protocols**: RabbitMQ, Kafka, RocketMQ, Pulsar, NATS, Redis (List/Stream/PubSub), SQL/NoSQL, file system, TCP/UDP/HTTP. |
| **FaaS microservices** | **Automatic routing**: with `funboost.faas`, consumer functions are automatically registered as FastAPI/Flask/Django endpoints; supports **service discovery** and **hot reloading**. |
| **CDC event driving** | **Binlog listening**: supports `MYSQL_CDC`, triggering functions in real time on database changes, a lightweight alternative to Canal/Flink. |
| **Framework hosting** | **Seamless compatibility**: can take over Celery, Dramatiq, RQ, Huey and others as the underlying engine behind a unified API. |
| **Heterogeneous communication** | **Multi-protocol**: supports bidirectional gRPC communication and MQTT IoT protocol integration. |
| **Super decorator** | **Use funboost as a super decorator**: even if you don't use a message queue, funboost is still recommended, because @boost offers an extremely rich set of function controls |

#### ⚡ Dimension 2: Concurrency & Throughput

*   **Hybrid concurrency model**: natively supports five modes: `Threading`, `Gevent`, `Eventlet`, `Asyncio` (native event loop) and `Single_thread`.
*   **Multiprocessing stacking**: `mp_consume(n)` stacks **multiple processes** on top of the above modes, bypassing the GIL and fully using multi-core CPUs.
*   **Micro-batch**: `MicroBatchConsumerMixin` automatically buffers and aggregates individual messages for batch processing (e.g. bulk DB writes), significantly improving I/O throughput.
*   **Zero-copy mode**: the memory queue supports an `Ultra-Fast` mode that skips serialization for microsecond-level in-process communication.

#### 🛡️ Dimension 3: Reliability

*   **Heartbeat-level ACK**: an ACK mechanism based on consumer heartbeat detection. It detects hung or crashed processes and reclaims and redelivers unacknowledged tasks **within seconds**, without misjudging long-running tasks.
*   **Exception retries**: exponential backoff, with retry configuration for specific exception types.
*   **Dead letter queue (DLQ)**: after retries are exhausted or specific exceptions are caught, messages are automatically moved to the dead letter queue so no data is lost.
*   **Full persistence**: function arguments, results, execution time and exception stack traces can be persisted automatically to MongoDB/MySQL for traceability.
*   **Multi-dimensional monitoring & alerting**: **five built-in alerting approaches** (built-in alert Mixin, circuit breaker hooks, Prometheus metrics, Mongo polling, ELK logs). Alert rules can be based on consecutive failure counts or sliding-window error rates, with channels such as DingTalk, WeCom, Feishu and Webhook; a recovery notification is sent automatically when tasks recover, closing the loop from failure detection to resolution. (See docs section **6.30 How funboost configures failure alerts and recovery alerts** for details.)


#### 🕹️ Dimension 4: Traffic Governance

*   **Precise rate control (QPS)**: natively supports **QPS rate limiting** from extremely low (0.00001/sec) to high (50000/sec) frequencies, executing tasks at **evenly spaced intervals**.
*   **Periodic quota**: limits the **total number** of executions within a period (e.g. 1 minute); tasks **run as they arrive** (not evenly spaced). For example, with "at most 100 per minute", once the 100 quota is used up, execution waits for the next period. See **section 4b.12** for usage.
*   **Distributed rate limiting**: **global traffic control** across servers and containers, coordinated through funboost's Redis heartbeat information.
*   **Group consumption**: `consume_group` starts consumers by business group, enabling resource isolation in large monolithic applications.
*   **Manual circuit breaking**: issue commands at runtime to **pause/resume** consumption of a given queue in real time.
*   **Automatic circuit breaking**: the CircuitBreakerConsumerMixin extension supports automatic tripping, half-open and recovery, in blocking mode or degraded mode.
*   **Batch flow control**: `wait_for_possible_has_finish_all_tasks` provides script-level **waiting until all tasks are drained**.

#### 🎼 Dimension 5: Scheduling & Orchestration

*   **Workflow orchestration**: built-in declarative orchestration primitives supporting **Chain (serial)**, **Group (parallel)** and **Chord (callback)** patterns.
*   **Distributed scheduling**: integrates `APScheduler` with Crontab/Interval/Date triggers, using distributed locks to prevent duplicate execution across instances.
*   **Delayed tasks**: native `countdown` (relative time) and `eta` (absolute time) delayed scheduling.
*   **Task deduplication**: deduplicates by a fingerprint of the function arguments (with TTL expiry), ignoring noise such as random URL parameters.

#### 🔭 Dimension 6: Observability

*   **Tracing**: native **OpenTelemetry** integration, with Jaeger/SkyWalking support and automatic context injection for end-to-end tracing across components.
*   **Metrics**: built-in **Prometheus** exporter supporting Pull and PushGateway modes, with real-time metrics shown in Grafana.
*   **Web console**: a built-in visual management UI showing backlog, QPS curves and consumer metadata.
*   **Remote operations**: `RemoteTaskKiller` terminates specific running tasks; `fabric_deploy` provides hot code deployment.
                funweb (funboost_web_manager) supports script updates and deployment, process liveness monitoring, log viewing and convenient file log search

#### 🧬 Dimension 7: Developer Experience

*   **FCT context**: the global object `from funboost import fct` gives access to metadata such as the TaskID and retry count anywhere in the call chain.
*   **Full syntax support**: fully supports **class methods (classmethod)**, **instance methods** and **async functions (async def)** as consumers.
*   **Lifecycle hooks**: the `consumer_override_cls` interface lets you override core logic such as message cleaning and result callbacks, handles **non-standard message formats**, and **lets you override any parent class method**.
*   **Object transfer**: a Pickle serialization option lets you pass custom Python objects directly as task arguments.
*   **Super decorator**: even if you don't need distribution or message queues, you can use the `@boost` decorator with **MEMORY_QUEUE** mode. A single @boost decorator provides 10+ features such as concurrency control, QPS limiting, automatic retries and task deduplication, worth as much as stacking 10 ordinary decorators.





## 1.3 🚀 Quick Start: Your First Funboost Program

> **⚠️ Environment setup (important)**
>
> Before running the code, make sure you understand the concept of **`PYTHONPATH`**.
> When running from Windows cmd or Linux, we recommend setting `PYTHONPATH` to the project root so the framework can generate or read its configuration automatically.
> 👉 [Learn about PYTHONPATH](https://github.com/ydf0509/pythonpathdemo)

### 1.3.1 ✨ Hello World: The Simplest Task Scheduling

This example shows how to turn an ordinary sum function into a distributed task.

**How the code works:**
1.  **Define the task**: use the `@boost` decorator, specifying the queue name `task_queue_name1` and QPS `5`.
2.  **Publish tasks**: call `task_fun.push(x, y)` to send messages.
3.  **Consume tasks**: call `task_fun.consume()` to start background threads that process them automatically.

```python
import time
from funboost import boost, BrokerEnum, BoosterParams

# Core configuration: use local SQLite as the message queue, with QPS limited to 5
@boost(BoosterParams(
    queue_name="task_queue_name1", 
    qps=5, 
    broker_kind=BrokerEnum.SQLITE_QUEUE
))
def task_fun(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3)  # Simulate a slow call; the framework works around the blocking with concurrency automatically

if __name__ == "__main__":
    # 1. Producer: publish 100 tasks
    for i in range(100):
        task_fun.push(i, y=i * 2)
    
    # 2. Consumer: start the scheduling loop
    task_fun.consume()
```

> **💡 Tips**
> If you get a `read-only` error using `SQLITE_QUEUE` on Linux/Mac, change `SQLLITE_QUEUES_PATH` in `funboost_config.py` to a directory you have write access to (see docs section 10.3).

**Screenshots:**

**Publishing tasks:**
![Publishing screenshot](https://s21.ax1x.com/2024/04/29/pkFkP4H.png) 

**Consuming tasks:**
![Consuming screenshot](https://s21.ax1x.com/2024/04/29/pkFkCUe.png)



### 1.3.2 🔥 Advanced Practice: RPC, Scheduled Tasks and Smooth Combos

This all-in-one example shows Funboost's core capabilities:
*   ✅ **Parameter reuse**: inherit from `BoosterParams` to reduce duplicate code.
*   ✅ **RPC mode**: the publisher fetches consumer results synchronously.
*   ✅ **Smooth startup**: start multiple consumers in a row without blocking.
*   ✅ **Scheduled tasks**: powerful scheduling based on `APScheduler`.

```python
import time
from funboost import boost, BrokerEnum, BoosterParams, ctrl_c_recv, ConcurrentModeEnum, ApsJobAdder

# 1. Define a shared base config class to reduce duplicate code
class MyBoosterParams(BoosterParams):
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    max_retry_times: int = 3
    concurrent_mode: str = ConcurrentModeEnum.THREADING 

# 2. Consumer function step1: demonstrates RPC mode
@boost(MyBoosterParams(
    queue_name='s1_queue', 
    qps=1,   
    is_using_rpc_mode=True  # Enable RPC so results can be fetched
))
def step1(a: int, b: int):
    print(f'step1: a={a}, b={b}')
    time.sleep(0.7)
    # The function can publish further tasks to step2
    for j in range(10):
        step2.push(c=a+b+j, d=a*b+j, e=a-b+j)
    return a + b

# 3. Consumer function step2: demonstrates overriding parameters
@boost(MyBoosterParams(
    queue_name='s2_queue', 
    qps=3, 
    max_retry_times=5  # Override the base class default
)) 
def step2(c: int, d: int, e: int=666):
    time.sleep(3)
    print(f'step2: c={c}, d={d}, e={e}')
    return c * d * e

if __name__ == '__main__':
    # --- Start consuming ---
    step1.consume()  # Non-blocking start
    step2.consume()
    step2.multi_process_consume(3) # Stack 3 processes of concurrency

    # --- RPC call demo ---
    async_result = step1.push(100, b=200)
    print('RPC result:', async_result.result)  # Block until the result is ready

    # --- Batch publishing demo ---
    for i in range(100):
        step1.push(i, i*2)
        # The publish method supports more advanced parameters (such as task_id)
        step1.publish({'a':i, 'b':i*2}, task_id=f'task_{i}')

    # --- Scheduled task demo (APScheduler) ---
    # Option 1: run at a specific date
    ApsJobAdder(step2, job_store_kind='redis', is_auto_start=True).add_push_job(
        trigger='date', run_date='2025-06-30 16:25:40', args=(7, 8, 9), id='job1'
    )
    # Option 2: run at an interval
    ApsJobAdder(step2, job_store_kind='redis').add_push_job(
        trigger='interval', seconds=30, args=(4, 6, 10), id='job2'
    )

    # Block the main thread to keep the program running
    ctrl_c_recv()
```

> **🧠 Design philosophy**
> Funboost advocates an **"anti-framework"** mindset: you are the protagonist, the framework is just a plugin.
> `task_fun(1, 2)` runs the function directly; `task_fun.push(1, 2)` publishes it to the queue.
> You can remove `@boost` at any time, and your code is still pure Python functions.

---

### 1.3.3 ✂️ Minimal Syntax: Omitting `@boost`

If you want maximum brevity, you can use `@BoosterParams` directly as the decorator; it is equivalent to `@boost(BoosterParams(...))`.

```python
# Minimal syntax
@BoosterParams(queue_name="task_queue_simple",qps=5)
def task_fun(a, b):
    return a + b
```

### 1.3.4 ❌ Outdated Syntax: Passing Config Arguments Directly to @boost (Not Recommended)
Passing arguments directly to `@boost` instead of using `BoosterParams` for configuration is outdated and not recommended, because you lose code completion.   
```python
# ⚠️ Counterexample: outdated syntax, not recommended!
@boost(queue_name="task_queue_simple",qps=5)
def task_fun(a, b):
    return a + b
```


## 🖥️ funweb (Funboost Web Manager) UI Preview

The visual management console provides powerful monitoring and operations capabilities. Screenshots of the core features:



Function results: view and search the real-time consumption status and results of functions  
[![Function results table](https://s41.ax1x.com/2025/12/19/pZ1L5h4.png)](https://imgchr.com/i/pZ1L5h4)

Queue operations: view and operate on queues, including clearing, pausing consumption, resuming consumption, and adjusting QPS and concurrency  
[![Queue operations 1](https://s41.ax1x.com/2025/12/17/pZlrYPH.png)](https://imgchr.com/i/pZlrYPH)
[![Queue operations 2](https://s41.ax1x.com/2025/12/17/pZlrUxI.png)](https://imgchr.com/i/pZlrUxI)

Queue operations: view consumption charts and metrics (historical run count, failure count, completions/failures in the last 10 seconds, average duration, remaining messages, etc.)  
[![Queue consumption chart](https://s41.ax1x.com/2025/12/19/pZ104HS.png)](https://imgchr.com/i/pZ104HS) 

RPC calls: publish messages to 30 kinds of message queues from the web page and get function results; results can also be fetched by task_id  
[![RPC call succeeded - green](https://s41.ax1x.com/2025/12/19/pZ10RjP.png)](https://imgchr.com/i/pZ10RjP)

Scheduled task management: list page  
[![Scheduled task list](https://s41.ax1x.com/2025/12/17/pZlrNRA.png)](https://imgchr.com/i/pZlrNRA)



## 1.4 💡 Why Python Badly Needs Distributed Function Computing

The nature of the Python language makes it more dependent on distributed scheduling frameworks than languages like Java/Go. There are two main reasons:

### 1️⃣ Pain point 1: the GIL (poor multi-core utilization)
> 🛑 **Status quo**: because of the GIL (Global Interpreter Lock), an ordinary Python script cannot use multiple CPU cores. On a 16-core machine, CPU utilization tops out at **6.25% (1/16)**.
> 😓 **Difficulty**: writing `multiprocessing` code by hand is cumbersome, involving complex inter-process communication (IPC), task distribution and state sharing.

✅ **Funboost's solution**:
*   **Decoupled by design**: tasks are decoupled through a broker (such as Redis/RabbitMQ), so you never have to hand-write how tasks are distributed to processes or how processes communicate.
*   **Transparent multiprocessing**: single-process and multi-process scripts are written exactly the same way. **No** hand-written `multiprocessing` needed; multi-core performance is squeezed out automatically.

### 2️⃣ Pain point 2: native performance bottleneck (dynamic language)
> 🐌 **Status quo**: as a dynamic language, Python's single-threaded execution is usually slower than static languages.
> 🚀 **Need**: to make up for single-machine speed, you must trade for time through **horizontal scaling**.

✅ **Funboost's solution**:
*   **Seamless scaling**: without changing any code, it adapts to many runtime environments:
    *   🔄 **Multiple interpreters**: start multiple Python processes on the same machine.
    *   🐳 **Containerized**: deploy across multiple Docker containers.
    *   ☁️ **Across physical machines**: deploy across multiple physical servers.
*   **Unified engine**: with Funboost as the scheduling core, Python runs on top of a cluster and achieves much higher system throughput.


## 1.5 🎓 The Best Learning Path

Funboost's design philosophy is **"minimalism"**. You don't need to read long treatises; just master the core through practice:

1.  **🧪 Learn by experimenting**:
    *   Use the sum example in **section 1.3** as your template.
    *   Change the parameters of the `@boost` decorator (such as `qps` and `concurrent_num`).
    *   Add `time.sleep()` in the function to simulate slow work.
    *   **Observe**: watch the console output to see distribution, concurrency and rate control in action.

2.  **✨ The one-line principle**:
    *   This is the simplest framework: its core is just one line of `@boost`.
    *   Master this decorator and you master the whole framework. That is far simpler than traditional frameworks that require inheriting multiple classes and configuring multiple files.

> **🤖 AI Tutor**
> We strongly recommend **[Chapter 14 of the docs]** to learn how to quickly master `funboost`'s advanced usage with large AI models.

---

## 1.6 🥋 Funboost Masters the "Star-Absorbing Technique", Absorbing Celery's Lifetime of Inner Power in One Move

**Funboost's minimalist moves + Celery's deep inner power = unrivaled in the martial world**

> "Many in the martial world are dazzled by Celery's prestigious reputation. Although Funboost moves dozens of times faster, as proven in the training ground (section 2.6), some heroes cling to their old ways and refuse to test the blade themselves.
> So Funboost unleashes the **'Star-Absorbing Technique'** and takes Celery into its service (as a Broker). **Once you enter my school, you follow my command**, dissolving everyone's attachments."

Celery has dominated the Python async world for over a decade. Its inner power is deep, but its moves are convoluted and its school rules strict (tedious configuration), deterring countless heroes. 
Now Funboost unleashes the **"Star-Absorbing Technique"**: with a single move, `BrokerEnum.CELERY`, Celery instantly becomes its **guardian disciple**. From then on, Celery is a mere **subset** of Funboost, at its command! 

### ⚔️ Dimensional Strike: Supreme Martial Arts That Make the Complex Simple
Controlling Celery through Funboost is like Linghu Chong mastering the Nine Swords of Dugu: it breaks every convoluted move and strikes straight at the vital point:

| 🆚 Duel of Moves | 🛑 Native Celery (shackles of the old school) | 🟢 Funboost Sword Control (ease of the new grandmaster) |
| :--- | :--- | :--- |
| **Launch technique**<br>(deployment) | **Reciting incantations**: you must memorize long `worker/beat` command lines; one slip and you go astray. | **Mind and intent as one**: the code is the launcher, no incantations to memorize; `python xx.py` breaks every technique. |
| **School rules**<br>(structure) | **Strict commandments**: a mandatory directory structure; misplace a file and you're expelled. Extremely rigid. | **No form beats form**: any leaf or petal can strike; any directory, any file can be the battlefield, with no constraints. |
| **Inner energy flow**<br>(barrier to entry) | **Meridians reversed**: you must manually cultivate `includes` and `task_routes`, easily leading to qi deviation (config errors). | **Perfectly natural**: the meridians open by themselves; the framework discovers and registers tasks automatically, flowing like water. |
| **Insight into heaven and earth**<br>(experience) | **Blind men and the elephant**: `@app.task` arguments are like flowers in fog; the IDE can't see them, making missteps easy. | **Heavenly eye**: `BoosterParams` opens an all-seeing view; code completion works like magic, what you see is what you get. |

> **📜 Scripture Library (code examples)**
> To practice this technique, see **[section 11.1]**.
> Just use Funboost's minimalist swordplay, and the mighty Celery engine underneath will move mountains and fill seas for you, with thunderous power and no backlash.


 Note that funboost's performance already far exceeds celery's. Absorbing celery as a broker, and supporting celery as a funboost broker, is meant to dispel some people's doubts about the stability of funboost's scheduling core.   
 > See docs section 2.6, **funboost vs celery controlled-variable performance comparison**, and section 2.9, **Why exactly is funboost dozens of times faster than celery? Too outrageous, too fake to be true?**


[View the full tutorial for the funboost distributed function scheduling platform](https://funboost.readthedocs.io/)  

![](https://visitor-badge.glitch.me/badge?page_id=distributed_framework)  

<div> </div>  

[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  

