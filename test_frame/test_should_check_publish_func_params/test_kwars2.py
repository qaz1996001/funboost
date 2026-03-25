
"""
Complete example of Funboost consuming arbitrary JSON message formats (compatible with non-Funboost publishing)

Funboost natively supports consuming arbitrary JSON messages and does not require tasks to be published
via Funboost, providing strong heterogeneous compatibility and message format tolerance.
This greatly reduces integration costs and collaboration barriers in real systems.
In contrast, Celery's format is closed and its message structure is complex, making cross-language
integration nearly impossible — Funboost wins decisively on this point.
"""

import time
import redis
import json
from funboost import boost, BrokerEnum, BoosterParams, fct,ctrl_c_recv

@boost(boost_params=BoosterParams(queue_name="task_queue_name2c", qps=5,
                                   broker_kind=BrokerEnum.REDIS,
                                  log_level=10, should_check_publish_func_params=False
                                  ))  # Parameters include 20+ options; virtually every control scenario is supported.
def task_fun(**kwargs):
    print(kwargs)
    print(fct.full_msg)
    time.sleep(3)  # The framework automatically manages concurrency around this blocking call;
                   # no matter how long the function takes, it will automatically adjust to run task_fun 5 times per second.


if __name__ == "__main__":
    redis_conn = redis.Redis(db=7)
    for i in range(10):
        task_fun.publish(dict(x=i, y=i * 2, x3=6, x4=8, x5={'k1': i, 'k2': i * 2, 'k3': i * 3}))  # Publisher publishes tasks
        task_fun.publisher.send_msg(dict(y1=i, y2=i * 2, y3=6, y4=8, y5={'k1': i, 'k2': i * 2, 'k3': i * 3})) # send_msg sends raw messages

        # Messages in arbitrary free-form JSON sent by users or colleagues in Java/Golang can also be
        # consumed by funboost — it does not matter whether Funboost was used to publish them.
        # Funboost's consumption compatibility is extremely strong, completely surpassing Celery.
        redis_conn.lpush('task_queue_name2c',json.dumps({"m":666,"n":777}))

    task_fun.consume()

    ctrl_c_recv()
