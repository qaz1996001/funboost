"""
This is a simple example demonstrating how to publish messages and retrieve results in a web context.

It is recommended to use `from funboost.fass` instead, as described in tutorial chapter 15.
It provides out-of-the-box functionality, better integration with your FastAPI service on a single port,
and supports more URL routes.

"""

import traceback
import typing

from funboost import AioAsyncResult, AsyncResult,TaskOptions

from funboost.core.cli.discovery_boosters import BoosterDiscovery
from funboost import BoostersManager
from fastapi import FastAPI
from pydantic import BaseModel


class MsgItem(BaseModel):
    queue_name: str  # Queue name
    msg_body: dict  # Message body, i.e. the input parameter dict of the boost function, e.g. {"x":1,"y":2}
    need_result: bool = False  # Whether to return the result after publishing the message
    timeout: int = 60  # Maximum wait time for the result to be returned.


class PublishResponse(BaseModel):
    succ: bool
    msg: str
    status_and_result: typing.Optional[dict] = None  # The consumption status and result of the consuming function.


# Create FastAPI application instance
app = FastAPI()

'''
If you need to retrieve the function execution result after publishing a message,
it is recommended to use an asyncio-based web framework such as FastAPI or Tornado, rather than Flask or Django,
to better handle the blocking time required for obtaining results. Without asyncio, the web framework would need
a very high number of threads configured.
'''


@app.post("/funboost_publish_msg")
async def publish_msg(msg_item: MsgItem):
    status_and_result = None
    try:
        booster = BoostersManager.get_or_create_booster_by_queue_name(msg_item.queue_name)
        if msg_item.need_result:
            if booster.boost_params.is_using_rpc_mode is False:
                raise ValueError(f' need_result is true, the consumer for queue {booster.queue_name} needs @boost configured to support rpc mode')
            async_result = await booster.aio_publish(msg_item.msg_body,task_options=TaskOptions(is_using_rpc_mode=True))
            status_and_result = await AioAsyncResult(async_result.task_id, timeout=msg_item.timeout).status_and_result
            print(status_and_result)
            # status_and_result = AsyncResult(async_result.task_id, timeout=msg_item.timeout).status_and_result
        else:
            await booster.aio_publish(msg_item.msg_body)
        return PublishResponse(succ=True, msg=f'Queue {msg_item.queue_name}, message published successfully', status_and_result=status_and_result)
    except Exception as e:
        return PublishResponse(succ=False, msg=f'Queue {msg_item.queue_name}, message publish failed {type(e)} {e} {traceback.format_exc()}',
                               status_and_result=status_and_result)


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run('funboost.contrib.api_publish_msg:app', host="0.0.0.0", port=16666, workers=4)

    '''
    Usage examples can be found in test_frame/test_api_publish_msg.
    '''
