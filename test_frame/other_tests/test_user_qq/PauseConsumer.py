import copy
import datetime
import threading
import time
import uuid

from funboost import AbstractConsumer
from funboost.core.funboost_time import FunboostTime
from funboost.core.helper_funs import get_func_only_params, get_publish_time


class PauseConsumer(AbstractConsumer):
    pause = threading.Event()

    def _submit_task(self, kw):
        
        kw['body'] = self.convert_msg_before_run(kw['body'])
        self._print_message_get_from_broker(kw['body'])
        if self._judge_is_daylight():
            self._requeue(kw)
            time.sleep(self.time_interval_for_check_do_not_run_time)
            return
        function_only_params = get_func_only_params(kw['body'], )
        if self._get_priority_conf(kw, 'do_task_filtering') and self._redis_filter.check_value_exists(
                function_only_params):  # Check function parameters and filter tasks that have already been executed successfully.
            self.logger.warning(f'Filtered task {kw["body"]} in redis key [{self._redis_filter_key_name}]')
            self._confirm_consume(kw)
            return
        publish_time = get_publish_time(kw['body'])
        msg_expire_seconds_priority = self._get_priority_conf(kw, 'msg_expire_seconds')
        if msg_expire_seconds_priority and time.time() - msg_expire_seconds_priority > publish_time:
            self.logger.warning(
                f'Message publish timestamp is {publish_time} {kw["body"].get("publish_time_format", "")}, '
                f'{round(time.time() - publish_time, 4)} seconds ago, '
                f'exceeding the specified {msg_expire_seconds_priority} seconds, discarding task')
            self._confirm_consume(kw)
            return 0

        msg_eta = self._get_priority_conf(kw, 'eta')
        msg_countdown = self._get_priority_conf(kw, 'countdown')
        misfire_grace_time = self._get_priority_conf(kw, 'misfire_grace_time')
        run_date = None
        # print(kw)
        if msg_countdown:
            run_date = FunboostTime(kw['body']['extra']['publish_time']).datetime_obj + datetime.timedelta(
                seconds=msg_countdown)
        if msg_eta:
            run_date = FunboostTime(msg_eta).datetime_obj
        # print(run_date,time_util.DatetimeConverter().datetime_obj)
        # print(run_date.timestamp(),time_util.DatetimeConverter().datetime_obj.timestamp())
        # print(self.concurrent_pool)
        if run_date:  # Delayed task
            # print(repr(run_date),repr(datetime.datetime.now(tz=pytz.timezone(frame_config.TIMEZONE))))
            if self._has_start_delay_task_scheduler is False:
                self._has_start_delay_task_scheduler = True
                self._start_delay_task_scheduler()

            # This approach submits to a thread pool
            # self._delay_task_scheduler.add_job(self.concurrent_pool.submit, 'date', run_date=run_date, args=(self._run,), kwargs={'kw': kw},
            #                                    misfire_grace_time=misfire_grace_time)

            # This approach resends delayed tasks to the message queue as ordinary tasks
            msg_no_delay = copy.deepcopy(kw['body'])
            self.__delete_eta_countdown(msg_no_delay)
            # print(msg_no_delay)
            # When using a database as apscheduler's jobstores, cannot use self.publisher_of_same_queue.publish because self cannot be serialized
            self._delay_task_scheduler.add_job(self._push_apscheduler_task_to_broker, 'date', run_date=run_date,
                                               kwargs={'queue_name': self.queue_name, 'msg': msg_no_delay,
                                                       'runonce_uuid': str(uuid.uuid4())},
                                               misfire_grace_time=misfire_grace_time,
                                               )
            self._confirm_consume(kw)

        else:  # Regular task
            self.concurrent_pool.submit(self._run, kw)

        if self.consumer_params.is_using_distributed_frequency_control:  # If distributed frequency control is needed.
            active_num = self._distributed_consumer_statistics.active_consumer_num
            self._frequency_control(self.consumer_params.qps / active_num,
                                    self._msg_schedule_time_intercal * active_num)
        else:
            self._frequency_control(self.consumer_params.qps, self._msg_schedule_time_intercal)

        while 1:  # This block of code supports pausing consumption.
            # print(self._pause_flag)
            if self._pause_flag.is_set() or PauseConsumer.pause.is_set():
                time.sleep(5)
                if time.time() - self._last_show_pause_log_time > 60:
                    self.logger.warning(f'Tasks in queue {self.queue_name} have been set to paused consumption')
                    self._last_show_pause_log_time = time.time()
            else:
                break
