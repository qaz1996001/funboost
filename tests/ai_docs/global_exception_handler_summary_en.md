# Funboost FastAPI Global Exception Handler Implementation Summary

## Implementation Content

### 1. Core Functionality File Changes

#### `funboost/faas/fastapi_adapter.py`

**New imports:**
```python
from funboost.core.exceptions import FunboostException
from fastapi import Request
from fastapi.responses import JSONResponse
```

**New functionality:**

1. **`funboost_exception_handler`**: Handles FunboostException type exceptions
   - Automatically extracts `code`, `message`, `data`, `trace_id`
   - Returns unified JSON format

2. **`general_exception_handler`**: Handles all other exceptions
   - Fixed return code 5555
   - Includes complete exception stack information
   - Automatically logs

3. **`register_funboost_exception_handlers(app)`**: Helper registration function
   - Register all exception handlers with one line of code
   - Simplify user usage

### 2. Exception Class Enhancement

#### `funboost/core/exceptions.py`

**QueueNameNotExists**:
```python
class QueueNameNotExists(FunboostException):
    default_message = "queue name not exists"
    default_code = 4001
```

**FuncParamsError**:
```python
class FuncParamsError(FunboostException):
    default_message = "consuming function input params error"  
    default_code = 5001
```

**FunboostException.to_dict()** enhancement:
- Add `utc_time` and `local_time` fields
- Use timezone-aware time format

### 3. Code Using Exceptions

#### `active_cousumer_info_getter.py`
```python
# Import exception class
from funboost.core.exceptions import QueueNameNotExists

# Use exception
raise QueueNameNotExists(
    err_msg, 
    data={'queue_name': self.queue_name}
)
```

#### `consuming_func_iniput_params_check.py`
```python
# Import exception class
from funboost.core.exceptions import FuncParamsError

# Use exception
error_data = {
    'your_now_publish_params_keys_list': list(publish_params_keys_set),
    'right_func_input_params_list_info': self.consuming_func_input_params_list_info,
}
raise FuncParamsError(
    'Invalid parameters for consuming function',
    data=error_data
)
```

## Usage Method

### Basic Usage

```python
from fastapi import FastAPI
from funboost.faas.fastapi_adapter import (
    fastapi_router, 
    register_funboost_exception_handlers
)

app = FastAPI()
app.include_router(fastapi_router)

# Key: Register global exception handler
register_funboost_exception_handlers(app)
```

### Endpoint Code Simplification

**Before** (each endpoint needs try-except):
```python
@fastapi_router.get("/get_msg_count")
def get_msg_count(queue_name: str):
    try:
        publisher = SingleQueueConusmerParamsGetter(queue_name).generate_publisher_by_funboost_redis_info()
        count = publisher.get_message_count()
        return BaseResponse(succ=True, msg="Retrieved successfully", data=CountData(queue_name=queue_name, count=count))
    except Exception as e:
        logger.exception(f'Failed to get message count: {str(e)}')
        return BaseResponse(
            succ=False,
            msg=f"Failed to get message count: {str(e)}",
            data=CountData(queue_name=queue_name, count=-1)
        )
```

**Now** (just write business logic):
```python
@fastapi_router.get("/get_msg_count")
def get_msg_count(queue_name: str):
    publisher = SingleQueueConusmerParamsGetter(queue_name).generate_publisher_by_funboost_redis_info()
    count = publisher.get_message_count()
    return BaseResponse(
        succ=True,
        msg="Retrieved successfully",
        data=CountData(queue_name=queue_name, count=count)
    )
```

## Error Response Format

### FunboostException Response Example

```json
{
    "succ": false,
    "msg": "queue name not exists",
    "code": 4001,
    "data": {
        "queue_name": "non_existent_queue",
        "available_queues": ["queue1", "queue2"]
    },
    "error": "QueueNameNotExists",
    "trace_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Normal Exception Response Example

```json
{
    "succ": false,
    "msg": "System error: ValueError: invalid literal for int() with base 10: 'abc'",
    "code": 5555,
    "data": null,
    "error": "ValueError",
    "traceback": "Traceback (most recent call last):\n  File \"...\", line 123, in ...\n    ...\nValueError: invalid literal for int() with base 10: 'abc'"
}
```

## Advantages

### 1. Code Simplicity
- No need to write try-except in every endpoint
- Reduced large amount of repeated code
- Business logic is clearer

### 2. Unified Error Format
- All errors return unified JSON format
- Frontend only needs one set of error handling logic

### 3. Rich Error Information
- **FunboostException**: Includes business error code, error data, trace_id
- **Normal exception**: Includes complete stack for easy debugging

### 4. Easy to Maintain
- Exception handling logic centrally managed
- Modify error format only needs to change one place

### 5. Type Safety
- FunboostException supports custom code and data
- Easy to extend new exception types

## File List

### Modified Files
1. `funboost/faas/fastapi_adapter.py` - Added global exception handlers
2. `funboost/core/exceptions.py` - Optimized exception classes, added time fields
3. `funboost/core/active_cousumer_info_getter.py` - Import and use QueueNameNotExists
4. `funboost/core/consuming_func_iniput_params_check.py` - Import and use FuncParamsError

### New Files
1. `tests/ai_docs/global_exception_handler_usage.md` - Usage documentation
2. `tests/ai_codes/test_global_exception_handler.py` - Test code
3. `tests/ai_docs/global_exception_handler_summary.md` - This summary

## Testing Method

Run test code:
```bash
python tests/ai_codes/test_global_exception_handler.py
```

Then visit:
- http://127.0.0.1:8888/docs - View API documentation
- http://127.0.0.1:8888/test/funboost_exception - Test FunboostException
- http://127.0.0.1:8888/test/normal_exception - Test normal exception
- http://127.0.0.1:8888/test/success - Test successful response

## Precautions

1. **Must register**: Global exception handler must call `register_funboost_exception_handlers(app)` to take effect

2. **Registration timing**: Must register immediately after creating FastAPI app

3. **HTTP status code**: All responses have HTTP status code 200, business errors distinguished by `code` field

4. **Local try-except**: If an endpoint needs special handling, can still use try-except inside endpoint

5. **Production environment**: Consider hiding `traceback` field in production to avoid leaking sensitive information

## Extension Suggestions

### 1. Add More Custom Exception Classes
```python
class PermissionDenied(FunboostException):
    default_message = "permission denied"
    default_code = 4003

class ResourceNotFound(FunboostException):
    default_message = "resource not found"
    default_code = 4004
```

### 2. Control Stack Information by Environment
```python
import os

def get_traceback():
    if os.getenv('ENV') == 'production':
        return None  # Don't return stack in production
    return traceback.format_exc()
```

### 3. Add Error Logging
```python
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f'Unexpected exception: {str(exc)}')
    # Can report to monitoring system like Sentry
    # sentry_sdk.capture_exception(exc)
    ...
```

## Summary

By implementing global exception handler, we successfully:
- ✅ Eliminated repeated try-except code in every endpoint
- ✅ Implemented unified error response format
- ✅ Provided rich error information (code, data, traceback)
- ✅ Simplified user usage (register with one line of code)
- ✅ Maintained code cleanliness and maintainability

This is an elegant solution that follows FastAPI best practices!
