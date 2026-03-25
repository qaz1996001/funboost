"""
Mainly used to test the performance comparison between celery and this framework under the same benchmark.
"""
import asyncio
import threading
import os
import time
from datetime import timedelta

import celery
from celery import platforms
from auto_run_on_remote import run_current_script_on_remote
from funboost_config import Br


# import celery_helper
from kombu import Queue, Exchange

platforms.C_FORCE_ROOT = True
# celery_app = celery.Celery('test_frame.test_celery.test_celery_app')
celery_app = celery.Celery()
class Config2:
    # broker_url = f'redis://:@127.0.0.1:6379/10'  # using redis
    broker_url = funboost_config.REDIS_URL #
    # result_backend = f'redis://:@127.0.0.1:6379/11'  # using redis
    broker_connection_max_retries = 150  # default is 100
    # result_serializer = 'json'
    # task_default_queue = 'default'  # default celery
    # # task_default_rate_limit = '101/s'
    # task_default_routing_key = 'default'
    # task_eager_propagates = False  # default disable
    # task_ignore_result = False
    # task_serializer = 'json'
    # task_time_limit = 70
    # task_soft_time_limit = 60
    # worker_concurrency = 32
    # worker_enable_remote_control = True
    # worker_prefetch_multiplier = 3  # default 4
    # worker_redirect_stdouts_level = 'WARNING'
    # worker_timer_precision = 0.1  # default 1 second
    task_routes = {
        'sum_task': {"queue": "queue_add3", },
        'sub_task': {"queue": 'queue_sub2'},
        'f1': {"queue": 'queue_f1'},
        'sync_fun': {"queue": 'sync_fun_queue'},
    }

    task_queues =[

        Queue('test_pri', Exchange('test_pri'), routing_key='test_pri',
              queue_arguments={'x-max-priority': 5}),
    ]

    # task_reject_on_worker_lost = True # configure these two to allow stopping freely
    # task_acks_late = True


celery_app.config_from_object(Config2)


@celery_app.task(name='sum_task',rate_limit='100/s' )  # REMIND rate_limit can be set here, or at call time like test_task.apply_async(args=(1,2),expires=3)
def add(a, b):
    # print(f'Consuming message {a} + {b}...')
    # time.sleep(100, )  # Simulate blocking for 10 seconds; must use concurrency to bypass.
    print(f'{time.strftime("%H:%M:%S")} Starting calculation {a} + {b} ')
    time.sleep(700)
    print(f'{time.strftime("%H:%M:%S")} Calculation {a} + {b} result is  {a + b}')
    return a + b


@celery_app.task(name='sub_task')
def sub(x, y):
    print(f'Consuming message {x} - {y}...')
    time.sleep(30, )  # Simulate blocking for 10 seconds; must use concurrency to bypass.
    print(f'Calculation {x} - {y} result is  {x - y}')
    return x - y

@celery_app.task(name='sub_task')
def print_hello(x):
    print(f'hello {x}')







@celery.shared_task(name='no_app_task')
def test_shere_deco(x):
    print(x)


@celery_app.task(name='sync_fun')
def sync_fun(x):
    print(f'{os.getpid()}  {threading.get_ident()}')
    asyncio.new_event_loop().run_until_complete(async_fun(x))


async def async_fun(x):
    await asyncio.sleep(10)
    print(f'async_fun {x}')

@celery_app.task(name='test_pri')
def test_priority_task(priority):
    print(priority)

def patch_celery_console(celery_instance:celery.Celery):
    import logging
    from nb_log.handlers import ColorHandler
    logging.StreamHandler = ColorHandler  # Fix celery's ugly color issue

    # Set celery conf config item to enable clickable log jump.
    # print(celery_app.conf)
    celery_instance.conf.worker_task_log_format = '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(message)s'
    celery_instance.conf.worker_log_format = '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(message)s'

    # Disable print redirection; don't want prints converted to celery logs. Configure this.
    celery_instance.conf.worker_redirect_stdouts = False

celery_app.conf.beat_schedule = {
    'add-every-30-seconds': {
        'task': 'sum_task',
        'schedule': timedelta(seconds=2),
        'args': (10000, 20000)
    }}
# celery_helper.auto_register_tasks_and_set_routes()
if __name__ == '__main__':
    """
    Celery can start consuming directly from a Python script. Just run this script. The author strongly dislikes typing commands in cmd.
    """

    """
    celery multi start
     Pool implementation: prefork (default), eventlet,
                        gevent or solo.
    """
    """
    celery_app.worker_main(
        argv=['worker', '--pool=prefork', '--concurrency=100', '-n', 'worker1@%h', '--loglevel=debug',
              '--queues=queue_add', '--detach','--logfile=/pythonlogs/celery_add.log'])
    """
    # queue_add,queue_sub,queue_f1
    # patch_celery_console(celery_app)

    print(celery.__version__)
    # run_current_script_on_remote()
    celery_app.worker_main(
        argv=['worker', '--pool=threads','--concurrency=500', '-n', 'worker1@%h', '--loglevel=DEBUG',
              '--queues=test_pri'])
    import threading

    print(777777777777777)