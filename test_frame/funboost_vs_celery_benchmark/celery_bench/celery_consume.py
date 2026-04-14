from celery import Celery
import datetime
# Create Celery instance, set broker and backend
app = Celery('namexx',
             broker='redis://localhost:6379/0',
)

# Define a simple print task
@app.task(name='print_number',queue='test_queue_celery02')
def print_number(i):
    if  i % 1000 == 0:
        print(f"{datetime.datetime.now()} current number is: {i}")
    return i  # Return result for easy viewing of task execution status

# If you need to call this task from the main program, use it like this:
# Synchronous call: print_number.delay(42)
# Async result: result = print_number.delay(42); print(result.get())



if __name__ == '__main__':
    # Start worker directly in Python, not using command line
    # Use --pool=solo parameter to ensure single-threaded mode
    app.worker_main(['worker', '--loglevel=info', '--pool=solo','--queues=test_queue_celery02'])


'''
Tested on win11 + python3.9 + celery 5 + redis middleware + amd r7 5800h cpu + single-thread concurrency mode

Celery consumption performance test results:

Celery consumes 1000 messages on average every 3.6 seconds, capable of consuming 300 messages per second


'''