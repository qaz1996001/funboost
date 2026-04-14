# -*- coding: utf-8 -*-
"""
Diagnose the issue of failing to add a task on the page
Directly call backend code to simulate a page request
"""

from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter
from funboost.timing_job.timing_push import ApsJobAdder
from funboost.utils import redis_manager
from funboost.constant import RedisKeys
import traceback

def test_add_job_directly():
    """Directly call Python code to add a task"""
    print("="*60)
    print("Test 1: Directly use Python code to add a task")
    print("="*60)

    queue_name = "test_funboost_faas_queue"
    job_id = "python_direct_test"

    try:
        # Get booster
        booster = SingleQueueConusmerParamsGetter(queue_name)\
            .gen_booster_for_faas()

        # Create ApsJobAdder
        job_adder = ApsJobAdder(booster, job_store_kind='redis', is_auto_start=True)

        print(f"Scheduler object: {job_adder.aps_obj}")
        print(f"Scheduler ID: {id(job_adder.aps_obj)}")
        print(f"Job count before adding: {len(job_adder.aps_obj.get_jobs())}")

        # Add task
        job = job_adder.add_push_job(
            trigger='interval',
            seconds=15,
            kwargs={"test": "from_python"},
            id=job_id,
            replace_existing=True
        )

        print(f"\n✅ Task added successfully:")
        print(f"   Job ID: {job.id}")
        print(f"   Trigger: {job.trigger}")
        print(f"   Next Run: {job.next_run_time}")

        # Query immediately
        print(f"\nJob count after adding: {len(job_adder.aps_obj.get_jobs())}")

        # Check Redis
        redis_conn = redis_manager.get_redis_connection()
        jobs_key = RedisKeys.gen_funboost_redis_apscheduler_jobs_key_by_queue_name(queue_name)
        jobs_in_redis = redis_conn.hgetall(jobs_key)

        print(f"\nJobs in Redis:")
        print(f"   Jobs Key: {jobs_key}")
        print(f"   Job count: {len(jobs_in_redis)}")
        print(f"   Job IDs: {[k.decode() if isinstance(k, bytes) else k for k in jobs_in_redis.keys()]}")

        return True

    except Exception as e:
        print(f"\n❌ Failed to add: {e}")
        traceback.print_exc()
        return False


def test_add_job_via_flask_api():
    """Simulate the processing logic of a Flask route"""
    print("\n" + "="*60)
    print("Test 2: Simulate Flask API processing logic")
    print("="*60)

    # Simulate data submitted from the frontend
    data = {
        "queue_name": "test_funboost_faas_queue",
        "trigger": "interval",
        "job_id": "flask_simulation_test",
        "job_store_kind": "redis",
        "replace_existing": True,
        "seconds": 20,
        "kwargs": {
            "test": "from_flask_simulation"
        }
    }

    print(f"Simulated request data: {data}\n")

    try:
        queue_name = data.get('queue_name')
        trigger = data.get('trigger')
        job_id = data.get('job_id')
        job_store_kind = data.get('job_store_kind', 'redis')
        replace_existing = data.get('replace_existing', False)

        # Get booster
        booster = SingleQueueConusmerParamsGetter(queue_name)\
            .gen_booster_for_faas()
        job_adder = ApsJobAdder(booster, job_store_kind=job_store_kind, is_auto_start=True)

        print(f"Scheduler object: {job_adder.aps_obj}")
        print(f"Scheduler ID: {id(job_adder.aps_obj)}")
        print(f"Job count before adding: {len(job_adder.aps_obj.get_jobs())}")

        # Build trigger arguments (same as flask_adapter.py)
        trigger_args = {}

        if trigger == 'interval':
            if data.get('weeks') is not None:
                trigger_args['weeks'] = data.get('weeks')
            if data.get('days') is not None:
                trigger_args['days'] = data.get('days')
            if data.get('hours') is not None:
                trigger_args['hours'] = data.get('hours')
            if data.get('minutes') is not None:
                trigger_args['minutes'] = data.get('minutes')
            if data.get('seconds') is not None:
                trigger_args['seconds'] = data.get('seconds')

        print(f"\ntrigger_args: {trigger_args}")

        # Add task
        job = job_adder.add_push_job(
            trigger=trigger,
            args=data.get('args'),
            kwargs=data.get('kwargs'),
            id=job_id,
            replace_existing=replace_existing,
            **trigger_args
        )

        print(f"\n✅ Task added successfully:")
        print(f"   Job ID: {job.id}")
        print(f"   Trigger: {job.trigger}")
        print(f"   Next Run: {job.next_run_time}")

        # Query immediately
        print(f"\nJob count after adding: {len(job_adder.aps_obj.get_jobs())}")

        # Check Redis
        redis_conn = redis_manager.get_redis_connection()
        jobs_key = RedisKeys.gen_funboost_redis_apscheduler_jobs_key_by_queue_name(queue_name)
        jobs_in_redis = redis_conn.hgetall(jobs_key)

        print(f"\nJobs in Redis:")
        print(f"   Jobs Key: {jobs_key}")
        print(f"   Job count: {len(jobs_in_redis)}")
        print(f"   Job IDs: {[k.decode() if isinstance(k, bytes) else k for k in jobs_in_redis.keys()]}")

        return True

    except Exception as e:
        print(f"\n❌ Failed to add: {e}")
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Run tests
    result1 = test_add_job_directly()
    result2 = test_add_job_via_flask_api()

    print("\n" + "="*60)
    print("Test Results:")
    print(f"  Test 1 (Python Direct): {'✅ Success' if result1 else '❌ Failed'}")
    print(f"  Test 2 (Simulate Flask): {'✅ Success' if result2 else '❌ Failed'}")
    print("="*60)
