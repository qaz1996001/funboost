from fastapi import FastAPI
from funboost import AioAsyncResult

from consume_fun import aio_long_time_fun, long_time_fun

app = FastAPI()


@app.get("/")
async def root():
    return {"Hello": "World"}


# Demonstrate push synchronous publishing and aio rpc to get consumption result
@app.get("/url1/{name}")
async def api1(name: str):
    async_result = long_time_fun.push(name)  # Usually publishing a message is fast; on LAN it's generally less than 0.3ms, so calling synchronous IO in an asyncio async method usually won't cause serious problems
    return {"result": await AioAsyncResult(async_result.task_id).result}   # In general you don't need rpc mode to get the consumption result immediately upon request. Just send the message to the middleware and forget it. Frontend uses ajax polling or mqtt.
    # return {"result": async_result.result}  # If you write code this way directly, it will cause all coroutines to block globally — a catastrophe.

# Demonstrate aio_push async publishing and aio rpc to get consumption result
@app.get("/url2/{name}")
async def api2(name: str):
    asio_async_result = await aio_long_time_fun.aio_push(name)  # If you use the asyncio programming ecosystem, this approach is still recommended, especially when publishing messages to external networks that may take longer.
    return {"result": await asio_async_result.result}  # In general you don't need rpc mode to get the consumption result immediately upon request. Just send the message to the middleware and forget it. Frontend uses ajax polling or mqtt.


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)