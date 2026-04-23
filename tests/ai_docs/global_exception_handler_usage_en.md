# Funboost FastAPI Global Exception Handler Usage Guide

## Overview

To avoid writing try-except in every FastAPI endpoint, we implemented a global exception handler that automatically captures and processes all exceptions, returning unified error format.

## Features

### 1. FunboostException Handling
- Automatically extracts exception's `code`, `message`, `data` information
- Returns structured error response
- Includes `trace_id` for tracing

### 2. Generic Exception Handling  
- Captures all other exception types
- Returns fixed code `5555`
- Includes complete exception stack for debugging

## Usage

### Method 1: Using Helper Function (Recommended)

```python
from fastapi import FastAPI
from funboost.faas.fastapi_adapter import fastapi_router, register_funboost_exception_handlers

app = FastAPI()

# 1. Include funboost router
app.include_router(fastapi_router)

# 2. Register global exception handlers
register_funboost_exception_handlers(app)
```

### Method 2: Manual Registration

```python
from fastapi import FastAPI
from funboost.faas.fastapi_adapter import (
    fastapi_router, 
    funboost_exception_handler, 
    general_exception_handler
)
from funboost.core.exceptions import FunboostException

app = FastAPI()
app.include_router(fastapi_router)

# Manually add exception handlers
app.add_exception_handler(FunboostException, funboost_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
```

## Error Response Format

### FunboostException Error Response

```json
{
    "succ": false,
    "msg": "queue name not exists",
    "code": 4001,
    "data": {
        "queue_name": "non_existent_queue"
    },
    "error": "QueueNameNotExists",
    "trace_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Normal Exception Error Response

```json
{
    "succ": false,
    "msg": "System error: ValueError: invalid literal for int()",
    "code": 5555,
    "data": null,
    "error": "ValueError",
    "traceback": "Traceback (most recent call last):\n  File ...\n"
}
```

## Custom Exception Examples

### Define Custom Exception

```python
from funboost.core.exceptions import FunboostException

class QueueNameNotExists(FunboostException):
    default_message = "queue name not exists"
    default_code = 4001

class FuncParamsError(FunboostException):
    default_message = "consuming function input params error"
    default_code = 5001
```

### Raise Exception in Code

```python
# Raise QueueNameNotExists exception
if queue_name not in all_queue_names:
    raise QueueNameNotExists(
        message=f"Queue {queue_name} does not exist",
        data={'queue_name': queue_name, 'available_queues': all_queue_names}
    )

# Raise FuncParamsError exception  
if not params_valid:
    error_data = {
        'your_now_publish_params_keys_list': list(publish_params_keys_set),
        'right_func_input_params_list_info': consuming_func_input_params_list_info,
    }
    raise FuncParamsError('Invalid parameters for consuming function', data=error_data)
```

## No More try-except in Endpoints

### Before (Need try-except in every endpoint)

```python
@fastapi_router.get("/get_msg_count")
def get_msg_count(queue_name: str):
    try:
        publisher = SingleQueueConusmerParamsGetter(queue_name).generate_publisher_by_funboost_redis_info()
        count = publisher.get_message_count()
        return BaseResponse(succ=True, msg="Retrieved successfully", data={"count": count})
    except Exception as e:
        logger.exception(f'Failed to get message count: {str(e)}')
        return BaseResponse(
            succ=False,
            msg=f"Failed to get message count: {str(e)}",
            data=None
        )
```

### Now (Global handler catches exceptions)

```python
@fastapi_router.get("/get_msg_count")
def get_msg_count(queue_name: str):
    publisher = SingleQueueConusmerParamsGetter(queue_name).generate_publisher_by_funboost_redis_info()
    count = publisher.get_message_count()
    return BaseResponse(succ=True, msg="Retrieved successfully", data={"count": count})
```

## Advantages

1. **Cleaner code**: No need to write try-except in every endpoint
2. **Unified error format**: All errors return unified format
3. **Rich information**:
   - FunboostException: Includes business error code, error data
   - Normal exception: Includes complete stack for easy debugging
4. **Easy to maintain**: Exception handling logic centrally managed
5. **Strong tracing ability**: Support trace_id for distributed tracing

## Precautions

1. Global exception handler must be registered immediately after creating FastAPI app
2. If endpoint needs special exception handling logic, can still use try-except inside endpoint
3. HTTP status code always returns 200, business errors distinguished by `code` field in response body
4. Recommend keeping stack information in development, consider hiding in production
