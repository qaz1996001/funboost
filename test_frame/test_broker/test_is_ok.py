import time
import asyncio
import copy
from funboost import boost, BrokerEnum, BoosterParams, ConcurrentModeEnum, ctrl_c_recv, ApsJobAdder
from funboost.contrib.save_function_result_status.save_result_status_use_dataset import ResultStatusUseDatasetMixin
from funboost.utils.class_utils import ClsHelper


# 0. Define a custom class to demonstrate pickle serialization
class MyObject:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return f"MyObject(name='{self.name}', value={self.value})"


# 1. Define a regular synchronous function.
# funboost's default concurrency mode is multi-threading (ConcurrentModeEnum.THREADING),
# which is ideal for IO-blocking functions containing time.sleep.
@boost(BoosterParams(queue_name='sync_task_queue', broker_kind=BrokerEnum.REDIS_ACK_ABLE,
                     concurrent_mode=ConcurrentModeEnum.THREADING, concurrent_num=5,
                     consumer_override_cls=ResultStatusUseDatasetMixin
                     ))
def task_sync(x: int, y: int):
    """
    This is a regular synchronous function.
    """
    print(f"Starting synchronous task: {x} + {y}")
    time.sleep(2)  # Simulate a time-consuming IO operation
    result = x + y
    print(f"Synchronous task completed: {x} + {y} = {result}")
    return result

# 2. Define an asynchronous coroutine function.
# For async def functions, specify concurrent_mode=ConcurrentModeEnum.ASYNC explicitly.
# funboost will use an event loop to run these coroutine tasks concurrently.
@boost(BoosterParams(queue_name='async_task_queue', broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_mode=ConcurrentModeEnum.ASYNC, concurrent_num=10,
    is_using_rpc_mode=True))
async def task_async(url: str):
    """
    This is an asynchronous coroutine function.
    """
    print(f"Starting async task: fetching {url}")
    await asyncio.sleep(3)  # Simulate an async aiohttp/httpx network request
    print(f"Async task completed: fetched {url} successfully")
    return f"Success: {url}"


# 3. Define a class with an instance method
class MyClass:
    def __init__(self, multiplier):
        # This line is required so funboost can re-instantiate the object when consuming
        self.obj_init_params: dict = ClsHelper.get_obj_init_params_for_funboost(copy.copy(locals()))
        self.multiplier = multiplier
        print(f"MyClass instance created, multiplier is: {self.multiplier}")

    # Apply the @boost decorator directly to the instance method
    @boost(BoosterParams(queue_name='instance_method_queue', broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_num=3))
    def multiply(self, x: int):
        print(f"Starting instance method task: {x} * {self.multiplier}")
        time.sleep(1)
        result = x * self.multiplier
        print(f"Instance method task completed: {x} * {self.multiplier} = {result}")
        return result


# 4. Define a function that receives a custom object, which will trigger pickle serialization
@boost(BoosterParams(queue_name='pickle_task_queue', broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_num=3))
def task_with_pickle(obj: MyObject):
    """
    This function receives a custom object; funboost will automatically use pickle for serialization.
    """
    print(f"Starting pickle task: received object {obj}")
    time.sleep(1)
    obj.value += 100
    print(f"Pickle task completed: object is now {obj}")
    return str(obj)


if __name__ == '__main__':
    # 5. Clear previous tasks (optional, to ensure a clean test environment)
    task_sync.clear()
    task_async.clear()
    task_with_pickle.clear()
    my_instance = MyClass(multiplier=10)  # Create an instance
    my_instance.multiply.clear()

    # Test calling functions directly
    print("Test calling functions directly")
    task_sync(1, 2)
    asyncio.get_event_loop().run_until_complete(task_async("https://example.com/page/1"))
    my_instance.multiply(10)
    task_with_pickle(MyObject(name="obj_1", value=1))

    # 6. Start all consumers
    # .consume() is non-blocking; it starts the consumer in the background
    task_sync.consume()
    task_async.consume()
    my_instance.multiply.consume()
    task_with_pickle.consume()

    print("\nAll consumers started, waiting to process tasks...")

    # 7. Publish tasks to their respective queues
    print("Publishing tasks...")
    for i in range(5):
        task_sync.push(i, i * 2)
        print(task_async.push(f"https://example.com/page/{i}").result)
        my_instance.multiply.push(my_instance, i)  # Publish instance method task, pass the instance as the first argument
        task_with_pickle.push(MyObject(name=f'obj_{i}', value=i))  # Publish a custom object
    print("Task publishing complete.")


    # 8. Add a scheduled task
    ApsJobAdder(task_sync).add_push_job(trigger='interval', seconds=1, args=(111, 222))


    print("Press Ctrl+C to exit.")



    # 10. Block the main thread so background consumers can keep running
    ctrl_c_recv()
