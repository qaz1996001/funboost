import traceback

import typing

from auto_run_on_remote import run_current_script_on_remote

run_current_script_on_remote()
import functools
import time
import signal


def timeout_linux(timeout: typing.Optional[int]):
    def _timeout_linux(func, ):
        """Decorator that adds timeout functionality to a function"""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def _timeout_handler(signum, frame):
                """Timeout handler function, raises exception when signal is received"""
                raise TimeoutError(f"Function: {func} params: {args}, {kwargs} ,execution timed out: {timeout}")

            # Set timeout signal handler
            signal.signal(signal.SIGALRM, _timeout_handler)  # Only suitable for Linux timeout
            # Start a timer, sends signal after timeout
            signal.alarm(timeout)

            try:
                return func(*args, **kwargs)
            finally:
                # Remember to cancel the timer after execution completes
                signal.alarm(0)  # Disable the timer

        return wrapper

    return _timeout_linux


if __name__ == '__main__':

    # Use decorator to implement timeout functionality
    @timeout_linux(3)
    def fun(x, ):
        """Example function simulating a long-running operation"""
        print(f"Running function with x={x}")
        time.sleep(5)  # Simulate time-consuming operation
        print("Function completed")
        return x + 1


    try:
        print(fun(10))  # Try to run the function with a 3-second timeout
    except TimeoutError as e:
        traceback.print_exc()

    import celery
