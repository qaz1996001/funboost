import asyncio
import time
from funboost import boost,BrokerEnum,ConcurrentModeEnum,BoosterParams

# funboost directly and conveniently supports consuming async def functions, far surpassing celery's support for async functions
@boost(BoosterParams(queue_name='aio_long_time_fun_queue',is_using_rpc_mode=True))
async def aio_long_time_fun(x):
    await asyncio.sleep(10)
    print(f'aio_long_time_fun {x}')
    return f'aio_long_time_fun {x}'

@boost(BoosterParams(queue_name='long_time_fun_queue',is_using_rpc_mode=True))
def long_time_fun(x):
    time.sleep(5)
    print(f'long_time_fun {x}')
    return f'long_time_fun {x}'


if __name__ == '__main__':
    async def aio_push_msg():
        for i in range(10):
            await aio_long_time_fun.aio_push(i)
    asyncio.run(aio_push_msg()) # Demonstrate asyncio publishing messages to middleware

    for j in range(10):     # Demonstrate synchronous publishing messages to middleware
        long_time_fun.push(j)


    aio_long_time_fun.consume() # Start consuming. funboost directly supports async def functions as consumer functions — far more convenient than celery's support for async def.
    long_time_fun.consume()  # Start consuming