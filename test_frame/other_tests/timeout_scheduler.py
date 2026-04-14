
import time
import schedule
from functools import wraps

class TimeoutException(Exception):
    """Custom timeout exception"""
    pass

def timeout_decorator(timeout):
    """Timeout decorator based on the schedule library"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]  # Use a list to store the result so it can be modified inside inner function
            executed = [False]  # Use a list to track whether the function has been executed

            def job():
                nonlocal result, executed
                try:
                    result[0] = func(*args, **kwargs)
                finally:
                    executed[0] = True

            schedule.every(timeout).seconds.do(job).tag('timeout_job')  # Use tag for easy subsequent clearing

            start_time = time.time()
            while time.time() - start_time < timeout * 2:  # Run for twice the timeout to ensure opportunity to check timeout
                schedule.run_pending()
                time.sleep(0.1)
                if executed[0]:
                    schedule.clear('timeout_job')  # Clear the tagged job
                    return result[0]

            schedule.clear('timeout_job')  # If timed out, ensure the task is cleared
            raise TimeoutException(f"Function {func.__name__} timed out after {timeout} seconds.")

        return wrapper
    return decorator

# Example function
@timeout_decorator(timeout=3)
def long_running_function(x):
    print(f"Running function with x={x}")
    time.sleep(5)  # Simulate time-consuming operation
    print("Function completed")
    return x + 1

try:
    print(long_running_function(10))
except TimeoutException as e:
    print(4444)
    print(e)