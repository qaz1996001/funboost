"""
This module demonstrates how users who already use FastAPI can easily add multiple
funboost router endpoints in one step, including /funboost/publish, /funboost/get_result,
/funboost/get_msg_count, and dozens of other endpoints. This way users do not need to
write their own FastAPI route handlers for publishing funboost messages and retrieving results.

from funboost.faas import fastapi_router
app.include_router(fastapi_router) # Just do this and your FastAPI app gains multiple funboost route endpoints
"""


import uvicorn
from fastapi import FastAPI

from funboost.faas import fastapi_router,CareProjectNameEnv


CareProjectNameEnv.set('test_project1') # Optional: only care about queues under the specified test_project1 project to reduce noise from unrelated queues.

# Create FastAPI app
app = FastAPI()

@app.get('/')
async def index():
    return "Hello World"

# 2. Include funboost.faas fastapi_router
app.include_router(fastapi_router)  # This is the core usage


# 4. Run the app
if __name__ == '__main__':
    # The consumer runs in the background threads/processes started by @boost.
    # We run uvicorn to serve the API.
    print("Starting FastAPI app with Funboost Router...")

    print("Starting Funboost API service...")
    print("API docs: http://127.0.0.1:8000/docs")
    print("Try POST http://127.0.0.1:8000/funboost/publish with body: {'queue_name': 'test_funboost_faas_queue', 'msg_body': {'x': 1, 'y': 2}, 'need_result': true}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
