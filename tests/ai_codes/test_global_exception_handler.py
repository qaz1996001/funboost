"""
Test code for the Funboost Router exception handling decorator
Note: Uses decorator approach, does not affect the user's own FastAPI app
"""

from fastapi import FastAPI
from funboost.faas.fastapi_adapter import fastapi_router, handle_funboost_exceptions, BaseResponse
from funboost.core.exceptions import QueueNameNotExists, FuncParamsError

# Create FastAPI application
app = FastAPI(title="Funboost Router Exception Handling Decorator Test")

# 1. Include funboost router (the decorator is already applied on the router's endpoints)
app.include_router(fastapi_router)

# Note: No need to register a global exception handler!
# Exception handling for the funboost router is implemented via the @handle_funboost_exceptions decorator
# This way it does not affect the user's own app


# ==================== Test endpoints ====================
# These are the user's own endpoints; the decorator can be used optionally

@app.get("/test/funboost_exception")
@handle_funboost_exceptions  # Use decorator
def test_funboost_exception():
    """
    Test FunboostException exception handling
    Accessing this endpoint will raise a QueueNameNotExists exception
    The decorator will automatically catch it and return a unified error format
    """
    # Simulate raising FunboostException
    raise QueueNameNotExists(
        message="Test queue does not exist",
        data={"queue_name": "test_queue", "available_queues": ["queue1", "queue2"]}
    )


@app.get("/test/normal_exception")
@handle_funboost_exceptions  # Use decorator
def test_normal_exception():
    """
    Test normal exception handling
    Accessing this endpoint will raise a ValueError
    The decorator will automatically catch it and return an error with stack trace
    """
    # Simulate raising a normal exception
    x = "not a number"
    return int(x)  # This will raise ValueError


@app.get("/test/func_params_error")
@handle_funboost_exceptions  # Use decorator
def test_func_params_error():
    """
    Test function parameter error exception
    """
    error_data = {
        'your_now_publish_params_keys_list': ['a', 'b'],
        'right_func_input_params_list_info': {
            'must_arg_name_list': ['a', 'b', 'c'],
            'optional_arg_name_list': []
        },
    }
    raise FuncParamsError('Invalid parameters for consuming function', data=error_data)


@app.get("/test/success")
@handle_funboost_exceptions  # Use decorator
def test_success():
    """
    Test normal return
    This endpoint does not raise exceptions
    Note: In successful responses, error, traceback, and trace_id are all None
    """
    return BaseResponse(
        succ=True,
        msg="Test successful",
        code=200,
        data={"message": "This is a successful response"},
        error=None,  # error is None on success
        traceback=None,  # traceback is None on success
        trace_id=None  # trace_id can also be set on success for tracing
    )


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("Funboost global exception handler test service started")
    print("=" * 60)
    print()
    print("Access the following URLs for testing:")
    print()
    print("1. API docs: http://127.0.0.1:8888/docs")
    print()
    print("2. Test endpoints:")
    print("   - http://127.0.0.1:8888/test/funboost_exception  (FunboostException)")
    print("   - http://127.0.0.1:8888/test/normal_exception    (Normal exception)")
    print("   - http://127.0.0.1:8888/test/func_params_error   (Function parameter error)")
    print("   - http://127.0.0.1:8888/test/success             (Successful response)")
    print()
    print("3. Funboost endpoints:")
    print("   - http://127.0.0.1:8888/funboost/get_all_queues")
    print()
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8888)
