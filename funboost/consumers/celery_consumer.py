# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32

import time
from funboost.assist.celery_helper import CeleryHelper, celery_app
from celery import Task as CeleryTask
from funboost.consumers.base_consumer import AbstractConsumer


class CeleryConsumer(AbstractConsumer):
    """
    Consumer implemented using Celery as middleware.
    """



    # Full list of celery configuration options: https://docs.celeryq.dev/en/stable/userguide/configuration.html#new-lowercase-settings
    # All configurable options for celery @app.task() can be found in D:\ProgramData\Miniconda3\Lib\site-packages\celery\app\task.py

    '''
        #: Execution strategy used, or the qualified name of one.
        Strategy = 'celery.worker.strategy:default'

        #: Request class used, or the qualified name of one.
        Request = 'celery.worker.request:Request'

        #: The application instance associated with this task class.
        _app = None

        #: Name of the task.
        name = None

        #: Enable argument checking.
        #: You can set this to false if you don't want the signature to be
        #: checked when calling the task.
        #: Defaults to :attr:`app.strict_typing <@Celery.strict_typing>`.
        typing = None

        #: Maximum number of retries before giving up.  If set to :const:`None`,
        #: it will **never** stop retrying.
        max_retries = 3

        #: Default time in seconds before a retry of the task should be
        #: executed.  3 minutes by default.
        default_retry_delay = 3 * 60

        #: Rate limit for this task type.  Examples: :const:`None` (no rate
        #: limit), `'100/s'` (hundred tasks a second), `'100/m'` (hundred tasks
        #: a minute),`'100/h'` (hundred tasks an hour)
        rate_limit = None

        #: If enabled the worker won't store task state and return values
        #: for this task.  Defaults to the :setting:`task_ignore_result`
        #: setting.
        ignore_result = None

        #: If enabled the request will keep track of subtasks started by
        #: this task, and this information will be sent with the result
        #: (``result.children``).
        trail = True

        #: If enabled the worker will send monitoring events related to
        #: this task (but only if the worker is configured to send
        #: task related events).
        #: Note that this has no effect on the task-failure event case
        #: where a task is not registered (as it will have no task class
        #: to check this flag).
        send_events = True

        #: When enabled errors will be stored even if the task is otherwise
        #: configured to ignore results.
        store_errors_even_if_ignored = None

        #: The name of a serializer that are registered with
        #: :mod:`kombu.serialization.registry`.  Default is `'json'`.
        serializer = None

        #: Hard time limit.
        #: Defaults to the :setting:`task_time_limit` setting.
        time_limit = None

        #: Soft time limit.
        #: Defaults to the :setting:`task_soft_time_limit` setting.
        soft_time_limit = None

        #: The result store backend used for this task.
        backend = None

        #: If enabled the task will report its status as 'started' when the task
        #: is executed by a worker.  Disabled by default as the normal behavior
        #: is to not report that level of granularity.  Tasks are either pending,
        #: finished, or waiting to be retried.
        #:
        #: Having a 'started' status can be useful for when there are long
        #: running tasks and there's a need to report what task is currently
        #: running.
        #:
        #: The application default can be overridden using the
        #: :setting:`task_track_started` setting.
        track_started = None

        #: When enabled messages for this task will be acknowledged **after**
        #: the task has been executed, and not *just before* (the
        #: default behavior).
        #:
        #: Please note that this means the task may be executed twice if the
        #: worker crashes mid execution.
        #:
        #: The application default can be overridden with the
        #: :setting:`task_acks_late` setting.
        acks_late = None

        #: When enabled messages for this task will be acknowledged even if it
        #: fails or times out.
        #:
        #: Configuring this setting only applies to tasks that are
        #: acknowledged **after** they have been executed and only if
        #: :setting:`task_acks_late` is enabled.
        #:
        #: The application default can be overridden with the
        #: :setting:`task_acks_on_failure_or_timeout` setting.
        acks_on_failure_or_timeout = None

        #: Even if :attr:`acks_late` is enabled, the worker will
        #: acknowledge tasks when the worker process executing them abruptly
        #: exits or is signaled (e.g., :sig:`KILL`/:sig:`INT`, etc).
        #:
        #: Setting this to true allows the message to be re-queued instead,
        #: so that the task will execute again by the same worker, or another
        #: worker.
        #:
        #: Warning: Enabling this can cause message loops; make sure you know
        #: what you're doing.
        reject_on_worker_lost = None

        #: Tuple of expected exceptions.
        #:
        #: These are errors that are expected in normal operation
        #: and that shouldn't be regarded as a real error by the worker.
        #: Currently this means that the state will be updated to an error
        #: state, but the worker won't log the event as an error.
        throws = ()

        #: Default task expiry time.
        expires = None

        #: Default task priority.
        priority = None

        #: Max length of result representation used in logs and events.
        resultrepr_maxsize = 1024

        #: Task request stack, the current request will be the topmost.
        request_stack = None
    '''

    def custom_init(self):
        # This is the core: when @boost is used, it applies the celery app.task decorator
        celery_task_deco_options = dict(name=self. queue_name,
                                        max_retries=self.consumer_params.max_retry_times, bind=True)
        if self.consumer_params.qps:
            celery_task_deco_options['rate_limit'] = f'{self.consumer_params.qps}/s'
        if self.consumer_params.function_timeout:
            celery_task_deco_options['soft_time_limit'] = self.consumer_params.function_timeout
        celery_task_deco_options.update(self.consumer_params.broker_exclusive_config['celery_task_config'])

        _use_celery_native_retry = 'autoretry_for' in celery_task_deco_options

        @celery_app.task(**celery_task_deco_options)
        def f(this: CeleryTask, *args, **kwargs):
            self.logger.debug(f' This message was fetched by celery from queue {self.queue_name}, dispatched by celery framework to function {self.consuming_function.__name__}: args: {args}, kwargs: {kwargs}')
            if _use_celery_native_retry:
                # User configured autoretry_for in broker_exclusive_config['celery_task_config'],
                # celery handles retry logic itself, just execute the function directly.
                return self.consuming_function(*args, **kwargs)
            try:
                return self.consuming_function(*args, **kwargs)
            except Exception as exc:
                # print(this.request.__dict__,dir(this))
                if this.request.retries != self.consumer_params.max_retry_times:
                    log_msg = f'fun: {self.consuming_function}  args: {args} , kwargs: {kwargs} message error on attempt {this.request.retries},  {exc} \n'
                    self.logger.error(log_msg, exc_info=self.consumer_params.is_print_detail_exception)
                else:
                    log_msg = f'fun: {self.consuming_function}  args: {args} , kwargs: {kwargs} message reached max retry times {this.request.retries} and still failed,  {exc} \n'
                    self.logger.critical(log_msg, exc_info=self.consumer_params.is_print_detail_exception)
                if self.consumer_params.is_using_advanced_retry:
                    countdown = self._calculate_exponential_backoff(
                        this.request.retries,
                        self._adv_retry_base_interval,
                        self._adv_retry_multiplier,
                        self._adv_retry_max_interval,
                        self._adv_retry_jitter,
                    )
                else:
                    countdown = 0
                raise this.retry(exc=exc, countdown=countdown)

        celery_app.conf.task_routes.update({self.queue_name: {"queue": self.queue_name}})  # Automatically configure celery to use different queue names for each function.
        self.celery_task = f
        CeleryHelper.concurrent_mode = self.consumer_params.concurrent_mode

    def start_consuming_message(self):
        # Don't start a celery worker for each function individually; put queue names in a list, and CeleryHelper.realy_start_celery_worker starts consuming multiple functions at once.
        CeleryHelper.add_start_work_celery_queue_name(self.queue_name)
        super().start_consuming_message()

    def _dispatch_task(self):
        """ Consumption is fully controlled by the celery framework, not using funboost's AbstractConsumer._run"""
        while 1:
            time.sleep(100)

    def _confirm_consume(self, kw):
        """Consumption and ack confirmation are fully controlled by the celery framework, no funboost code needed"""
        pass

    def _requeue(self, kw):
        pass
