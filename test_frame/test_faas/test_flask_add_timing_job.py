# -*- coding: utf-8 -*-
"""
Test Flask scheduled task API
Test adding, querying, pausing, resuming, and deleting scheduled tasks
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Flask service address
BASE_URL = "http://localhost:27019"

def test_add_timing_job_date():
    """Test adding a one-time task (date trigger)"""
    print("\n" + "="*60)
    print("Test 1: Add one-time task (date)")
    print("="*60)

    # Set execution time 5 seconds from now
    run_date = (datetime.now() + timedelta(seconds=5)).strftime('%Y-%m-%d %H:%M:%S')

    data = {
        "queue_name": "test_funboost_task3",
        "trigger": "date",
        "job_id": "date_job_test_001",
        "job_store_kind": "redis",
        "replace_existing": True,
        "run_date": run_date,
        "kwargs": {
            "user_id": 123,
            "name": "Zhang San",
            "action": "one-time task test"
        }
    }

    print(f"Request data: {json.dumps(data, indent=2, ensure_ascii=False)}")

    response = requests.post(
        f"{BASE_URL}/funboost/add_timing_job",
        json=data,
        headers={"Content-Type": "application/json"}
    )

    print(f"Response status: {response.status_code}")
    print(f"Response data: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    return response.json()


def test_add_timing_job_interval():
    """Test adding an interval task (interval trigger)"""
    print("\n" + "="*60)
    print("Test 2: Add interval task (interval)")
    print("="*60)

    data = {
        "queue_name": "test_funboost_faas_queue",
        "trigger": "interval",
        "job_id": "interval_job_test_001",
        "job_store_kind": "redis",
        "replace_existing": True,
        "seconds": 10,  # Execute every 10 seconds
        "kwargs": {
            # "user_id": 456,
            # "name": "Li Si",
            # "action": "interval task test"
            "x":8,"y":9
        }
    }

    print(f"Request data: {json.dumps(data, indent=2, ensure_ascii=False)}")

    response = requests.post(
        f"{BASE_URL}/funboost/add_timing_job",
        json=data
    )

    print(f"Response status: {response.status_code}")
    print(f"Response data: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    return response.json()


def test_add_timing_job_cron():
    """Test adding a cron task (cron trigger)"""
    print("\n" + "="*60)
    print("Test 3: Add cron task (cron)")
    print("="*60)

    data = {
        "queue_name": "test_funboost_task3",
        "trigger": "cron",
        "job_id": "cron_job_test_001",
        "job_store_kind": "redis",
        "replace_existing": True,
        "hour": "*/1",  # Execute every hour
        "minute": "0",
        "second": "0",
        "kwargs": {
            "user_id": 789,
            "name": "Wang Wu",
            "action": "Cron task test",
            "tags": ["scheduled", "important"]
        }
    }

    print(f"Request data: {json.dumps(data, indent=2, ensure_ascii=False)}")

    response = requests.post(
        f"{BASE_URL}/funboost/add_timing_job",
        json=data
    )

    print(f"Response status: {response.status_code}")
    print(f"Response data: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    return response.json()


def test_get_timing_jobs(queue_name=None):
    """Test getting task list"""
    print("\n" + "="*60)
    print("Test 4: Get task list")
    print("="*60)

    params = {"job_store_kind": "redis"}
    if queue_name:
        params["queue_name"] = queue_name

    print(f"Request params: {params}")

    response = requests.get(
        f"{BASE_URL}/funboost/get_timing_jobs",
        params=params
    )

    print(f"Response status: {response.status_code}")
    result = response.json()
    print(f"Task count: {len(result.get('data', {}).get('jobs', []))}")
    print(f"Response data: {json.dumps(result, indent=2, ensure_ascii=False)}")

    return result


def test_get_timing_job(job_id, queue_name):
    """Test getting a single task detail"""
    print("\n" + "="*60)
    print("Test 5: Get single task detail")
    print("="*60)

    params = {
        "job_id": job_id,
        "queue_name": queue_name,
        "job_store_kind": "redis"
    }

    print(f"Request params: {params}")

    response = requests.get(
        f"{BASE_URL}/funboost/get_timing_job",
        params=params
    )

    print(f"Response status: {response.status_code}")
    print(f"Response data: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    return response.json()


def test_pause_timing_job(job_id, queue_name):
    """Test pausing a task"""
    print("\n" + "="*60)
    print("Test 6: Pause task")
    print("="*60)

    params = {
        "job_id": job_id,
        "queue_name": queue_name,
        "job_store_kind": "redis"
    }

    print(f"Request params: {params}")

    response = requests.post(
        f"{BASE_URL}/funboost/pause_timing_job",
        params=params
    )

    print(f"Response status: {response.status_code}")
    print(f"Response data: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    return response.json()


def test_resume_timing_job(job_id, queue_name):
    """Test resuming a task"""
    print("\n" + "="*60)
    print("Test 7: Resume task")
    print("="*60)

    params = {
        "job_id": job_id,
        "queue_name": queue_name,
        "job_store_kind": "redis"
    }

    print(f"Request params: {params}")

    response = requests.post(
        f"{BASE_URL}/funboost/resume_timing_job",
        params=params
    )

    print(f"Response status: {response.status_code}")
    print(f"Response data: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    return response.json()


def test_delete_timing_job(job_id, queue_name):
    """Test deleting a task"""
    print("\n" + "="*60)
    print("Test 8: Delete task")
    print("="*60)

    params = {
        "job_id": job_id,
        "queue_name": queue_name,
        "job_store_kind": "redis"
    }

    print(f"Request params: {params}")

    response = requests.delete(
        f"{BASE_URL}/funboost/delete_timing_job",
        params=params
    )

    print(f"Response status: {response.status_code}")
    print(f"Response data: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    return response.json()


def test_delete_all_timing_jobs(queue_name=None):
    """Test deleting all tasks"""
    print("\n" + "="*60)
    print("Test 9: Delete all tasks")
    print("="*60)

    params = {"job_store_kind": "redis"}
    if queue_name:
        params["queue_name"] = queue_name

    print(f"Request params: {params}")

    response = requests.delete(
        f"{BASE_URL}/funboost/delete_all_timing_jobs",
        params=params
    )

    print(f"Response status: {response.status_code}")
    print(f"Response data: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    return response.json()


def run_all_tests():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# Starting Flask scheduled task API tests")
    print("#"*60)

    queue_name = "test_funboost_faas_queue"


    try:
        # 1. Add three types of tasks
        result1 = test_add_timing_job_date()
        time.sleep(0.5)

        result2 = test_add_timing_job_interval()
        time.sleep(0.5)

        result3 = test_add_timing_job_cron()
        time.sleep(0.5)

        # 2. Get all tasks
        test_get_timing_jobs()
        time.sleep(0.5)

        # 3. Get tasks for a specific queue
        test_get_timing_jobs(queue_name)
        time.sleep(0.5)

        # # 4. Get single task detail
        # test_get_timing_job("interval_job_test_001", queue_name)
        # time.sleep(0.5)

        # # 5. Pause task
        # test_pause_timing_job("interval_job_test_001", queue_name)
        # time.sleep(0.5)

        # # 6. Check status after pausing
        # print("\nCheck task list after pausing:")
        # test_get_timing_jobs(queue_name)
        # time.sleep(0.5)

        # # 7. Resume task
        # test_resume_timing_job("interval_job_test_001", queue_name)
        # time.sleep(0.5)

        # # 8. Check status after resuming
        # print("\nCheck task list after resuming:")
        # test_get_timing_jobs(queue_name)
        # time.sleep(0.5)

        # # 9. Delete single task
        # test_delete_timing_job("date_job_test_001", queue_name)
        # time.sleep(0.5)

        # # 10. Check task list after deletion
        # print("\nCheck task list after deleting single task:")
        # test_get_timing_jobs(queue_name)

        # # 11. Delete all tasks (optional, use with caution)
        # # test_delete_all_timing_jobs(queue_name)

        # print("\n" + "#"*60)
        # print("# All tests completed!")
        # print("#"*60)

    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # Run all tests
    # run_all_tests()

    # Or run individual tests
    test_add_timing_job_interval()
    test_get_timing_jobs("test_funboost_faas_queue")
