# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/6 0006 13:32

import abc
from funboost.consumers.base_consumer import AbstractConsumer


class EmptyConsumer(AbstractConsumer, metaclass=abc.ABCMeta):
    """
    An empty consumer base class, serving as a template for custom Brokers.

    This class is actually redundant, because users can simply inherit from AbstractConsumer, implement the custom_init method, and implement _dispatch_task, _confirm_consume, _requeue methods to add a custom broker.
    This class exists to clearly tell you that only the three methods below are needed to implement a custom broker, because the AbstractConsumer base class is feature-rich with too many methods, and users may not know which methods need to be overridden.


    """
    def custom_init(self):
        pass

    @abc.abstractmethod
    def _dispatch_task(self):
        """
        Core task dispatch. This method needs to implement a loop that fetches messages from your middleware,
        then calls `self._submit_task(msg)` to submit tasks to the framework's concurrent pool for execution. Refer to various consumer implementations in the funboost source code.
        """
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def _confirm_consume(self, kw):
        """Confirm consumption, equivalent to the ACK concept"""
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def _requeue(self, kw):
        """Requeue the message"""
        raise NotImplemented('not realization')
