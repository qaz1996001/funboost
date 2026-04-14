# run_background_worker.py
import time
from funboost import ApsJobAdder, ctrl_c_recv
from tasks import dynamic_task  # Import the task function

if __name__ == '__main__':

    print("--- Background Worker and Scheduled Dispatcher ---")
    print("Starting...")

    # 1. Start the consumer to begin listening on the 'web_dynamic_task_queue' queue
    dynamic_task.consume()
    print("[Worker] Consumer started, waiting for tasks...")

    # 2. Create an ApsJobAdder instance and start it.
    #    - job_store_kind='redis' ensures it can read the plans added by the Web side.
    #    - is_auto_start=True (or omitted; default is True) automatically starts the apscheduler background loop.
    # This instance continuously scans Redis and pushes due tasks to the message queue.
    ApsJobAdder(dynamic_task, job_store_kind='redis')
    print("[Scheduler] Scheduled task dispatcher started, scanning task plans...")

    print("\nBackground service is ready. Press Ctrl+C to exit.")
    ctrl_c_recv()
