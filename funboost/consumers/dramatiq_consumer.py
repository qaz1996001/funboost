import time

import dramatiq

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.assist.dramatiq_helper import DramatiqHelper


class DramatiqConsumer(AbstractConsumer):
    """
    Consumer implemented using dramatiq as middleware.
    """


    def custom_init(self):
        # This is the core
        dramatiq_actor_options = self.consumer_params.broker_exclusive_config['dramatiq_actor_options']
        if self.consumer_params.function_timeout:
            dramatiq_actor_options['time_limit'] = self.consumer_params.function_timeout * 1000  # dramatiq timeout is in milliseconds, funboost uses seconds.
        dramatiq_actor_options['max_retries'] = self.consumer_params.max_retry_times

        @dramatiq.actor(actor_name=self.queue_name, queue_name=self.queue_name,
                        **dramatiq_actor_options)
        def f(*args, **kwargs):
            self.logger.debug(f' This message was fetched by dramatiq from queue {self.queue_name}, dispatched by dramatiq framework to function {self.consuming_function.__name__}: args: {args}, kwargs: {kwargs}')
            return self.consuming_function(*args, **kwargs)

        DramatiqHelper.queue_name__actor_map[self.queue_name] = f

    def start_consuming_message(self):
        # Don't start a worker for each function individually; put queue names in a list, and realy_start_dramatiq_worker starts consuming multiple functions at once.
        DramatiqHelper.to_be_start_work_celery_queue_name_set.add(self.queue_name)
        super().start_consuming_message()

    def _dispatch_task(self):
        """ Consumption is fully controlled by the dramatiq framework, not using funboost's AbstractConsumer._run"""
        while 1:
            time.sleep(100)

    def _confirm_consume(self, kw):
        """Built-in with dramatiq framework, no funboost implementation needed"""

    def _requeue(self, kw):
        pass
