# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import os
import sys
import time
import celery
import celery.result
import typing

from funboost.assist.celery_helper import celery_app
from funboost.publishers.base_publisher import AbstractPublisher, TaskOptions


class CeleryPublisher(AbstractPublisher, ):
    """
    Uses celery as the broker.
    """

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                task_options: TaskOptions = None) -> celery.result.AsyncResult:
        msg, msg_function_kw, extra_params,task_id = self._convert_msg(msg, task_id, task_options)
        t_start = time.time()
        celery_result = celery_app.send_task(name=self.queue_name, kwargs=msg_function_kw, task_id=extra_params['task_id'])  # type: celery.result.AsyncResult
        self.logger.debug(f'Pushed message to queue {self._queue_name}, took {round(time.time() - t_start, 4)} seconds  {msg_function_kw}')  # Full msg is too long to display.
        with self._lock_for_count:
            self.count_per_minute += 1
            self.publish_msg_num_total += 1
            if time.time() - self._current_time > 10:
                self.logger.info(
                    f'Pushed {self.count_per_minute} messages in 10 seconds, total {self.publish_msg_num_total} messages pushed to queue {self._queue_name}')
                self._init_count()
        # return AsyncResult(task_id)
        return celery_result  # Returns the native celery result object, type is celery.result.AsyncResult.

    def _publish_impl(self, msg):
        pass

    def clear(self):
        python_executable = sys.executable
        cmd = f''' {python_executable} -m celery -A funboost.publishers.celery_publisher purge -Q {self.queue_name} -f'''
        self.logger.warning(f'Deleting messages in celery queue {self.queue_name}  {cmd}')
        os.system(cmd)

    def get_message_count(self):
        # return -1
        with celery_app.connection_or_acquire() as conn:
            msg_cnt = conn.default_channel.queue_declare(
                queue=self.queue_name, passive=False,durable=True,auto_delete=False).message_count

        return msg_cnt

    def close(self):
        pass
