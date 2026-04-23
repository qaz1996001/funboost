# Timing Task API Interface Description

## Overview

FastAPI router now provides complete timing task management interfaces supporting dynamic adding, querying, deleting, pausing, and resuming timing tasks via HTTP API.

## New Interface List

| Interface | Method | Function |
|------|------|------|
| `/funboost/add_timing_job` | POST | Add timing task |
| `/funboost/get_timing_jobs` | GET | Get timing task list |
| `/funboost/delete_timing_job` | DELETE | Delete timing task |
| `/funboost/pause_timing_job` | POST | Pause timing task |
| `/funboost/resume_timing_job` | POST | Resume timing task |

## Timing Trigger Methods

Supports **3 timing trigger methods**, fully compatible with APScheduler:

### 1. date - Execute Once at Specified Time

Execute task once at specified date time.

**Parameters:**
- `run_date`: Run time, format: `"YYYY-MM-DD HH:MM:SS"`

**Example:**
```json
{
  "queue_name": "test_queue",
  "trigger": "date",
  "run_date": "2025-12-03 15:00:00",
  "job_id": "my_date_job",
  "args": [10, 20],
  "job_store_kind": "redis"
}
```

### 2. interval - Fixed Interval Execution

Repeat execute task at fixed time interval.

**Parameters:**
- `weeks`: Weeks
- `days`: Days
- `hours`: Hours
- `minutes`: Minutes
- `seconds`: Seconds

**Example:**
```json
{
  "queue_name": "test_queue",
  "trigger": "interval",
  "seconds": 10,
  "job_id": "my_interval_job",
  "kwargs": {"x": 1, "y": 2},
  "job_store_kind": "redis"
}
```

### 3. cron - Cron Expression Execution

Execute task at scheduled time using cron expression.

**Parameters:**
- `year`: Year (4-digit number)
- `month`: Month (1-12)
- `day`: Date (1-31)
- `week`: Week (1-53)
- `day_of_week`: Day of week (0-6 or mon,tue,wed,thu,fri,sat,sun)
- `hour`: Hour (0-23)
- `minute`: Minute (0-59)
- `second`: Second (0-59)

**Cron Expression Notes:**
- Use `*` for any value
- Use `*/n` for every n units
- Use `a-b` for range
- Use `a,b,c` for multiple values

**Example 1 - Execute daily at 3:30pm:**
```json
{
  "queue_name": "test_queue",
  "trigger": "cron",
  "hour": "15",
  "minute": "30",
  "job_id": "daily_3pm_job",
  "args": [1, 2],
  "job_store_kind": "redis"
}
```

**Example 2 - Execute every 2 hours:**
```json
{
  "queue_name": "test_queue",
  "trigger": "cron",
  "hour": "*/2",
  "minute": "0",
  "job_id": "every_2_hours_job",
  "kwargs": {"x": 10, "y": 20},
  "job_store_kind": "redis"
}
```

**Example 3 - Execute weekdays at 9am:**
```json
{
  "queue_name": "test_queue",
  "trigger": "cron",
  "day_of_week": "mon-fri",
  "hour": "9",
  "minute": "0",
  "job_id": "weekday_morning_job",
  "job_store_kind": "redis"
}
```

## Detailed API Description

### 1. Add Timing Task

**Interface:** `POST /funboost/add_timing_job`

**Request Parameters:**
```json
{
  "queue_name": "Queue name (required)",
  "trigger": "Trigger type: date/interval/cron (required)",
  "job_id": "Task ID (optional, auto-generate if not provided)",
  "job_store_kind": "Storage method: redis/memory (default: redis)",
  "replace_existing": "Replace existing task (default: false)",
  
  "args": [1, 2],  // Position parameters (optional)
  "kwargs": {"x": 1, "y": 2},  // Keyword parameters (optional)
  
  // Provide corresponding parameters based on trigger type
  "run_date": "2025-12-03 15:00:00",  // date trigger
  "seconds": 10,  // interval trigger
  "hour": "15",  // cron trigger
  // ... other parameters
}
```

**Response Example:**
```json
{
  "succ": true,
  "msg": "Timing task added successfully",
  "data": {
    "job_id": "my_job_123",
    "queue_name": "test_queue",
    "trigger": "cron",
    "next_run_time": "2025-12-03 15:00:00+08:00"
  }
}
```

### 2. Get Timing Task List

**Interface:** `GET /funboost/get_timing_jobs`

**Query Parameters:**
- `queue_name`: Queue name (optional, get tasks from all queues if not provided)
- `job_store_kind`: Storage method, `redis` or `memory` (default: redis)

**Response Example:**
```json
{
  "succ": true,
  "msg": "Retrieved successfully",
  "data": {
    "jobs": [
      {
        "job_id": "job1",
        "queue_name": "test_queue",
        "trigger": "cron",
        "next_run_time": "2025-12-03 15:00:00+08:00"
      },
      {
        "job_id": "job2",
        "queue_name": "test_queue",
        "trigger": "interval",
        "next_run_time": "2025-12-03 14:50:10+08:00"
      }
    ],
    "count": 2
  }
}
```

### 3. Delete Timing Task

**Interface:** `DELETE /funboost/delete_timing_job`

**Query Parameters:**
- `job_id`: Task ID (required)
- `queue_name`: Queue name (required)
- `job_store_kind`: Storage method (default: redis)

**Response Example:**
```json
{
  "succ": true,
  "msg": "Timing task my_job_123 deleted successfully",
  "data": null
}
```

### 4. Pause Timing Task

**Interface:** `POST /funboost/pause_timing_job`

**Query Parameters:**
- `job_id`: Task ID (required)
- `queue_name`: Queue name (required)
- `job_store_kind`: Storage method (default: redis)

**Response Example:**
```json
{
  "succ": true,
  "msg": "Timing task my_job_123 paused",
  "data": null
}
```

### 5. Resume Timing Task

**Interface:** `POST /funboost/resume_timing_job`

**Query Parameters:**
- `job_id`: Task ID (required)
- `queue_name`: Queue name (required)
- `job_store_kind`: Storage method (default: redis)

**Response Example:**
```json
{
  "succ": true,
  "msg": "Timing task my_job_123 resumed",
  "data": null
}
```

## Python Usage Example

```python
import requests
import json

base_url = "http://127.0.0.1:8000"

# 1. Add interval task executing every 10 seconds
def add_interval_job():
    url = f"{base_url}/funboost/add_timing_job"
    data = {
        "queue_name": "test_fastapi_router_queue",
        "trigger": "interval",
        "seconds": 10,
        "job_id": "interval_job_10s",
        "kwargs": {"x": 10, "y": 20},
        "job_store_kind": "redis",
        "replace_existing": True
    }
    
    resp = requests.post(url, json=data)
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

# 2. Add cron task executing daily at 3pm
def add_cron_job():
    url = f"{base_url}/funboost/add_timing_job"
    data = {
        "queue_name": "test_fastapi_router_queue",
        "trigger": "cron",
        "hour": "15",
        "minute": "0",
        "job_id": "daily_3pm_job",
        "args": [100, 200],
        "job_store_kind": "redis"
    }
    
    resp = requests.post(url, json=data)
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

# 3. Get all timing tasks
def get_all_jobs():
    url = f"{base_url}/funboost/get_timing_jobs"
    params = {"job_store_kind": "redis"}
    
    resp = requests.get(url, params=params)
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

# 4. Get tasks from specific queue
def get_queue_jobs():
    url = f"{base_url}/funboost/get_timing_jobs"
    params = {
        "queue_name": "test_fastapi_router_queue",
        "job_store_kind": "redis"
    }
    
    resp = requests.get(url, params=params)
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

# 5. Pause task
def pause_job():
    url = f"{base_url}/funboost/pause_timing_job"
    params = {
        "job_id": "interval_job_10s",
        "queue_name": "test_fastapi_router_queue",
        "job_store_kind": "redis"
    }
    
    resp = requests.post(url, params=params)
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

# 6. Resume task
def resume_job():
    url = f"{base_url}/funboost/resume_timing_job"
    params = {
        "job_id": "interval_job_10s",
        "queue_name": "test_fastapi_router_queue",
        "job_store_kind": "redis"
    }
    
    resp = requests.post(url, params=params)
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

# 7. Delete task
def delete_job():
    url = f"{base_url}/funboost/delete_timing_job"
    params = {
        "job_id": "interval_job_10s",
        "queue_name": "test_fastapi_router_queue",
        "job_store_kind": "redis"
    }
    
    resp = requests.delete(url, params=params)
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print("1. Add interval task")
    add_interval_job()
    
    print("\n2. Add cron task")
    add_cron_job()
    
    print("\n3. Get all tasks")
    get_all_jobs()
    
    print("\n4. Pause task")
    pause_job()
    
    print("\n5. Resume task")
    resume_job()
    
    print("\n6. Delete task")
    delete_job()
```

## Precautions

1. **job_store_kind choice**:
   - `redis`: Task persistent storage, survives service restart (recommended)
   - `memory`: In-memory storage, tasks lost on service restart

2. **job_id uniqueness**: Each task's `job_id` must be unique within same queue

3. **replace_existing**: If set to `true`, replaces existing task with same name

4. **Timezone**: Time uses server-configured timezone (FunboostCommonConfig.TIMEZONE)

5. **Parameter Passing**:
   - Use `args` for position parameters: `[1, 2, 3]`
   - Use `kwargs` for keyword parameters: `{"x": 1, "y": 2}`

## Summary

Through these interfaces, you can:
- ✅ Dynamically add various timing task types
- ✅ Query all or specific queue timing tasks
- ✅ Pause/Resume/Delete timing tasks
- ✅ Support date, interval, cron three trigger methods
- ✅ Support redis persistent storage

All operations done via simple HTTP API, no need to restart service! 🚀
