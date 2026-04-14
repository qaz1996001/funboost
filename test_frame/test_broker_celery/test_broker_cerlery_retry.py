
"""
This script demonstrates funboost using celery as a broker.
Users can still use celery's low-level details in addition to funboost's unified API.
"""
import time


from funboost import boost, BrokerEnum, BoosterParams
from funboost.assist.celery_helper import CeleryHelper, Task

@boost(BoosterParams(queue_name='test_broker_celery_retry3',
                     broker_kind=BrokerEnum.CELERY,  # Use the celery framework as funboost's broker
                     concurrent_num=10,

                    max_retry_times=100,
                      is_using_advanced_retry=True,
                        advanced_retry_config={
                            'retry_mode': 'requeue',          # Delayed requeue, does not consume worker threads
                            'retry_base_interval': 10.0,       # Initial 10s
                            'retry_multiplier': 2.0,          # Doubles each time: 10s -> 20s -> 40s ...
                            'retry_max_interval': 300.0,      # Maximum retry interval is 5 minutes, no unlimited doubling
                            'retry_jitter': False,            # Whether to add random jitter, randomly multiply by 0.5 - 1.5
                        },

                     broker_exclusive_config= {
                        'celery_task_config' : dict(
                            # autoretry_for = (ZeroDivisionError,),
                            retry_kwargs={'max_retries': 50},                       # Maximum retry count
                            retry_backoff=10,                                   # Enable exponential backoff strategy
                            retry_backoff_max=300,
                            retry_jitter=False,                                    # Add random jitter to prevent thundering herd
                            default_retry_delay=60                                # Default wait time (seconds)
                        )
                        }

                     ))
def my_fun(x, y):
    1/ 0

if __name__ == '__main__':
    # Publish messages using funboost syntax; my_fun type is funboost Booster
    my_fun.clear()
    my_fun.push(1, 2)

    my_fun.consume()  # This does not start consuming immediately; it registers the queue to be started by celery
    CeleryHelper.realy_start_celery_worker()  # This actually starts the celery worker command line to consume all registered queues
