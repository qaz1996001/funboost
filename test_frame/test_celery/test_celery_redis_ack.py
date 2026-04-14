



# Celery style
from celery import Celery
import time
import kombu
# Basic configuration is still needed when creating a Celery instance
app = Celery('myapp', broker='redis://localhost:6379/11',backend='redis://localhost:6379/14')
app.conf.task_acks_late = True
app.conf.broker_transport_options = {
    'visibility_timeout': 5 
}
@app.task(name='task_function_name1', queue='my_queue_name1b6')
def task_function(x):
    print(f'task_function {x} starting execution')
    time.sleep(60)
    print(f'task_function {x} execution complete')
    return x 


if __name__ == '__main__':
    

    app.worker_main(
            argv=['worker', '--pool=threads','--concurrency=500', '-n', 'worker1@%h', '--loglevel=INFO',
                '--queues=my_queue_name1b6'
                ])