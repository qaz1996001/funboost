---
noteId: "b8794550160c11f1876707e213463054"
tags: []

---


# Funboost AI Coding Guide (Rules & Skills)

## Section 1: Rules (AI Behavioral Guidelines & Constraints)

These are **absolute rules** that AI must never violate when writing `funboost` code, designed to eliminate AI hallucinations (e.g., fabricating parameters, using deprecated APIs, confusing Celery concepts).

### 0. Supreme Knowledge Principle: Official Context Document as Single Source of Truth
- **Must deeply read**: Before writing any `funboost` code or answering questions, you must comprehensively search and study the `funboost_all_docs_and_codes.md` document provided by the user (containing 100K+ lines of tutorials and source code).
- **Absolutely no fabrication**: Your pre-training knowledge may lack the latest `funboost` details or easily confuse it with `Celery`. All class names, method names, and parameter definitions (especially `BoosterParams` attributes and middleware configs) **must be 100% based on source code facts or tutorial examples** from that document. No LLM hallucinations allowed!

### 1. Core Syntax: Always Use `BoosterParams`
- **Forbidden**: Old-style parameter passing `@boost("queue_name", qps=2)`.
- **Required**: Place all config parameters in a `BoosterParams` object: `@boost(BoosterParams(queue_name="xxx", ...))`.
- **No fabricated parameters**: `BoosterParams` is a Pydantic model. Never pass non-existent fields (e.g., `timeout` — correct is `function_timeout`; `max_retries` — correct is `max_retry_times`).

### 2. Publishing Messages (`push` vs `publish`)
- For passing only function business parameters, use `func.push(*args, **kwargs)`.
- When passing framework control parameters (e.g., `task_id`, `countdown`, `eta`, `msg_expire_seconds`), **must** use `func.publish(msg_dict, task_options=TaskOptions(...))`.
- In **async environments** (async def), must use `await func.aio_push()` or `await func.aio_publish()`.

### 3. Consumer Startup Methods
- Basic startup: `func.consume()`.
- Multi-process + multi-thread stacked concurrency (extreme performance): `func.multi_process_consume(n)` or shorthand `func.mp_consume(n)`.
- Group startup: `BoostersManager.consume_group("group_name")` (requires setting `booster_group` in BoosterParams first).
- At the end of startup code, if the main thread has no other blocking tasks, **recommended** to use `from funboost import ctrl_c_recv; ctrl_c_recv()` to prevent main thread exit.
- Starting multiple consumers sequentially: `func1.consume(); func2.consume()`. Do not use child threads to start consumption — `func1.consume()` does not block the main thread. Do not use `threading.Thread(target=func1.consume).start()` — this is unnecessary, as funboost already handles this at the framework level.

### 4. Context Retrieval (No Celery Thinking)
- **Forbidden**: Adding `self` or `bind=True` to function parameters like Celery.
- **Must** use the global context object: `from funboost import fct`.
- Get Task ID: `fct.task_id`.
- Get retry count: `fct.function_result_status.run_times` (function_result_status has many other properties, type is `FunctionResultStatus`).
- Get full message: `fct.full_msg`.

### 5. Scheduled Tasks (ApsJobAdder)
- **Forbidden**: Using native `apscheduler.add_job` to execute consumer functions directly.
- **Must** use the `ApsJobAdder` class: `ApsJobAdder(func, job_store_kind='redis').add_push_job(trigger='...', ...)`.

### 6. Async Concurrency (Asyncio)
- If the consumer function is `async def`, **must** set `concurrent_mode=ConcurrentModeEnum.ASYNC` in `BoosterParams` (threading mode can also handle async functions but is not optimal).
- When getting RPC results in asyncio, **must** use `AioAsyncResult` with `await`. Never use synchronous `AsyncResult.result` in async functions.

### 7. FaaS Microservices
- When integrating FastAPI/Flask/Django, **no need** to manually write publish/get-result APIs.
- **Prefer built-in router**: `from funboost.faas import fastapi_router; app.include_router(fastapi_router)`.

### 8. Heterogeneous System Compatibility & Arbitrary JSON Consumption (Very Important)
- By default, Funboost strictly validates that published message fields match the function signature.
- **To consume messages not published by Funboost (e.g., from Java/Go, or JSON with unknown keys)**:
  - **Must** set `should_check_publish_func_params=False` in BoosterParams.
  - **Must** define the consumer function to accept variable-length arguments, e.g., `def task_fun(**kwargs):`. Never write `def task_fun(msg):` to receive the entire dictionary with a single parameter.

### 9. Instance Method & Class Method `push` Call Convention
- AI easily gets instance method publishing wrong! Funboost supports decorating instance and class methods, but `push` syntax differs from regular functions.
- **Instance methods**: **Forbidden** `obj.method.push(x)`. **Must** write `ClassName.method.push(obj, x)`, first argument must be the object instance, and the object must define `obj_init_params` for deserialization.
- **Class methods**: **Forbidden** `ClassName.method.push(x)`. **Must** write `ClassName.method.push(ClassName, x)`, first argument must be the class itself.

### 10. Custom Extension Convention (`user_options` & `override_cls`)
- **Forbidden**: Modifying Funboost source code or fabricating `BoosterParams` attributes for custom logic.
- For custom configuration, **must** use `BoosterParams(user_options={'my_key': 'value'})` dictionary.
- For overriding interception logic (e.g., message formatting, rate limiting), **must** use OOP inheritance from `AbstractConsumer` via `consumer_override_cls`.

### 11. AI Agent Should Use `python -c "import subprocess; subprocess.run(['python','your_script.py'], timeout=30)"` to Start Funboost Consumer Scripts
- **Core issue**: Funboost consumer functions run in an infinite loop pulling messages; the program won't auto-terminate, blocking AI Agent test runs.
- **Must actively terminate**: AI Agent **must** forcefully kill the program after an appropriate time (max 50 seconds) to avoid prolonged blocking.
- **AI should use subprocess to start funboost consumption**: Always use `python -c "import subprocess; subprocess.run(['python','your_script.py'], timeout=30)"` — this auto-kills the program. Replace `your_script.py` with the actual script.
- Never directly use `python your_script.py` to start funboost programs to avoid blocking the AI workflow.

---

## Section 2: Skills (AI Skill Templates)

These are **standard code snippets** for AI, enabling direct copy of best practices for specific scenarios (crawlers, scheduled tasks, microservices) without improvisation.

### Skill 0: Simplest Hello World Task (Zero Config / Local Single Process)
**Scenario**: User wants the simplest background task, no need to install Redis/RabbitMQ, just needs to run.
**Template**:
```python
import time
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv

@boost(BoosterParams(
    queue_name="hello_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=2,
))
def hello_task(word: str):
    print(f"Hello, {word}!")
    time.sleep(1)
    return True

if __name__ == '__main__':
    for i in range(10):
        hello_task.push(word=f"funboost_{i}")
    hello_task.consume() 
    ctrl_c_recv()
```

### Skill 1: Standard Background Task (with Advanced Control)
**Scenario**: User needs a background queue task with high concurrency, rate limiting, and error retry.
**Template**:
```python
import time
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv

@boost(BoosterParams(
    queue_name="my_standard_task",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    concurrent_num=50,
    qps=10,
    max_retry_times=3,
))
def my_task(user_id: int, action: str):
    print(f"Processing user: {user_id}, action: {action}")
    time.sleep(1)
    return True

if __name__ == '__main__':
    for i in range(100):
        my_task.push(user_id=i, action="login")
    my_task.mp_consume(2)
    ctrl_c_recv()
```

### Skill 2: RPC Mode (Publish and Wait for Result)
**Scenario**: User needs to publish a task and synchronously/asynchronously wait for the consumer to finish and return a result.
**Template**:
```python
from funboost import boost, BoosterParams, BrokerEnum, AsyncResult

@boost(BoosterParams(
    queue_name="rpc_task",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    is_using_rpc_mode=True,
))
def calc_sum(a: int, b: int):
    return a + b

if __name__ == '__main__':
    calc_sum.consume()
    async_result: AsyncResult = calc_sum.push(10, 20)
    print(f"Task ID: {async_result.task_id}, Result: {async_result.result}")
```

### Skill 3: Scheduled Tasks (Cron / Interval)
**Scenario**: User needs daily scheduled or periodic task execution.
**Template**:
```python
from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder, ctrl_c_recv

@boost(BoosterParams(queue_name="daily_report", broker_kind=BrokerEnum.REDIS))
def generate_report(report_type: str):
    print(f"Generating {report_type} report...")

if __name__ == '__main__':
    generate_report.consume()
    ApsJobAdder(generate_report, job_store_kind='redis').add_push_job(
        trigger='cron',
        hour=2,
        minute=0,
        kwargs={"report_type": "sales"},
        id='daily_sales_report',
        replace_existing=True
    )
    ctrl_c_recv()
```

### Skill 4: Asyncio Async Tasks & Coroutine Publishing
**Scenario**: User uses FastAPI or other asyncio ecosystem, needs pure async scheduling.
**Template**:
```python
import asyncio
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, AioAsyncResult

@boost(BoosterParams(
    queue_name="async_crawler",
    broker_kind=BrokerEnum.REDIS,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    is_using_rpc_mode=True
))
async def async_fetch(url: str):
    await asyncio.sleep(1)
    return f"Data from {url}"

async def main():
    aio_result = await async_fetch.aio_push("http://example.com")
    result_status = await AioAsyncResult(aio_result.task_id).status_and_result
    print(result_status.result)

if __name__ == '__main__':
    async_fetch.consume()
    asyncio.run(main())
```

### Skill 5: Declarative Workflow Orchestration
**Scenario**: User needs to execute complex task flows with Chain (serial), Group (parallel), or Chord (parallel + aggregation).
**Template**:
```python
from funboost import boost
from funboost.workflow import chain, group, chord, WorkflowBoosterParams

@boost(WorkflowBoosterParams(queue_name="wf_download"))
def download(url): return f"/tmp/{url}"

@boost(WorkflowBoosterParams(queue_name="wf_process"))
def process(path, resolution): return f"{path}_{resolution}"

@boost(WorkflowBoosterParams(queue_name="wf_notify"))
def notify(results, user_id): print(f"User {user_id} done: {results}")

if __name__ == '__main__':
    download.consume()
    process.consume()
    notify.consume()
    workflow = chain(
        download.s("video.mp4"),
        chord(
            group(process.s(resolution=r) for r in ['360p', '720p', '1080p']),
            notify.s(user_id=1001)
        )
    )
    result = workflow.apply()
```

### Skill 6: Quick FaaS Microservice Integration
**Scenario**: User needs to expose Funboost tasks as HTTP endpoints for external system calls.
**Template**:
```python
import uvicorn
from fastapi import FastAPI
from funboost.faas import fastapi_router, CareProjectNameEnv

CareProjectNameEnv.set('my_faas_project')

app = FastAPI()
app.include_router(fastapi_router)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Core API Endpoints**:

After startup, all endpoints are under the `/funboost` prefix. Interactive docs at `http://127.0.0.1:8000/docs`.

#### 6.1 Publish Message (with RPC Support)

**Endpoint**: `POST /funboost/publish`

**Request Body**:
```json
{
    "queue_name": "my_task_queue",
    "msg_body": {"user_id": 1001, "action": "login"},
    "need_result": true,
    "timeout": 60,
    "task_id": "optional_custom_task_id"
}
```

**Field Description**:
- `queue_name` (required): Queue name
- `msg_body` (required): Message body dict, i.e., the consumer function's parameters
- `need_result` (optional): Whether to wait for RPC result, default `false`
- `timeout` (optional): Max timeout in seconds for waiting, default `60`
- `task_id` (optional): Custom task ID, auto-generated if not provided

---

#### 6.2 Other Important Endpoint Quick Reference

**Note**: For full API definitions, AI can check the FastAPI routes and Pydantic model definitions in `funboost\faas\fastapi_adapter.py`.

**Get RPC Result**: `GET /funboost/get_result?task_id={task_id}&timeout=5`

**Add Scheduled Task**: `POST /funboost/add_timing_job`
```json
{
    "queue_name": "my_queue",
    "trigger": "cron",
    "hour": "2",
    "minute": "0",
    "kwargs": {"report_type": "daily"}
}
```
Trigger types: `date` (one-time) / `interval` (periodic) / `cron` (cron expression)

**Get Queue Message Count**: `GET /funboost/get_msg_count?queue_name={queue_name}`

**Pause/Resume Consumption**: `POST /funboost/pause_consume` or `/resume_consume`
```json
{"queue_name": "my_queue"}
```

**Get Scheduled Task List**: `GET /funboost/get_timing_jobs?queue_name={queue_name}`

**Get Single Scheduled Task**: `GET /funboost/get_timing_job?job_id={job_id}&queue_name={queue_name}`

**Delete Scheduled Task**: `DELETE /funboost/delete_timing_job?job_id={job_id}&queue_name={queue_name}`

**Clear Queue**: `POST /funboost/clear_queue`
```json
{"queue_name": "my_queue"}
```

**Get All Queues**: `GET /funboost/get_all_queues`

**Get All Queue Run Info**: `GET /funboost/get_all_queue_run_info`

---

**Tip**: Full API docs at `http://127.0.0.1:8000/docs`. All endpoints return unified format: `{"succ": bool, "msg": str, "data": any, "code": int}`


### Skill 7: Efficient Crawler (with boost_spider)
**Scenario**: User needs a distributed crawler with auto proxy switching, XPath parsing, and one-click database storage.
**Template**:
```python
from funboost import boost, BoosterParams, BrokerEnum
from boost_spider import RequestClient, SpiderResponse, DatasetSink

db_sink = DatasetSink("sqlite:///spider_data.db")

@boost(BoosterParams(
    queue_name="spider_task", 
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    qps=3,
    max_retry_times=5
))
def crawl_page(url: str):
    client = RequestClient(request_retry_times=3, is_change_ua_every_request=True)
    resp: SpiderResponse = client.get(url)
    title = resp.xpath('//title/text()').extract_first()
    data = {"url": url, "title": title}
    db_sink.save("article_table", data)
    return data
```

### Skill 8: Inheriting BoosterParams (Reducing Repetitive Config)
**Scenario**: When a project has multiple consumer functions with lots of repeated configuration. Create a custom subclass to avoid repeating the same config in every `@boost` decorator.
**Template**:
```python
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, ctrl_c_recv

class MyBoosterParams(BoosterParams):
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    max_retry_times: int = 3
    concurrent_mode: str = ConcurrentModeEnum.THREADING
    project_name: str = 'my_project'

@boost(MyBoosterParams(queue_name='task_queue_1'))
def task1(x: int):
    print(f"Task1: {x}")
    return x * 2

@boost(MyBoosterParams(queue_name='task_queue_3', qps=0.5))
def task3(report_type: str):
    print(f"Generating {report_type} report")
    return True

if __name__ == '__main__':
    task1.consume()
    task3.consume()
    ctrl_c_recv()
```

### Skill 9: Consuming Arbitrary JSON from Heterogeneous Systems
**Scenario**: Messages not published by Funboost (e.g., written directly to Redis by a Java team), with variable/unknown JSON fields.
**Template**:
```python
from funboost import boost, BoosterParams, BrokerEnum, fct

@boost(BoosterParams(
    queue_name="java_topic_queue",
    broker_kind=BrokerEnum.REDIS,
    should_check_publish_func_params=False
))
def process_any_msg(**kwargs):
    print(f"Received full dict from external system: {kwargs}")
    print(f"Original full message: {fct.full_msg}")

if __name__ == '__main__':
    process_any_msg.consume()
```

### Skill 10: Custom Consumer Interceptor (Override Class)
**Scenario**: User wants to execute custom logic before/after function execution (e.g., data cleaning, custom rate limiter, custom result storage).
**Template**:
```python
from funboost import boost, BoosterParams, AbstractConsumer, FunctionResultStatus

class MyCustomConsumer(AbstractConsumer):
    def _user_convert_msg_before_run(self, msg) -> dict:
        if isinstance(msg, str) and "=" in msg:
            return {k: int(v) for k, v in [pair.split('=') for pair in msg.split(',')]}
        return super()._user_convert_msg_before_run(msg)
        
    def user_custom_record_process_info_func(self, function_result_status: FunctionResultStatus):
        if function_result_status.success:
            print(f"Custom storage: Task {function_result_status.task_id} succeeded, duration {function_result_status.time_cost}")

@boost(BoosterParams(
    queue_name="custom_override_queue",
    consumer_override_cls=MyCustomConsumer
))
def my_task(a: int, b: int):
    return a + b
```

### Skill 11: Configuring Middleware-Specific Parameters (`broker_exclusive_config`)
**Scenario**: You need to set advanced features specific to the chosen message queue middleware (e.g., RabbitMQ message priority, Kafka consumer groups/partitions, Redis Stream consumer group names). These cannot be expressed through generic `BoosterParams` fields and must be passed via `broker_exclusive_config`.
**Template**:
```python
from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name="priority_queue",
    broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM,
    broker_exclusive_config={
        'x-max-priority': 5,
        'no_ack': False,
    }
))
def priority_task(user_id: int):
    print(f"Processing VIP user: {user_id}")
    return True

@boost(BoosterParams(
    queue_name="kafka_topic",
    broker_kind=BrokerEnum.KAFKA_CONFLUENT,
    broker_exclusive_config={
        'group_id': 'my_consumer_group',
        'auto_offset_reset': 'earliest',
        'num_partitions': 10,
        'replication_factor': 1,
    }
))
def process_kafka_msg(data: dict):
    print(f"Received from Kafka: {data}")
```

**Notes**:
- `broker_exclusive_config` is a dict that **can only contain keys supported by the chosen `broker_kind`**. Supported keys are defined in `funboost/core/broker_kind__exclusive_config_default_define.py` (e.g., `'x-max-priority'` only works for RabbitMQ, not Redis).
- Unsupported keys trigger a warning but don't block execution. Consult the middleware docs or framework source code to ensure config takes effect.

### Skill 12: Starting Funboost Web Manager (funboost_web_manager)
**Scenario**: Need a Web UI to monitor queue status, consumption speed, task success rates, etc.

**Template**:

#### Method 1: Command Line (Recommended)
```bash
export PYTHONPATH=/path/to/your/project
python -m funboost.funweb.app
```

#### Method 2: In Code
```python
from funboost.funweb.app import start_funboost_web_manager

start_funboost_web_manager()

start_funboost_web_manager(
    port=8080,
    care_project_name="my_project"
)
```


### Skill 100: BoosterParams Configuration Dictionary (AI Must-Read)
**Important**: This is the complete set of legal `BoosterParams` fields. **AI can only use the following attribute names when generating `@boost` configs. Absolutely forbidden to fabricate parameter names not listed here!**

```python
class BoosterParams(BaseJsonAbleModel):
    """
    Mastering funboost's essence means knowing BoosterParams parameters.
    If you know all the parameter fields, you've mastered 90% of funboost.
    """

    queue_name: str  # Queue name, required. Each function must use a different queue name.
    broker_kind: str = BrokerEnum.SQLITE_QUEUE  # Middleware selection, see section 3.1

    # project_name: Project name, a management-level label. Default None.
    # Used for filtering queues by project in Redis-stored funboost info.
    # Typically used with CareProjectNameEnv.set($project_name).
    project_name: typing.Optional[str] = None

    # If qps is set and concurrent_num is default 50, auto-expands to 500 concurrency.
    # Uses smart thread pool that auto-shrinks when tasks are few.
    concurrent_mode: str = ConcurrentModeEnum.THREADING  # Concurrency mode: THREADING, GEVENT, EVENTLET, ASYNC, SINGLE_THREAD
    concurrent_num: int = 50  # Concurrency count, type determined by concurrent_mode
    specify_concurrent_pool: typing.Optional[FunboostBaseConcurrentPool] = None  # Use a specified thread/coroutine pool
    
    specify_async_loop: typing.Optional[asyncio.AbstractEventLoop] = None  # Specify async event loop
    is_auto_start_specify_async_loop_in_child_thread: bool = True
    
    # qps: Powerful rate control. Specifies function executions per second.
    # Can be decimal 0.01 (once per 100s) or 50 (50 times/s). None = no rate limit.
    # When qps is set, no need to specify concurrency — funboost auto-adapts pool size.
    qps: typing.Union[float, int, None] = None
    # is_using_distributed_frequency_control: Whether to use distributed rate control
    # (relies on Redis to count consumers, then divides frequency evenly).
    is_using_distributed_frequency_control: bool = False

    is_send_consumer_heartbeat_to_redis: bool = False  # Whether to send consumer heartbeat to Redis

    # --------------- Retry Config Start
    # max_retry_times: Max auto-retry count on error.
    # Can throw ExceptionForRetry for immediate retry.
    # ExceptionForRequeue returns message to broker.
    # ExceptionForPushToDlxqueue sends to dead letter queue (queue_name + _dlx).
    max_retry_times: int = 3
    
    # is_using_advanced_retry: Whether to use advanced retry with exponential backoff.
    # Two retry modes: requeue (release thread immediately) and sleep (sleep in current thread).
    # Example with base=1.0, multiplier=2.0, max=60.0: 1s, 2s, 4s, 8s, 16s, 32s, 60s, 60s...
    is_using_advanced_retry: bool = False  
    advanced_retry_config: dict = { 
        'retry_mode': 'sleep',
        'retry_base_interval': 1.0,
        'retry_multiplier': 2.0,
        'retry_max_interval': 60.0,
        'retry_jitter': False,
    }
    
    is_push_to_dlx_queue_when_retry_max_times: bool = False  # Send to DLQ after max retries exhausted
    # --------------- Retry Config End

    consuming_function_decorator: typing.Optional[typing.Callable[..., typing.Any]] = None  # Function decorator
    
    # function_timeout: Timeout in seconds. Auto-kills function if exceeded. 0 = no limit.
    # Use with caution — causes performance degradation and potential deadlocks.
    function_timeout: typing.Union[int, float, None] = None 
    # is_support_remote_kill_task: Whether to support remote task killing.
    is_support_remote_kill_task: bool = False  
    
    # log_level: Logger level for consumers and publishers. Recommended DEBUG.
    log_level: int = logging.DEBUG
    logger_prefix: str = ''
    create_logger_file: bool = True
    logger_name: typing.Union[str, None] = ''
    log_filename: typing.Union[str, None] = None
    is_show_message_get_from_broker: bool = False
    is_print_detail_exception: bool = True
    publish_msg_log_use_full_msg: bool = False

    msg_expire_seconds: typing.Union[float, int, None] = None  # Message expiry time. None = never discard.

    do_task_filtering: bool = False  # Whether to deduplicate based on function parameters.
    task_filtering_expire_seconds: int = 0  # Dedup expiry. 0 = permanent filtering.

    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_result=False, is_save_status=False, expire_seconds=7 * 24 * 3600, is_use_bulk_insert=False)

    user_custom_record_process_info_func: typing.Optional[typing.Callable[..., typing.Any]] = None

    is_using_rpc_mode: bool = False  # Whether to use RPC mode for getting consumer results.
    rpc_result_expire_seconds: int = 1800
    rpc_timeout: int = 1800

    delay_task_apscheduler_jobstores_kind: Literal['redis', 'memory'] = 'redis'

    # allow_run_time_cron: Only allow running during specified crontab expression times.
    # E.g., '* 23,0-2 * * *' = only run 23:00-02:59
    # '* 9-17 * * 1-5' = only Mon-Fri 9:00-17:59
    allow_run_time_cron: typing.Optional[str] = None

    schedule_tasks_on_main_thread: bool = False
    is_auto_start_consuming_message: bool = False

    # booster_group: Consumer group name for BoostersManager.consume_group
    booster_group: typing.Union[str, None] = None

    consuming_function: typing.Optional[typing.Callable[..., typing.Any]] = None  # Auto-generated
    consuming_function_raw: typing.Optional[typing.Callable[..., typing.Any]] = None  # Auto-generated
    consuming_function_name: str = ''  # Auto-generated

    # broker_exclusive_config: Middleware-specific config dict.
    # See funboost/core/broker_kind__exclusive_config_default.py for supported keys per broker.
    broker_exclusive_config: dict = {} 

    should_check_publish_func_params: bool = True  # Whether to validate published message params
    manual_func_input_params: dict = {'is_manual_func_input_params': False, 'must_arg_name_list': [], 'optional_arg_name_list': []}

    consumer_override_cls: typing.Optional[typing.Type] = None  # Custom consumer override class
    publisher_override_cls: typing.Optional[typing.Type] = None  # Custom publisher override class

    consuming_function_kind: typing.Optional[str] = None  # Auto-detected: CLASS_METHOD, INSTANCE_METHOD, STATIC_METHOD, COMMON_FUNCTION

    # user_options: User-defined custom config dict for advanced/special needs.
    # Provides a unified namespace for custom configuration without modifying BoosterParams source.
    user_options: dict = {}
    
    auto_generate_info: dict = {}  # Auto-generated info, no user input needed.
    
    # is_fake_booster: Whether this is a fake booster (for FaaS cross-project metadata management).
    is_fake_booster: bool = False

    booster_registry_name: str = StrConst.BOOSTER_REGISTRY_NAME_DEFAULT  
```
