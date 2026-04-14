
"""
This script demonstrates funboost using celery as a broker.
Users can still use celery's low-level details in addition to funboost's unified API.
"""
import time
from funboost import boost, BrokerEnum, BoosterParams
from funboost.assist.celery_helper import CeleryHelper, Task

@boost(BoosterParams(queue_name='test_broker_celery_simple',
                     broker_kind=BrokerEnum.CELERY,  # Use the celery framework as funboost's broker
                     concurrent_num=10,))
def my_fun(x, y):
    time.sleep(3)
    print(6666, x, y)
    return x + y

if __name__ == '__main__':
    # Publish messages using funboost syntax; my_fun type is funboost Booster
    my_fun.push(1, 2)

    # Users can publish messages via my_fun.consumer.celery_task using celery's built-in delay
    # my_fun.consumer.celery_task type is celery's celery.app.task.Task
    my_fun_celery_task: Task = my_fun.consumer.celery_task
    my_fun_celery_task.delay(3, 4)  # Can use celery task's native delay
    my_fun_celery_task.apply_async(args=[5, 6], task_id='123456789123', countdown=10)  # Can use celery task's native apply_async

    my_fun.consume()  # This does not start consuming immediately; it registers the queue to be started by celery
    CeleryHelper.realy_start_celery_worker()  # This actually starts the celery worker command line to consume all registered queues
