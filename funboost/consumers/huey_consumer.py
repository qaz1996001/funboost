import time

from huey import RedisHuey
from huey.consumer import Consumer

from funboost import AbstractConsumer
from funboost.assist.huey_helper import HueyHelper


class HueyConsumer(AbstractConsumer):
    """
    Consumer implemented using huey as middleware.
    """




    def custom_init(self):
        # This is the core
        huey_task_kwargs = self.consumer_params.broker_exclusive_config['huey_task_kwargs']
        huey_task_kwargs['retries'] = self.consumer_params.max_retry_times

        @HueyHelper.huey_obj.task(name=self.queue_name,
                        **huey_task_kwargs)
        def f(*args, **kwargs):
            self.logger.debug(f' This message was fetched by huey from queue {self.queue_name}, dispatched by huey framework to function {self.consuming_function.__name__}: args: {args}, kwargs: {kwargs}')
            return self.consuming_function(*args, **kwargs)

        HueyHelper.queue_name__huey_task_fun_map[self.queue_name] = f

    def start_consuming_message(self):
        # Don't start a worker for each function individually; put queue names in a list, and realy_start_dramatiq_worker starts consuming multiple functions at once.
        HueyHelper.to_be_start_huey_queue_name_set.add(self.queue_name)
        super().start_consuming_message()

    def _dispatch_task(self):
        """ Consumption is fully controlled by the huey framework, not using funboost's AbstractConsumer._run"""
        while 1:
            time.sleep(100)

    def _confirm_consume(self, kw):
        """Built-in with huey framework, no funboost implementation needed"""

    def _requeue(self, kw):
        pass
