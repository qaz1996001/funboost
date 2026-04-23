# funboost FaaS (Function as a Service) Example

This example demonstrates how to use funboost FaaS.

```
funboost FaaS can be deployed and started as a standalone consumer. Users can start the booster
together with their web application, or start the consumer independently.

Because funboost.faas is driven by metadata that funboost registers into Redis, it can
dynamically discover boosters. As long as the consumer function is deployed and online,
the web service requires no restart — it is immediately callable via the HTTP interface.
Compared to traditional web development where adding a feature means adding a new endpoint
and restarting the web server, funboost FaaS is a breath of fresh air.
```


## 📁 File Descriptions

### 1. `task_funs_dir` - Task Function Definition Folder

**Purpose**: Defines the consumer functions (task functions) to be managed by Funboost

`Project1BoosterParams` is a subclass of `BoosterParams`. Each consumer function can use this
subclass directly to avoid repeating the same parameters in every decorator.




### 2. `example_fastapi_faas.py` - FastAPI Application Entry Point

**Purpose**: The main program for the FastAPI application, demonstrating how to integrate Funboost
routing in a single step to implement FaaS

Runs the Uvicorn server


**Core code**:
```python
from funboost.faas import fastapi_router,CareProjectNameEnv

CareProjectNameEnv.set('test_project1') # Optional: only watch queues under the test_project1 project

app = FastAPI()
app.include_router(fastapi_router)  # Core usage: integrate with one line of code



if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Access URLs**:
- API docs: http://127.0.0.1:8000/docs
- Root path: http://127.0.0.1:8000/

---

### 3. `start_consume.py` - Standalone Consumer Startup Script

**Purpose**: Demonstrates how to start a Funboost consumer independently, without launching it
alongside FastAPI



---

### 4. `example_req_fastapi.py` - API Test Client

**Purpose**: Demonstrates how to call the various endpoints of the Funboost FastAPI router

**Included test cases**:

#### Test 1: `test_publish_and_get_result()`
- **Function**: Publish a task and synchronously wait for the result
- **Request**: `POST /funboost/publish`
- **Parameters**:
  ```json
  {
    "queue_name": "test_fastapi_router_queue",
    "msg_body": {"x": 10, "y": 20},
    "need_result": true,
    "timeout": 10
  }
  ```
- **Note**: When `need_result=True`, the endpoint blocks until the task completes and returns the result

#### Test 2: `test_get_msg_count()`
- **Function**: Get the number of messages in a specified queue
- **Request**: `GET /funboost/get_msg_count?queue_name=test_fastapi_router_queue`
- **Use case**: Monitor queue backlog

#### Test 3: `test_publish_async_then_get_result()`
- **Function**: Publish a task asynchronously, first obtain a task_id, then query the result using the task_id
- **Flow**:
  1. Publish the task (`need_result=False`), immediately returns a task_id
  2. Use the task_id to call `GET /funboost/get_result` to retrieve the result
- **Advantage**: Non-blocking, suitable for long-running tasks

**How to run**:
```bash
python example_req_fastapi.py
```

---




