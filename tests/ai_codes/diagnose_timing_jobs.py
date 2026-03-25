# -*- coding: utf-8 -*-
"""
Timing job diagnostic script - Check APScheduler Redis JobStore status
"""

from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter, QueuesConusmerParamsGetter
from funboost.timing_job.timing_push import ApsJobAdder
from funboost.utils import redis_manager
from funboost.constant import RedisKeys
import json

def diagnose_timing_jobs(queue_name=None):
    """Diagnose timing job status"""

    print("="*60)
    print("Timing Job Diagnostic Report")
    print("="*60)

    # 1. Check all queues
    all_queues = list(QueuesConusmerParamsGetter().get_all_queue_names())
    print(f"\n📋 Number of registered queues: {len(all_queues)}")
    print(f"Queue list: {all_queues}")

    # 2. Check jobs in Redis
    redis_conn = redis_manager.get_redis_connection()

    if queue_name:
        queues_to_check = [queue_name]
    else:
        queues_to_check = all_queues

    print(f"\n🔍 Checking queues: {queues_to_check}\n")

    for q_name in queues_to_check:
        print(f"\n{'─'*60}")
        print(f"Queue: {q_name}")
        print(f"{'─'*60}")

        # Check jobs_key in Redis
        jobs_key = RedisKeys.gen_funboost_redis_apscheduler_jobs_key_by_queue_name(q_name)
        run_times_key = RedisKeys.gen_funboost_redis_apscheduler_run_times_key_by_queue_name(q_name)
        lock_key = RedisKeys.gen_funboost_apscheduler_redis_lock_key_by_queue_name(q_name)

        print(f"📌 Redis Keys:")
        print(f"   Jobs Key: {jobs_key}")
        print(f"   Run Times Key: {run_times_key}")
        print(f"   Lock Key: {lock_key}")

        # Check if there are jobs in Redis
        jobs_in_redis = redis_conn.hgetall(jobs_key)
        run_times_in_redis = redis_conn.zrange(run_times_key, 0, -1, withscores=True)

        print(f"\n📊 Redis storage status:")
        print(f"   Jobs count: {len(jobs_in_redis)}")
        print(f"   Run Times count: {len(run_times_in_redis)}")

        if jobs_in_redis:
            print(f"\n   Jobs details:")
            for job_id, job_data in jobs_in_redis.items():
                print(f"     - Job ID: {job_id.decode() if isinstance(job_id, bytes) else job_id}")
                try:
                    import pickle
                    job_obj = pickle.loads(job_data)
                    print(f"       Trigger: {job_obj.trigger}")
                    print(f"       Next run: {job_obj.next_run_time}")
                except Exception as e:
                    print(f"       (Unable to parse: {e})")

        # 3. Check if tasks can be retrieved via ApsJobAdder
        try:
            booster = SingleQueueConusmerParamsGetter(q_name).gen_booster_for_faas()
            job_adder = ApsJobAdder(booster, job_store_kind='redis', is_auto_start=True)

            jobs = job_adder.aps_obj.get_jobs()

            print(f"\n🔄 Jobs retrieved by APScheduler:")
            print(f"   Job count: {len(jobs)}")

            for job in jobs:
                print(f"\n   ➤ Job ID: {job.id}")
                print(f"     Trigger: {job.trigger}")
                print(f"     Next run: {job.next_run_time}")
                print(f"     Status: {'Paused' if job.next_run_time is None else 'Running'}")
                if hasattr(job, 'kwargs') and job.kwargs:
                    print(f"     Args: {job.kwargs}")

            # Check scheduler status
            print(f"\n⚙️  APScheduler status:")
            print(f"   Is running: {job_adder.aps_obj.running}")
            print(f"   State: {job_adder.aps_obj.state}")

        except Exception as e:
            print(f"\n❌ Failed to retrieve jobs: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print("Diagnosis complete")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    # Diagnose all queues
    diagnose_timing_jobs()

    # Or diagnose a specific queue
    # diagnose_timing_jobs('test_funboost_task3')
