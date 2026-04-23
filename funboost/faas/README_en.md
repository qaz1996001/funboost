## See Tutorial Chapter 4.38 for Details


## funboost.faas - Add funboost API routes to popular Python web frameworks with a single line

`funboost.faas` ships with out-of-the-box support for multiple mainstream web frameworks, so you no longer need to manually write routing interfaces for publishing messages, retrieving results, accessing message queues, or scheduled task endpoints in various Python web frameworks.

###  funboost.faas Out-of-the-Box  
Easily add multiple funboost routing interfaces to your own web service in one step.   

**Supported frameworks:**  
- fastapi
- flask
- django


### Usage Example
#### FastAPI Example
```
from funboost.faas import fastapi_router, CareProjectNameEnv

app = FastAPI() # app is your FastAPI application. Simply include fastapi_router to instantly add multiple funboost routing interfaces.

CareProjectNameEnv.set('test_project1') # Optional — only watch queues under the specified test_project1 project

app.include_router(fastapi_router)
```
