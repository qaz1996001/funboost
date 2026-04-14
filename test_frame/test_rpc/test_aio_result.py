
from auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote()

import asyncio

from funboost import AioAsyncResult,TaskOptions
from test_frame.test_rpc.test_consume import add


async def process_result(status_and_result: dict):
    """
    :param status_and_result: A dictionary containing the function arguments, result,
                              whether the function ran successfully, and the exception type.
    """
    await asyncio.sleep(1)
    print(status_and_result)


async def test_get_result(i):
    add.publish({"a":1,"b":2},task_id=100005,task_options=TaskOptions(is_using_rpc_mode=True))
    async_result = add.push(i, i * 2)
    aio_async_result = AioAsyncResult(task_id=async_result.task_id) # Use the asyncio-compatible class here for better integration with the asyncio ecosystem
    print(await aio_async_result.result) # Note the await here; without await, it prints a coroutine object and does not return the result. This is basic asyncio syntax that users should be familiar with.
    print(await aio_async_result.status_and_result)
    # await aio_async_result.set_callback(process_result)  # You can also schedule tasks into the loop


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    for j in range(100):
        loop.create_task(test_get_result(j))
    loop.run_forever()