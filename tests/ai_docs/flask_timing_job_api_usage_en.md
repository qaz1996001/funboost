# Flask Adapter Timing Task Interface Usage Guide

## Overview

Successfully ported all timing task management interfaces from FastAPI adapter to Flask adapter (`flask_adapter.py`). Now can directly use these interfaces in Flask applications.

## Quick Start

### 1. Register Blueprint

Register `flask_blueprint` in your Flask application:

```python
from flask import Flask
from funboost.faas.flask_adapter import flask_blueprint

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Register funboost blueprint
app.register_blueprint(flask_blueprint)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### 2. Access Interfaces

After starting Flask application, can access timing task interfaces through following paths:

- Base path: `http://localhost:5000/funboost`
- Example: `http://localhost:5000/funboost/add_timing_job`

## Interface List

### 1. Add Timing Task

**Interface**: `POST /funboost/add_timing_job`

**Request body example**:

```json
{
    "queue_name": "test_queue",
    "trigger": "interval",
    "seconds": 10,
    "job_id": "my_job_001",
    "job_store_kind": "redis",
    "replace_existing": false
}
```

**Trigger types**:

1. **date** - One-time task
   ```json
   {
       "queue_name": "test_queue",
       "trigger": "date",
       "run_date": "2025-12-15 10:00:00"
   }
   ```

2. **interval** - Execute at intervals
   ```json
   {
       "queue_name": "test_queue",
       "trigger": "interval",
       "minutes": 10
   }
   ```

3. **cron** - Execute at scheduled time
   ```json
   {
       "queue_name": "test_queue",
       "trigger": "cron",
       "hour": "9",
       "minute": "0"
   }
   ```

**Response example**:
```json
{
    "succ": true,
    "msg": "Timing task added successfully",
    "data": {
        "job_id": "my_job_001",
        "queue_name": "test_queue",
        "trigger": "interval",
        "next_run_time": "2025-12-11 16:40:00"
    }
}
```

### 2. Get Timing Task List

**Interface**: `GET /funboost/get_timing_jobs`

**Query parameters**:
- `queue_name` (optional): Queue name, omit to get tasks from all queues
- `job_store_kind` (optional): Storage type, default `redis`

**Request examples**:
```bash
# Get all tasks
GET /funboost/get_timing_jobs

# Get tasks from specific queue
GET /funboost/get_timing_jobs?queue_name=test_queue

# Specify storage type
GET /funboost/get_timing_jobs?job_store_kind=redis
```

**Response example**:
```json
{
    "succ": true,
    "msg": "Retrieved successfully",
    "data": {
        "jobs": [
            {
                "job_id": "my_job_001",
                "queue_name": "test_queue",
                "trigger": "interval[0:00:10]",
                "next_run_time": "2025-12-11 16:40:00"
            }
        ],
        "count": 1
    }
}
```

### 3. Get Single Task Details

**Interface**: `GET /funboost/get_timing_job`

**Query parameters**:
- `job_id` (required): Task ID
- `queue_name` (required): Queue name
- `job_store_kind` (optional): Storage type, default `redis`

**Request example**:
```bash
GET /funboost/get_timing_job?job_id=my_job_001&queue_name=test_queue
```

**Response example**:
```json
{
    "succ": true,
    "msg": "Retrieved successfully",
    "data": {
        "job_id": "my_job_001",
        "queue_name": "test_queue",
        "trigger": "interval[0:00:10]",
        "next_run_time": "2025-12-11 16:40:00"
    }
}
```

### 4. Delete Timing Task

**Interface**: `DELETE /funboost/delete_timing_job`

**Query parameters**:
- `job_id` (required): Task ID
- `queue_name` (required): Queue name
- `job_store_kind` (optional): Storage type, default `redis`

**Request example**:
```bash
DELETE /funboost/delete_timing_job?job_id=my_job_001&queue_name=test_queue
```

**Response example**:
```json
{
    "succ": true,
    "msg": "Timing task my_job_001 deleted successfully",
    "data": null
}
```

### 5. Delete All Tasks

**Interface**: `DELETE /funboost/delete_all_timing_jobs`

**Query parameters**:
- `queue_name` (optional): Queue name, omit to delete tasks from all queues
- `job_store_kind` (optional): Storage type, default `redis`

**Request examples**:
```bash
# Delete all tasks from all queues
DELETE /funboost/delete_all_timing_jobs

# Delete all tasks from specific queue
DELETE /funboost/delete_all_timing_jobs?queue_name=test_queue
```

**Response example**:
```json
{
    "succ": true,
    "msg": "Successfully deleted 5 timing tasks",
    "data": {
        "deleted_count": 5,
        "failed_jobs": []
    }
}
```

### 6. Pause Timing Task

**Interface**: `POST /funboost/pause_timing_job`

**Query parameters**:
- `job_id` (required): Task ID
- `queue_name` (required): Queue name
- `job_store_kind` (optional): Storage type, default `redis`

**Request example**:
```bash
POST /funboost/pause_timing_job?job_id=my_job_001&queue_name=test_queue
```

**Response example**:
```json
{
    "succ": true,
    "msg": "Timing task my_job_001 paused",
    "data": null
}
```

### 7. Resume Timing Task

**Interface**: `POST /funboost/resume_timing_job`

**Query parameters**:
- `job_id` (required): Task ID
- `queue_name` (required): Queue name
- `job_store_kind` (optional): Storage type, default `redis`

**Request example**:
```bash
POST /funboost/resume_timing_job?job_id=my_job_001&queue_name=test_queue
```

**Response example**:
```json
{
    "succ": true,
    "msg": "Timing task my_job_001 resumed",
    "data": null
}
```

## Testing with curl

### Add task
```bash
curl -X POST http://localhost:5000/funboost/add_timing_job \
  -H "Content-Type: application/json" \
  -d '{
    "queue_name": "test_queue",
    "trigger": "interval",
    "seconds": 10
  }'
```

### Query task list
```bash
curl http://localhost:5000/funboost/get_timing_jobs
```

### Delete task
```bash
curl -X DELETE "http://localhost:5000/funboost/delete_timing_job?job_id=my_job_001&queue_name=test_queue"
```

## Python Call Example

```python
import requests

BASE_URL = "http://localhost:5000/funboost"

# 1. Add timing task
def add_job():
    url = f"{BASE_URL}/add_timing_job"
    data = {
        "queue_name": "test_queue",
        "trigger": "interval",
        "seconds": 10,
        "job_id": "my_test_job"
    }
    response = requests.post(url, json=data)
    print(response.json())

# 2. Get task list
def get_jobs():
    url = f"{BASE_URL}/get_timing_jobs"
    params = {"queue_name": "test_queue"}
    response = requests.get(url, params=params)
    print(response.json())

# 3. Delete task
def delete_job(job_id, queue_name):
    url = f"{BASE_URL}/delete_timing_job"
    params = {
        "job_id": job_id,
        "queue_name": queue_name
    }
    response = requests.delete(url, params=params)
    print(response.json())

if __name__ == "__main__":
    add_job()
    get_jobs()
    # delete_job("my_test_job", "test_queue")
```

## Precautions

1. **Queue must exist**: Before adding timing task, ensure queue is registered via `@boost` decorator
2. **Storage method**: 
   - `redis`: Supports distribution, task persistence (recommended for production)
   - `memory`: Memory storage only, tasks lost on process restart
3. **Task ID**: If not specified `job_id`, system auto-generates unique ID
4. **Trigger parameters**: Different trigger types require different parameters, see interface documentation

## Related Interfaces

Besides timing task interfaces, Flask adapter also provides following interfaces:

- `POST /funboost/publish` - Publish message
- `GET /funboost/get_result` - Get task result
- `GET /funboost/get_msg_count` - Get queue message count
- `GET /funboost/get_all_queues` - Get all queues

Complete interfaces can be understood by viewing `flask_adapter.py` source code.

## More Information

- Source location: `funboost/faas/flask_adapter.py`
- Timing task core: `funboost/timing_job/timing_push.py`
- APScheduler documentation: https://apscheduler.readthedocs.io/
