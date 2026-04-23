# Funboost Router Exception Handler Decorator Documentation

## Overview

To avoid writing try-except in every FastAPI endpoint while **not affecting the user's own FastAPI app**, we created a decorator `@handle_funboost_exceptions` that is **only used in funboost router endpoints**.

## Why Use Decorator Instead of Global Exception Handler?

### Problems with Global Exception Handler
- ❌ Affects all endpoints in the user's entire FastAPI app
- ❌ May conflict with user's own exception handling logic
- ❌ User may not want funboost to control their global error handling

### Advantages of Decorator
- ✅ **Only applies to funboost router endpoints**, doesn't affect user's app
- ✅ User can freely define their own exception handling logic
- ✅ Clear and straightforward, which endpoints use exception handling at a glance
- ✅ Higher flexibility, some endpoints can choose not to use

## Usage

### Basic Usage

```python
from funboost.faas.fastapi_adapter import fastapi_router, handle_funboost_exceptions, BaseResponse

@fastapi_router.get("/some_endpoint")
@handle_funboost_exceptions  # Add this decorator
async def some_endpoint(queue_name: str):
    """
    Write business logic directly, no need for try-except
    Exceptions will be automatically captured and returned in unified format
    """
    # Business logic
    result = do_something(queue_name)
    return BaseResponse(succ=True, msg="Success", data=result)
```

### Complete Example

```python
@fastapi_router.get("/get_msg_count")
@handle_funboost_exceptions  # Use decorator
def get_msg_count(queue_name: str):
    """Get message count by queue_name"""
    # Write business logic directly, no need for try-except
    publisher = SingleQueueConusmerParamsGetter(queue_name).generate_publisher_by_funboost_redis_info()
    count = publisher.get_message_count()
    
    return BaseResponse(
        succ=True,
        msg="Retrieved successfully",
        data={"queue_name": queue_name, "count": count}
    )
```

### Async Functions Also Supported

```python
@fastapi_router.post("/publish")
@handle_funboost_exceptions  # Async functions are also supported
async def publish_msg(msg_item: MsgItem):
    """Publish message"""
    # Write business logic directly
    publisher = SingleQueueConusmerParamsGetter(msg_item.queue_name).generate_publisher_by_funboost_redis_info()
    async_result = await publisher.aio_publish(msg_item.msg_body)
    
    return BaseResponse(
        succ=True,
        msg="Published successfully",
        data={"task_id": async_result.task_id}
    )
```

## Exception Handling Rules

The decorator handles exceptions according to the following rules:

### 1. FunboostException

```python
# When code raises FunboostException
raise QueueNameNotExists(
    message="Queue does not exist",
    data={"queue_name": "test_queue"}
)

# Decorator automatically returns
{
    "succ": false,
    "msg": "Queue does not exist",
    "code": 4001,                    # Exception's code
    "data": {"queue_name": "test_queue"},  # Exception's data
    "error": "QueueNameNotExists",   # Exception class name
    "traceback": null,               # Business exceptions don't return stack
    "trace_id": "uuid-xxx"           # If exception has trace_id
}
```

### 2. Normal Exceptions

```python
# When code raises normal exception
x = "not a number"
result = int(x)  # Raises ValueError

# Decorator automatically returns
{
    "succ": false,
    "msg": "System error: ValueError: invalid literal for int()",
    "code": 5555,                    # Fixed 5555
    "data": null,
    "error": "ValueError",           # Exception class name
    "traceback": "Traceback...",     # Complete stack
    "trace_id": null
}
```

## User Integration Example

### User's FastAPI App

```python
from fastapi import FastAPI
from funboost.faas.fastapi_adapter import fastapi_router

# Create user's own app
app = FastAPI()

# User's own endpoint (using their own exception handling)
@app.get("/user/endpoint")
def user_endpoint():
    try:
        # User's own logic and exception handling
        return {"result": "ok"}
    except Exception as e:
        # User's own exception handling way
        return {"error": str(e)}

# Include funboost router
app.include_router(fastapi_router)
# Note: No need to register global exception handler!
# funboost router's exception handling is implemented via decorator, doesn't affect user's app
```

### Isolation Example

```python
# User's endpoint - not affected
@app.get("/user/divide")
def divide(a: int, b: int):
    # If b=0, user can handle exception themselves
    try:
        return {"result": a / b}
    except ZeroDivisionError:
        return {"error": "Divisor cannot be 0"}  # User-defined error format

# funboost's endpoint - uses decorator
@fastapi_router.get("/get_queue_info")
@handle_funboost_exceptions
def get_queue_info(queue_name: str):
    # If error occurs, returns funboost unified format
    info = get_info(queue_name)
    return BaseResponse(succ=True, data=info)
```

## Comparison

### Before (Using try-except)

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

### Now (Using Decorator)

```python
@fastapi_router.get("/get_msg_count")
@handle_funboost_exceptions  # Only need to add one line
def get_msg_count(queue_name: str):
    # Write business logic directly, much cleaner!
    publisher = SingleQueueConusmerParamsGetter(queue_name).generate_publisher_by_funboost_redis_info()
    count = publisher.get_message_count()
    return BaseResponse(succ=True, msg="Retrieved successfully", data={"count": count})
```

## Decorator Order

**Important:** Decorator order matters! `@handle_funboost_exceptions` must be placed after the route decorator:

```python
# ✅ Correct
@fastapi_router.get("/endpoint")
@handle_funboost_exceptions
def endpoint():
    pass

# ❌ Incorrect
@handle_funboost_exceptions
@fastapi_router.get("/endpoint")
def endpoint():
    pass
```

## Optional Usage

Not all endpoints must use the decorator. If an endpoint needs special exception handling logic, it can choose not to use the decorator:

```python
@fastapi_router.get("/special_endpoint")
def special_endpoint():
    """This endpoint has special exception handling requirements"""
    try:
        result = do_something_special()
        return BaseResponse(succ=True, data=result)
    except SpecialException as e:
        # Special handling logic
        return custom_error_response(e)
    except Exception as e:
        # Special handling for other exceptions
        return another_custom_response(e)
```

## Implementation Principle

The decorator internally judges whether the function is synchronous or asynchronous, then uses the corresponding wrapper:

```python
def handle_funboost_exceptions(func):
    import functools
    
    # Wrapper for async functions
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except FunboostException as e:
            # Handle FunboostException
            return BaseResponse(...)
        except Exception as e:
            # Handle other exceptions
            return BaseResponse(...)
    
    # Wrapper for sync functions
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FunboostException as e:
            return BaseResponse(...)
        except Exception as e:
            return BaseResponse(...)
    
    # Return corresponding wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
```

## Summary of Advantages

1. **Doesn't affect user app** ✅  
   - Only applies to funboost router endpoints
   - User can freely define their own exception handling

2. **Cleaner code** ✅  
   - No need to write try-except in every endpoint
   - Business logic is clearer

3. **Unified format** ✅  
   - All endpoints using the decorator return unified error format
   - Convenient for frontend unified processing

4. **High flexibility** ✅  
   - Can be used selectively
   - Special endpoints can customize exception handling

5. **Easy to maintain** ✅  
   - Exception handling logic is centralized in the decorator
   - Modify once, all endpoints using the decorator take effect

## Precautions

1. **Don't forget to add the decorator**  
   For new endpoints that want unified exception handling, remember to add `@handle_funboost_exceptions`

2. **Decorator order is important**  
   `@handle_funboost_exceptions` must be placed after route decorator (like `@fastapi_router.get(...)`)

3. **Both sync and async are supported**  
   Decorator automatically judges function type, no need to distinguish

4. **Doesn't affect user app**  
   This is the most important design principle, funboost should not interfere with user's global configuration

## Summary

By using decorator instead of global exception handler, we have achieved:

- ✅ Cleaner code (no need for try-except)
- ✅ Unified error format
- ✅ **Doesn't affect user's app** (this is key!)
- ✅ Flexibility and maintainability

This is a more elegant and reasonable design solution!
