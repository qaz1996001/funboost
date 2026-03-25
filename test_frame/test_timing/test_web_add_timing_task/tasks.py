# tasks.py
import time
from funboost import boost, BrokerEnum, BoosterParams

# To allow both the Web side and the background Worker side to connect to the same message queue,
# we use Redis as the middleware.
# Make sure Redis is configured in your funboost_config.py.
@boost(BoosterParams(
    queue_name='web_dynamic_task_queue2',
    broker_kind=BrokerEnum.REDIS_ACK_ABLE
))
def dynamic_task(task_id: str, message: str):
    """
    This function will be dynamically and periodically scheduled by the Web application.
    """
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time}] [Background Worker] Executing task...\n"
          f"  - Task ID: {task_id}\n"
          f"  - Message: '{message}'")
    # You can perform actual operations here such as sending emails or generating reports
