import time
import deprecated
# from inspect import ismethod, isclass, formatargspec
from funboost import boost, BrokerEnum, BoosterParamsComplete, AsyncResult
from funboost.concurrent_pool.bounded_threadpoolexcutor import BoundedThreadPoolExecutor


@boost(BoosterParamsComplete(queue_name='test_rpc_hello',
do_task_filtering=True,

is_using_rpc_mode=True,broker_kind=BrokerEnum.REDIS_ACK_ABLE))
def fun(x):
    time.sleep(2)
    print(x)
    return f'hello {x} '


def show_result(status_and_result: dict):
    """
    :param status_and_result: A dictionary containing the function arguments, result,
                              whether the function ran successfully, and the exception type.
    """
    print(status_and_result)


thread_pool = BoundedThreadPoolExecutor(200)

def wait_msg_result(async_result:AsyncResult):
    print(async_result.status_and_result)

if __name__ == '__main__':
    fun.consume()

    async_result = fun.push(10)
    print(async_result.result)

    async_result = fun.push(10)
    print(async_result.result)


    # for i in range(100):
    #     async_result = fun.push(i)
    #     print(async_result.result) # print(async_result.get()) usage is equivalent

    #     async_result.set_callback(show_result) # equivalent to thread_pool.submit(wait_msg_result,async_result)