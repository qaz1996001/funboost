"""
This demonstrates the funboost.faas scheduled task management.
"""


import requests

# Add a task that runs every 10 seconds
resp = requests.post("http://127.0.0.1:8000/funboost/add_timing_job", json={
    "queue_name": "test_funboost_faas_queue",
    "trigger": "interval",
    "seconds": 10,
    "job_id": "my_job",
    "kwargs": {"x": 10, "y": 20},
    "job_store_kind": "redis",
    "replace_existing": True,
})
print('add_timing_job',resp.json())

# Get all jobs
resp = requests.get("http://127.0.0.1:8000/funboost/get_timing_jobs")
print('get_timing_jobs',resp.json())

# Pause a job
resp = requests.post("http://127.0.0.1:8000/funboost/pause_timing_job",
    params={"job_id": "my_job", "queue_name": "test_funboost_faas_queue"})
print('pause_timing_job',resp.json())

# # Resume a job
# resp = requests.post("http://127.0.0.1:8000/funboost/resume_timing_job",
#     params={"job_id": "my_job", "queue_name": "test_funboost_faas_queue"})
# print('resume_timing_job',resp.json())
