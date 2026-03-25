
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time
from threading import Thread
# from concurrent.futures import ThreadPoolExecutor
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor,BasePoolExecutor

from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAbleNonDaemon

# ThreadPoolExecutorShrinkAbleNonDaemon


class ThreadPoolExecutorForAps(BasePoolExecutor):
    """
    An executor that runs jobs in a concurrent.futures thread pool.

    Plugin alias: ``threadpool``

    :param max_workers: the maximum number of spawned threads.
    :param pool_kwargs: dict of keyword arguments to pass to the underlying
        ThreadPoolExecutor constructor
    """

    def __init__(self, max_workers=100, pool_kwargs=None):
        pool = ThreadPoolExecutorShrinkAbleNonDaemon(int(max_workers), )
        super().__init__(pool)

executors = {
    'default': ThreadPoolExecutor(10) , # Default thread pool, maximum 10 threads
    'non_daemon': ThreadPoolExecutorForAps(10) , # Default thread pool, maximum 10 threads
}


def job():
    print("Executing task:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def t1():
    while 1:
        time.sleep(10)
        print('sleep 10 seconds')

if __name__ == "__main__":
    t = Thread(target=t1)
    t.start()

    scheduler = BackgroundScheduler(executors=executors)
    
    # Execute every 3 seconds
    scheduler.add_job(job, trigger='interval', seconds=30,executor='non_daemon')

    # Start the scheduler (background thread)
    scheduler.start()

    print("Scheduler started, main thread continuing...")

    
    # try:0
    #     # Main thread can do other things; using sleep here as a simulation
    #     while True:
    #         print("Main thread working...")
    #         time.sleep(5)
    # except (KeyboardInterrupt, SystemExit):
    #     scheduler.shutdown()
    #     print("Scheduler stopped")

