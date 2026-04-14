"""
Precisely locate consumer performance bottlenecks - direct profiling in synchronous mode
"""
import time
import cProfile
import pstats
from io import StringIO

# Directly test internal consumer methods
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum
from funboost.core.serialization import Serialization
from funboost.core.helper_funs import get_func_only_params, MsgGenerater
from funboost.core.function_result_status_saver import FunctionResultStatus


def test_consume_overhead():
    """Test the overhead of each stage during consumption"""
    n = 100000

    # Simulate a message
    msg = {'x': 1, 'extra': {'task_id': 'test_123', 'publish_time': time.time(), 'publish_time_format': '2026-01-21 18:00:00'}}
    msg_str = Serialization.to_json_str(msg)

    print(f"=== Test overhead of each stage ({n} iterations) ===\n")

    # 1. Serialization.to_dict
    t = time.time()
    for _ in range(n):
        Serialization.to_dict(msg_str)
    print(f"Serialization.to_dict(str): {time.time()-t:.3f} seconds")

    # 2. Serialization.to_dict (already a dict)
    t = time.time()
    for _ in range(n):
        Serialization.to_dict(msg)
    print(f"Serialization.to_dict(dict): {time.time()-t:.3f} seconds")

    # 3. get_func_only_params
    t = time.time()
    for _ in range(n):
        get_func_only_params(msg)
    print(f"get_func_only_params: {time.time()-t:.3f} seconds")

    # 4. FunctionResultStatus creation
    t = time.time()
    for _ in range(n):
        FunctionResultStatus('test_queue', 'test_func', msg)
    print(f"FunctionResultStatus creation: {time.time()-t:.3f} seconds")

    # 5. dict.get operations
    t = time.time()
    for _ in range(n):
        msg.get('extra', {}).get('task_id')
        msg.get('extra', {}).get('publish_time')
    print(f"dict.get operations: {time.time()-t:.3f} seconds")

    # 6. Simple function call
    def simple_func(x):
        pass
    t = time.time()
    for _ in range(n):
        simple_func(1)
    print(f"Simple function call: {time.time()-t:.3f} seconds")

    # 7. queue.Queue.get + put
    from queue import Queue
    q = Queue()
    for _ in range(n):
        q.put(msg)
    t = time.time()
    for _ in range(n):
        q.get()
    print(f"queue.Queue.get: {time.time()-t:.3f} seconds")


if __name__ == '__main__':
    test_consume_overhead()
