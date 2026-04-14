# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import json

from funboost.assist.rq_helper import RqHelper
from funboost.publishers.base_publisher import AbstractPublisher


class RqPublisher(AbstractPublisher):
    """
    Uses RQ (Redis Queue) as the broker.
    """

    def _publish_impl(self, msg):
        func_kwargs = json.loads(msg)
        func_kwargs.pop('extra')
        RqHelper.queue_name__rq_job_map[self.queue_name].delay(**func_kwargs)

    def clear(self):
        pass

    def get_message_count(self):
        return -1

    def close(self):
        pass

    def _at_exit(self):
        pass
