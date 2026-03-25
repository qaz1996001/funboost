

import time
from funboost import boost, BrokerEnum, BoosterParams

# 1. Add the @boost decorator to your function
@boost(BoosterParams(queue_name="hello_queue", qps=5))
def say_hello(name: str):
    print(f"Hello, {name}!")
    time.sleep(1)

if __name__ == "__main__":
    # 2. Publish tasks and start consuming
    for i in range(50):
        say_hello.push(name=f"Funboost User {i}")
    
    say_hello.consume()