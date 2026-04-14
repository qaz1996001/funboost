# -*- coding: utf-8 -*-

"""
All usage examples for funboost — demo showcase.
This file demonstrates 90% of funboost's main features.
"""

import time
import random
import asyncio
import datetime
from funboost import (
    boost,                  # Core decorator
    BoosterParams,          # Parameter configuration class
    BrokerEnum,             # Broker enum
    ConcurrentModeEnum,     # Concurrent mode enum
    TaskOptions, # Priority/delay configuration
    ApsJobAdder,            # Scheduled job adder
    ctrl_c_recv,            # Main-thread blocking utility
    fct,                    # Context object (Funboost Current Task)
    BoostersManager,        # Consumer manager (for group startup)
    AsyncResult,            # Async result object for synchronous code
    AioAsyncResult,          # Async result object for asyncio ecosystem
)

# ==========================================
# 1. Basic Task (uses SQLite local file as queue; no Redis/RabbitMQ needed for testing)
# ==========================================
@boost(BoosterParams(
    queue_name="demo_queue_basic",
    broker_kind=BrokerEnum.SQLITE_QUEUE,  # Use local SQLite file as queue
    concurrent_num=2,                     # Thread concurrency count
))
def task_basic(x, y):
    print(f"[Basic Task] Processing: {x} + {y} = {x + y}")
    time.sleep(0.5)
    return x + y


# ==========================================
# 2. Retry Task (demonstrates automatic retry mechanism)
# 2.b Get task_id and message publish time (demonstrates fct context usage)
# ==========================================
@boost(BoosterParams(
    queue_name="demo_queue_retry",
    broker_kind=BrokerEnum.MEMORY_QUEUE,  # Use in-memory queue
    max_retry_times=3,                    # Max 3 retries

    is_print_detail_exception=False       # Do not print detailed stack trace; keep console clean
))
def task_retry(n):
    # Simulation: only succeeds when n > 8, otherwise raises an error to trigger retry
    if n <= 8:
        print(f"[Retry Task] Input {n} simulates failure, current run count: {fct.function_result_status.run_times}...")
        raise ValueError("Simulated error")
    print(f"[Retry Task] Input {n} processed successfully! Task ID: {fct.task_id}, Publish time: {fct.function_result_status.publish_time_format}")


# ==========================================
# 3. QPS Rate-Limited Task (precisely control executions per second)
# ==========================================
@boost(BoosterParams(
    queue_name="demo_queue_qps",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=2,  # Limit to 2 executions per second regardless of concurrency
))
def task_qps(idx):
    print(f"[QPS Task] {idx} running (approx. 2/sec)... {datetime.datetime.now()}")


# ==========================================
# 4. Asyncio Coroutine Task (high-performance IO-intensive)
# ==========================================
@boost(BoosterParams(
    queue_name="demo_queue_async",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC, # Enable asyncio mode
    concurrent_num=100,  # Coroutine concurrency can be set very high
    is_using_rpc_mode = True,
))
async def task_async(url):
    print(f"[Async Task] Starting request: {url}")
    await asyncio.sleep(1) # Simulate IO wait
    print(f"[Async Task] Request finished: {url}")
    return f'url:{url} ,resp: mock_resp'


# ==========================================
# 5. RPC Task (publisher retrieves result from consumer)
# Note: RPC mode typically requires Redis; here we use MEMORY_QUEUE for demo (Funboost supports in-memory simulation)
# For production, it is strongly recommended to configure funboost_config.py to use Redis
# ==========================================
@boost(BoosterParams(
    queue_name="demo_queue_rpc",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_using_rpc_mode=True,  # Enable RPC mode
    rpc_result_expire_seconds=10
))
def task_rpc(a, b):
    time.sleep(1)
    return a * b


# ==========================================
# 6. Task Filtering (deduplication)
# ==========================================
@boost(BoosterParams(
    queue_name="demo_queue_filter",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    do_task_filtering=True,           # Enable filtering
    task_filtering_expire_seconds=60  # Tasks with identical parameters within 60 seconds are executed only once
))
def task_filter(user_id, user_sex, user_name):
    print(f"[Filter Task] Executing: user_id={user_id} name={user_name} sex={user_sex}")


# ==========================================
# 7. Delayed Task (executed with a delay after consumer picks it up)
# ==========================================
@boost(BoosterParams(queue_name="demo_queue_delay", broker_kind=BrokerEnum.MEMORY_QUEUE))
def task_delay(msg):
    print(f"[Delay Task] Finally executed: {msg} - Current time: {datetime.datetime.now()}")


# ==========================================
# 10. Booster Group (group startup demo)
# Scenario: Suppose you have 100 consumer functions and only want to start those belonging to 'my_group_a'
# ==========================================
@boost(BoosterParams(
    queue_name="demo_group_task_1",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    booster_group="my_group_a"  # Specify group name
))
def task_group_a_1(x):
    print(f"[Group Task A-1] Processing: {x}")

@boost(BoosterParams(
    queue_name="demo_group_task_2",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    booster_group="my_group_a"  # Specify the same group name
))
def task_group_a_2(x):
    print(f"[Group Task A-2] Processing: {x}")

@boost(BoosterParams(
    queue_name="demo_group_task_3",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    booster_group="my_group_b"  # Different group; will not be started by my_group_a
))
def task_group_b_1(x):
    print(f"[Group Task B-1] (This should not run because my_group_b was not started and task_group_b_1 consumer was not started): {x}")


# ==========================================
# Main entry point
# ==========================================
if __name__ == '__main__':
    # --- 1. Start regular consumers ---
    # Startup method A: start individually
    task_basic.consume()
    task_retry.consume()
    task_qps.consume()
    task_async.consume()
    task_rpc.consume()
    task_filter.consume()
    task_delay.consume()

    # Startup method B: multi-process startup (for CPU-intensive tasks; shown here for demo only)
    # task_basic.multi_process_consume(process_num=2)   # or task_basic.mp_consume(process_num=2), mp_consume is an alias for multi_process_consume

    # Startup method C: group startup (new demo)
    print(">>> Starting all consumers belonging to group 'my_group_a'...")
    BoostersManager.consume_group("my_group_a")
    # Note: task_group_b_1 is not started here because it belongs to my_group_b

    print("=== Consumers started, beginning to publish tasks ===")
    time.sleep(1)

    # --- 2. Publish basic tasks ---
    for i in range(5):
        task_basic.push(i, i+1)

    # --- 3. Publish retry tasks ---
    task_retry.push(5) # This will fail and retry 3 times
    task_retry.push(6666) # This will succeed without retrying

    # --- 4. Publish QPS tasks ---
    for i in range(6):
        task_qps.push(i)

    # --- 5. Publish async tasks ---
    for i in range(3):
        # Supports async push: await task_async.aio_push(...)
        task_async.push(f"http://site-{i}.com")

    # --- 6. RPC result demo ---
    print("\n--- RPC Demo ---")
    # push returns an AsyncResult object
    async_result:AsyncResult = task_rpc.push(10, 20)
    print("RPC task published, waiting for result...")
    # The result property blocks the current thread until the result is available
    print(f"RPC Result: {async_result.result}")


    # --- 7. Task filtering demo ---
    print("\n--- Filter Demo ---")
    print("If filter_str is not specified, all function arguments including user_id, user_sex, and user_name are used for filtering by default")
    task_filter.push(1001,"man",user_name="xiaomin")

    # Demo: specify a string filter (publish method + task_options)
    # Scenario: filter only by user_id; tasks with the same user_id are filtered even if other params differ
    print("Publishing user_id=1001 (1st time)")
    task_filter.publish(
        msg={"user_id": 1001, "user_sex": "man", "user_name": "Tom"},
        task_options=TaskOptions(filter_str="1001")
    )

    print("Publishing user_id=1001 (2nd time, different name, but same filter_str — should be filtered)")
    task_filter.publish(
        msg={"user_id": 1001, "user_sex": "man", "user_name": "Jerry"},
        task_options=TaskOptions(filter_str="1001")
    )


    # --- 8. Delayed task demo ---
    print("\n--- Delay Demo ---")
    print(f"Publish time for delayed task: {datetime.datetime.now()}")
    # Publish using the publish method with task_options
    task_delay.publish(
        msg={"msg": "I am a message delayed by 5 seconds"},
        task_options=TaskOptions(countdown=5)
    )

    # --- 9. Scheduled task demo (APScheduler) ---
    print("\n--- Schedule Demo (triggers every 5 seconds) ---")
    # Note: this schedules a "publish" of the task to the queue, not a direct function call
    ApsJobAdder(task_basic, job_store_kind='memory').add_push_job(
        trigger='interval',
        seconds=5,
        args=(100, 200), # Scheduled to execute task_basic(100, 200)
        id='my_schedule_job'
    )

    # --- 10. Group task publish demo ---
    print("\n--- Group Task Demo ---")
    task_group_a_1.push("A1 data")
    task_group_a_2.push("A2 data")
    task_group_b_1.push("B1 data (this message will not be consumed because group B was not started)")

    # --- 11. Demo of funboost's full asyncio ecosystem: asyncio publish, asyncio consume, asyncio get result
    async def rpc_asyncio():
        aio_async_result:AioAsyncResult = await task_async.aio_push("http://site-1.com") # aio_push returns an AioAsyncResult object
        print("RPC task published, waiting for result in asyncio ecosystem...")
        print(f"aio_async_result RPC Result: {await aio_async_result.result}")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(rpc_asyncio())


    print("\n=== All demo tasks published; ctrl_c_recv puts the main thread into listening state (press Ctrl+C 3 times to exit) ===\n")
    # ctrl_c_recv blocks the main thread to prevent it from exiting, which is recommended because
    # daemon threads would also exit if the main thread ends.
    # Since booster.consume() starts in a child thread, multiple consume() calls can be chained without blocking the main thread.
    ctrl_c_recv()
