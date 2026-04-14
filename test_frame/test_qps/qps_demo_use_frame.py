
"""
This code simulates why conventional concurrency cannot achieve a sustained, precise 8 calls per second
(i.e., 8 requests to a Flask API per second).
But using a distributed function scheduling framework easily achieves this goal.

The code below uses the distributed function scheduling framework to schedule and run the request_flask_api function.

When flask_veiw_mock takes 0.1 seconds:  console prints 'hello world' 8 times per second - precisely meets the frequency target.
When flask_veiw_mock takes 1 second:     console prints 'hello world' 8 times per second - precisely meets the frequency target.
When flask_veiw_mock takes 10 seconds:   console prints 'hello world' 8 times per second - precisely meets the frequency target.
When flask_veiw_mock takes 0.001 second: console prints 'hello world' 8 times per second - precisely meets the frequency target.
When flask_veiw_mock takes 50 seconds:   console prints 'hello world' 8 times per second - precisely meets the frequency target.
The distributed function scheduling framework ignores function duration and always achieves precise frequency control.
Thread pools, asyncio, etc. are simply helpless when faced with uncertain API response times.

Some people still don't understand the difference between concurrency and qps (how many times per second):
concurrency count only equals qps when the function duration is exactly 1 second.
"""
import time
from funboost import boost,BrokerEnum


def flask_veiw_mock(x):
    time.sleep(0.1)  # Use different sleep durations to simulate server response time
    # time.sleep(1)   # Use different sleep durations to simulate server response time
    # time.sleep(10)  # Use different sleep durations to simulate server response time
    return f"hello world {x}"

@boost("test_qps", broker_kind=BrokerEnum.MEMORY_QUEUE, qps=8)
def request_flask_api(x):
    response = flask_veiw_mock(x)
    print(time.strftime("%H:%M:%S"), '   ', response)


if __name__ == '__main__':
    for i in range(800):
        request_flask_api.push(i)
    request_flask_api.consume()
