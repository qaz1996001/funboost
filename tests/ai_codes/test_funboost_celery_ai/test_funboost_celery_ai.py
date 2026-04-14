import time
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv
from funboost.assist.celery_helper import CeleryHelper

@boost(BoosterParams(
    queue_name="funboost_celery_queue",
    broker_kind=BrokerEnum.CELERY,
    qps=5,
    max_retry_times=3,
))
def celery_task(user_id: int, message: str):
    """Task function using Celery as the broker"""
    print(f"Processing message for user {user_id}: {message}")
    time.sleep(1)  # Simulate processing time
    return f"Message processing complete for user {user_id}"

@boost(BoosterParams(
    queue_name="funboost_celery_queue2",
    broker_kind=BrokerEnum.CELERY
))
def another_celery_task(data: dict):
    """Another task function using Celery as the broker"""
    print(f"Processing data: {data}")
    time.sleep(0.5)  # Simulate processing time
    return f"Data processing complete: {data['key']}"

if __name__ == '__main__':
    print("=== Starting consumers ===")
    # Start consumers for both tasks
    celery_task.consume()
    another_celery_task.consume()

    print("=== Publishing tasks ===")
    # Publish multiple tasks
    for i in range(10):
        # Use push method to publish tasks
        result = celery_task.push(user_id=i, message=f"Hello Funboost {i}")
        print(f"Published task {i}, task ID: {result.task_id if hasattr(result, 'task_id') else 'N/A'}")

        # Publish a task to the second queue
        another_celery_task.push(data={"key": f"value_{i}", "timestamp": time.time()})

    print("=== Starting Celery Worker and Flower ===")
    # Start Flower monitoring (optional)
    CeleryHelper.start_flower()

    # Start Celery Worker
    # Note: In actual production, you may want to start Celery Worker in a separate process.
    # Here, for demonstration purposes, we start it in the current process.
    # Important: Celery worker concurrency is a global setting, not per-task.
    # You can set the concurrency via worker_concurrency, default is 200.
    # Example: CeleryHelper.realy_start_celery_worker(worker_concurrency=10)
    CeleryHelper.realy_start_celery_worker()
