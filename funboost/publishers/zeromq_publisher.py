# -*- coding: utf-8 -*-
# @Author  : ydf
from funboost.core.lazy_impoter import ZmqImporter
from funboost.publishers.base_publisher import AbstractPublisher


# noinspection PyProtectedMember
class ZeroMqPublisher(AbstractPublisher):
    """
    ZeroMQ broker publisher. ZeroMQ is based on socket code, does not persist, and requires no software installation.
    """
    def custom_init(self):
        self._port = self.publisher_params.broker_exclusive_config['port']
        if self._port is None:
            raise ValueError('please specify port')

        context = ZmqImporter().zmq.Context()
        socket = context.socket(ZmqImporter().zmq.REQ)
        socket.connect(f"tcp://localhost:{int(self._port)}")
        self.socket =socket
        self.logger.warning('When using zeromq as the broker, the consumer must be started first (the consumer will also start the broker). Tasks can only be published after the server is started.')

    def _publish_impl(self, msg):
        self.socket.send(msg.encode())
        self.socket.recv()

    def clear(self):
        pass

    def get_message_count(self):
        return -1

    def close(self):
        pass

