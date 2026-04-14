# -*- coding: utf-8 -*-
"""
Funboost Comprehensive Capability Demo
Demonstrates: basic consumption, RPC result retrieval, QPS frequency control, concurrency mode, delayed tasks, workflow orchestration
"""
import time
from funboost import boost, BrokerEnum, ctrl_c_recv, ConcurrentModeEnum
from funboost.timing_job.timing_push import ApsJobAdder
from funboost.workflow import chain


@boost(queue_name='demo_basic', broker_kind=BrokerEnum.REDIS, concurrent_num=5)
def basic_task(name: str, count: int):
    """Basic task: demonstrates simple publish-consume pattern"""
    time.sleep(0.5)
    print(f'[Basic task] {name} - Execution #{count}')
    return f'{name}_done_{count}'


@boost(queue_name='demo_rpc', broker_kind=BrokerEnum.REDIS, concurrent_num=3, is_using_rpc_mode=True)
def rpc_task(x: int, y: int):
    """RPC task: demonstrates getting consumption result"""
    time.sleep(0.3)
    result = x * y
    print(f'[RPC task] {x} * {y} = {result}')
    return result


@boost(queue_name='demo_qps', broker_kind=BrokerEnum.REDIS, concurrent_num=10, qps=2)
def qps_limited_task(data: str):
    """QPS frequency-controlled task: precisely control executions per second"""
    print(f'[QPS control] Processing data: {data}, time: {time.strftime("%H:%M:%S")}')


@boost(queue_name='demo_concurrent', broker_kind=BrokerEnum.REDIS, concurrent_num=8, concurrent_mode=ConcurrentModeEnum.THREADING)
def concurrent_task(task_id: int):
    """Concurrent task: demonstrates multi-threaded concurrent execution"""
    time.sleep(1)
    print(f'[Concurrent task] Task {task_id} completed in thread')


@boost(queue_name='demo_delay', broker_kind=BrokerEnum.REDIS, concurrent_num=3)
def delay_task(msg: str):
    """Delayed task: demonstrates delayed message consumption"""
    print(f'[Delayed task] Received message: {msg}, current time: {time.strftime("%H:%M:%S")}')


@boost(queue_name='demo_workflow', broker_kind=BrokerEnum.REDIS, concurrent_num=3)
def workflow_step(step_name: str, data: int = 0):
    """Workflow step function"""
    result = data + 10
    print(f'[Workflow] {step_name}: input={data}, output={result}')
    return result


def demo_basic():
    """Demo 1: Basic publish-consume"""
    print('\n' + '=' * 50)
    print('Demo 1: Basic publish-consume pattern')
    print('=' * 50)
    basic_task.consume()
    for i in range(3):
        basic_task.push('Task A', i + 1)


def demo_rpc():
    """Demo 2: RPC mode to get results"""
    print('\n' + '=' * 50)
    print('Demo 2: RPC mode - synchronously get consumption results')
    print('=' * 50)
    rpc_task.consume()

    result1 = rpc_task.push(3, 7)
    print(f'Waiting for result1: 3 * 7 = {result1.result}')

    result2 = rpc_task.push(10, 20)
    print(f'Waiting for result2: 10 * 20 = {result2.result}')


def demo_qps():
    """Demo 3: Precise QPS frequency control"""
    print('\n' + '=' * 50)
    print('Demo 3: QPS frequency control - maximum 2 executions per second')
    print('=' * 50)
    qps_limited_task.consume()

    print('Quickly publishing 10 messages, observe consumption speed...')
    for i in range(10):
        qps_limited_task.push(f'data_{i}')


def demo_concurrent():
    """Demo 4: Multi-threaded concurrency"""
    print('\n' + '=' * 50)
    print('Demo 4: 8-thread concurrent execution')
    print('=' * 50)
    concurrent_task.consume()

    start = time.time()
    for i in range(8):
        concurrent_task.push(i + 1)
    print('8 tasks published, expected to complete in about 1 second (concurrent execution)')


def demo_delay():
    """Demo 5: Delayed tasks"""
    print('\n' + '=' * 50)
    print('Demo 5: Delayed task - consumed after 5 seconds')
    print('=' * 50)
    delay_task.consume()

    print(f'Current time: {time.strftime("%H:%M:%S")}')
    delay_task.push('This is a message delayed by 5 seconds', delay_seconds=5)
    print('Message published, will be consumed after 5 seconds')


def demo_workflow():
    """Demo 6: Workflow orchestration"""
    print('\n' + '=' * 50)
    print('Demo 6: Workflow orchestration - Chain sequential execution')
    print('=' * 50)
    workflow_step.consume()

    wf = chain(
        workflow_step.s('Step 1', 0),
        workflow_step.s('Step 2'),
        workflow_step.s('Step 3'),
    )
    wf.apply()
    print('Workflow submitted, observe chain execution effect')


def demo_timer():
    """Demo 7: Scheduled tasks"""
    print('\n' + '=' * 50)
    print('Demo 7: Scheduled task - execute every 3 seconds')
    print('=' * 50)
    basic_task.consume()

    ApsJobAdder(basic_task, job_store_kind='memory').add_push_job(
        trigger='interval',
        seconds=3,
        args=('Scheduled task', 999)
    )
    print('Scheduled task added, auto-published every 3 seconds')


if __name__ == '__main__':
    print('\n' + '#' * 60)
    print('#  Funboost Comprehensive Capability Demo')
    print('#  Demonstrates: basic consumption, RPC, QPS control, concurrency, delays, workflows')
    print('#' * 60)

    demo_basic()
    demo_rpc()
    demo_qps()
    demo_concurrent()
    demo_delay()
    demo_workflow()
    demo_timer()

    print('\n' + '=' * 50)
    print('All demos started, press Ctrl+C to exit...')
    print('=' * 50)
    ctrl_c_recv()
