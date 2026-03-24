# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
from threading import Thread
import socket
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer


class TCPConsumer(AbstractConsumer, ):
    """
    Message queue implemented with socket, does not support persistence, but requires no software installation.
    """



    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        # ip__port_str = self.queue_name.split(':')
        # ip_port = (ip__port_str[0], int(ip__port_str[1]))
        # self._ip_port_raw = ip_port
        # self._ip_port = ('', ip_port[1])
        # ip_port = ('', 9999)
        self._ip_port = (self.consumer_params.broker_exclusive_config['host'],
                         self.consumer_params.broker_exclusive_config['port'])
        self.bufsize = self.consumer_params.broker_exclusive_config['bufsize']

    # noinspection DuplicatedCode
    def _dispatch_task(self):
      
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP protocol
        server.bind(self._ip_port)
        server.listen(128)
        self._server = server
        while True:
            tcp_cli_sock, addr = self._server.accept()
            Thread(target=self.__handle_conn, args=(tcp_cli_sock,)).start()  # Server-side multi-threading, can simultaneously handle messages from multiple TCP long-connection clients.

    def __handle_conn(self, tcp_cli_sock):
        try:
            while True:
                data = tcp_cli_sock.recv(self.bufsize)
                # print('server received data', data)
                if not data:
                    break
                # self._print_message_get_from_broker(f'udp {self._ip_port_raw}', data.decode())
                tcp_cli_sock.send('has_recived'.encode())
                # tcp_cli_sock.close()
                kw = {'body': data}
                self._submit_task(kw)
            tcp_cli_sock.close()
        except ConnectionResetError:
            pass

    def _confirm_consume(self, kw):
        pass  # No consumption confirmation functionality.

    def _requeue(self, kw):
        pass
