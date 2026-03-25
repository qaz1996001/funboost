### 4.4.3 Demonstrates adding scheduled tasks in a Python web application (the scripts for adding and executing scheduled tasks are in different .py files)

Demo link for adding scheduled tasks in a web application:

[https://github.com/ydf0509/funboost/tree/master/test_frame/funboost_aps_web_demo](https://github.com/ydf0509/funboost/tree/master/test_frame/funboost_aps_web_demo)

##### 4.4.3.1 Demonstrates adding scheduled tasks in a Python web application, where the script for adding scheduled tasks and the script for starting consumption are in different .py files

```
Demonstrates adding scheduled tasks in a Python web application, where the script for adding scheduled tasks and the script for starting consumption are in different .py files. It is critical to make sure you start the APScheduler object — this is the most important step.
```

##### 4.4.3.2 web_app.py is the web application responsible for adding scheduled tasks to Redis. Flask is used as the example framework here; Django and FastAPI work the same way — there is no need to demonstrate them individually.

```
Because funboost is free and unconstrained, it does not require plugins like django-funboost, flask-funboost, or fastapi-funboost.

Only the troublesome and hard-to-use celery requires third-party plugins such as django-celery, flask-celery, and fastapi-celery to help users simplify adaptation to various web frameworks.
funboost has no need for such plugins to adapt to various web frameworks.
```

##### 4.4.3.3 run_consume.py is the script that starts consumption and starts the APScheduler timer

```python
ApsJobAdder(fun_sum,job_store_kind='redis',) # Responsible for starting the APScheduler object; the APScheduler object will scan Redis for scheduled tasks
# and execute them. The scheduled task's job is to push messages to the message queue on a timer.

fun_sum.consume()  # Start consuming messages from the message queue
```

**Warning!!! Do not only start fun_sum.consume() without also starting the APScheduler object. Without it, APScheduler will not scan Redis for already-added scheduled tasks, and will not automatically push messages to the message queue on schedule.**
