# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/6 0006 12:12

import abc
from funboost.publishers.base_publisher import AbstractPublisher


class EmptyPublisher(AbstractPublisher, metaclass=abc.ABCMeta):
    """
    Empty publisher with empty implementation. Should be used with boost's consumer_override_cls and publisher_override_cls parameters, or be inherited.
    """

    def custom_init(self):
        pass

    @abc.abstractmethod
    def _publish_impl(self, msg: str):
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def clear(self):
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def get_message_count(self):
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def close(self):
        raise NotImplemented('not realization')
