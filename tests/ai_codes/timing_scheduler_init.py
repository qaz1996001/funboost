# -*- coding: utf-8 -*-
"""
Initialize APScheduler schedulers when a Flask application starts up
Ensure that Redis JobStore schedulers for all queues start correctly
"""

from funboost.core.active_cousumer_info_getter import QueuesConusmerParamsGetter, SingleQueueConusmerParamsGetter
from funboost.timing_job.timing_push import ApsJobAdder
from funboost import logger_getter

logger = logger_getter.get_logger('timing_jobs_init')

# Global dict storing initialized schedulers
_initialized_schedulers = {}

def init_all_timing_schedulers():
    """
    Initialize timing job schedulers for all queues
    Should be called once when the Flask application starts
    """
    logger.info("Starting initialization of timing job schedulers...")

    all_queues = list(QueuesConusmerParamsGetter().get_all_queue_names())
    logger.info(f"Found {len(all_queues)} queues")

    for queue_name in all_queues:
        try:
            # Create a Redis-mode scheduler for each queue
            booster = SingleQueueConusmerParamsGetter(queue_name)\
                .gen_booster_for_faas()

            # Create and start scheduler
            job_adder = ApsJobAdder(booster, job_store_kind='redis', is_auto_start=True)

            # Check for existing jobs
            jobs = job_adder.aps_obj.get_jobs()

            _initialized_schedulers[queue_name] = job_adder.aps_obj

            logger.info(f"✓ Scheduler for queue '{queue_name}' started, current job count: {len(jobs)}")

        except Exception as e:
            logger.error(f"✗ Scheduler initialization failed for queue '{queue_name}': {e}")

    logger.info(f"Timing job scheduler initialization complete, {len(_initialized_schedulers)} scheduler(s) running")

    return _initialized_schedulers


def get_scheduler_for_queue(queue_name, job_store_kind='redis'):
    """
    Get the scheduler for a specific queue
    Creates one if it does not exist
    """
    if job_store_kind == 'redis':
        key = queue_name
        if key not in _initialized_schedulers:
            try:
                booster = SingleQueueConusmerParamsGetter(queue_name)\
                    .gen_booster_for_faas()
                job_adder = ApsJobAdder(booster, job_store_kind='redis', is_auto_start=True)
                _initialized_schedulers[key] = job_adder.aps_obj
                logger.info(f"Created new scheduler: {queue_name}")
            except Exception as e:
                logger.error(f"Failed to create scheduler {queue_name}: {e}")
                raise

        return _initialized_schedulers[key]
    else:
        # memory mode uses global scheduler
        from funboost.timing_job.timing_job_base import funboost_aps_scheduler
        return funboost_aps_scheduler


# Example of calling in app.py:
if __name__ == '__main__':
    # Test initialization
    init_all_timing_schedulers()

    import time
    print("\\nSchedulers running, press Ctrl+C to exit...")
    try:
        while True:
            time.sleep(60)
            # Periodically check scheduler status
            for queue_name, scheduler in _initialized_schedulers.items():
                jobs = scheduler.get_jobs()
                print(f"Queue {queue_name}: {len(jobs)} job(s) running")
    except KeyboardInterrupt:
        print("\\nStopping schedulers...")
