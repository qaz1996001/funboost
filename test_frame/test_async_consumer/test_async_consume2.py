"""

This script demonstrates that coroutine asyncio + aiohttp is 70% faster than threading + requests multi-threading
"""


from funboost import boost, BrokerEnum,ConcurrentModeEnum,ctrl_c_recv
import asyncio
import time
import aiohttp
import requests

url = 'http://mini.eastday.com/assets/v1/js/search_word.js'
# url = 'https://www.baidu.com/content-search.xml'
# rl = 'https://www.google-analytics.com/analytics.js'

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
ss = aiohttp.ClientSession(loop=loop)


@boost('test_async_queue1', concurrent_mode=ConcurrentModeEnum.ASYNC, broker_kind=BrokerEnum.REDIS,
        log_level=10,concurrent_num=3,
       specify_async_loop=loop
       )
async def async_f1(x):
    # If the same session is used with async with ss.request, specify_async_loop must match ClientSession's loop.
    # Otherwise, if using async with aiohttp.request, specify_async_loop parameter is not needed.
    # async with aiohttp.request('get', url=url) as resp:  # If making requests this way, boost decorator does not need to specify specify_async_loop
    #     text = await resp.text()
    # print(x,55555555555)
    # await asyncio.sleep(1,)
    # print(x,66666666666)
    # ss = aiohttp.ClientSession( )
    async with ss.request('get', url=url) as resp:  # If making requests this way, boost decorator must specify specify_async_loop,
        text = await resp.text()
        print('async_f1', x, resp.url, text[:10])
    await asyncio.sleep(5)
    return x


@boost('test_async_queue2', concurrent_mode=ConcurrentModeEnum.ASYNC, broker_kind=BrokerEnum.REDIS,
        log_level=10,concurrent_num=3,
       specify_async_loop=loop
       )
async def async_f2(x):
    async with ss.request('get', url=url) as resp:  # If making requests this way, boost decorator must specify specify_async_loop,
        text = await resp.text()
        print('async_f2', x, resp.url, text[:10])
    await asyncio.sleep(5)
    return x

rss = requests.session()
@boost('test_f_queue2', concurrent_mode=ConcurrentModeEnum.THREADING, broker_kind=BrokerEnum.REDIS, concurrent_num=500, log_level=10)
def f(y):
    # resp = requests.request('get', url)
    resp = rss.request('get', url)
    print(y, resp.text[:10])

async def do_req(i):
    async with ss.request('get', url=url) as resp:  # If making requests this way, boost decorator must specify specify_async_loop,
        text = await resp.text()
        print(f'Main thread loop running {i}:',text[:10])
    await asyncio.sleep(3)

if __name__ == '__main__':

    async_f1.clear()
    async_f2.clear()
    f.clear()

    for i in range(10):
        async_f1.push(i)
        async_f2.push(i*10)
        f.push(i * 10)

    async_f1.consume()
    async_f2.consume()
    # f.consume()
    # loop.run_until_complete(main_run())
    [loop.create_task(do_req(i)) for i in range(20)]
    loop.run_forever()


    ctrl_c_recv()
