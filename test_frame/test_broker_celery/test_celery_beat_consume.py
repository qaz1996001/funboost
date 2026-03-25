from celery.schedules import crontab
from datetime import timedelta
import time

from funboost import boost, BrokerEnum
from funboost.consumers.celery_consumer import CeleryHelper


@boost('celery_beat_queue_7a2b6', broker_kind=BrokerEnum.CELERY,
       # qps=5
       )
def f_beat(x, y):
    time.sleep(3)
    print(1111, x, y)
    return x + y


@boost('celery_beat_queueb_8a2b6', broker_kind=BrokerEnum.CELERY, qps=1, broker_exclusive_config={'celery_task_config': {'default_retry_delay': 60 * 5}})
def f_beat2(a, b):
    time.sleep(2)
    print(2222, a, b)
    return a - b


beat_schedule = {  # This is 100% pure celery scheduled task configuration style
    'add-every-10-seconds_job': {
        'task': f_beat.queue_name,
        'schedule': timedelta(seconds=10),
        'args': (10000, 20000),
    },
    'celery_beat_queueb_8_jobxx': {
        'task': f_beat2.queue_name,
        'schedule': timedelta(seconds=20),
        # 'schedule': crontab(minute=30, hour=16),
        'kwargs': {'a': 20, 'b': 30}
    }

}

if __name__ == '__main__':
    f_beat2(a=6, b=2)
    for i in range(10):
        f_beat.push(i, i * 2)
        f_beat2.push(i, i * 10)
    CeleryHelper.start_flower(port=5556)  # Start flower web UI; this function can also be started in a separate script
    CeleryHelper.celery_start_beat(beat_schedule)  # Configure and start scheduled tasks; this can also run in a separate script, but the script must first import the module containing @boost-decorated functions, since the consumer's custom_init registers celery task routing during @boost, enabling scheduled tasks to be sent to the correct message queue.
    print(CeleryHelper.celery_app.conf)
    CeleryHelper.show_celery_app_conf()
    f_beat.consume()  # Register f_beat for consumption; this registers the function with the celery worker, actual worker startup requires realy_start_celery_worker, which starts all registered functions at once
    # f_beat2.consume()  # Register f_beat2 for consumption; this registers the function with the celery worker, actual worker startup requires realy_start_celery_worker, which starts all registered functions at once
    CeleryHelper.realy_start_celery_worker(worker_name='test_worker_ah')  # This actually starts the celery worker function consumer.
    print('Code after batch_start_celery_consumers() will not be executed')
