
"""
This code simulates why conventional concurrency cannot achieve a sustained, precise 8 calls per second
(i.e., 8 requests to a Flask API per second).

The code below uses 8 concurrent threads to run request_flask_api.

When flask_veiw_mock takes 0.1 seconds:  finishes in 10s; console prints 80 'hello world' per second - 10x over the target.
When flask_veiw_mock takes exactly 1 second: finishes in 100s; console prints 8 'hello world' per second - only meets target when duration is exactly 1 second.
When flask_veiw_mock takes 10 seconds:   takes 1000s to finish; console prints 8 'hello world' only every 10 seconds - far from the goal of 8 per second continuously.

As you can see, using concurrency count to achieve 8 requests per second to Flask is very difficult.
In 99.99% of cases, the server doesn't happen to take exactly 1 second.

Some people still don't understand the difference between concurrency and qps (how many times per second):
concurrency count only equals qps when the function duration is exactly 1 second.
"""
import time
from concurrent.futures import ThreadPoolExecutor


def flask_veiw_mock(x):
    # time.sleep(0.1)  # Use different sleep durations to simulate server response time
    # time.sleep(1)   # Use different sleep durations to simulate server response time
    time.sleep(10)  # Use different sleep durations to simulate server response time
    return f"hello world {x}"


def request_flask_api(x):
    response = flask_veiw_mock(x)
    print(time.strftime("%H:%M:%S"), '   ', response)


if __name__ == '__main__':
    with ThreadPoolExecutor(8) as pool:
        for i in range(800):
            pool.submit(request_flask_api,i)
