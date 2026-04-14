# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/25
"""
WebSocket Broker - WebSocket-based message queue

Design philosophy:
    - Uses WebSocket connections for message publishing and consumption
    - Supports real-time bidirectional communication
    - Suitable for lightweight, low-latency scenarios

Usage:
    from websocket_broker import BROKER_KIND_WEBSOCKET

    @boost(BoosterParams(
        queue_name='ws_queue',
        broker_kind=BROKER_KIND_WEBSOCKET,
        broker_exclusive_config={
            'ws_url': 'ws://localhost:8765',
        }
    ))
    def process_message(x, y):
        return x + y

    if __name__ == '__main__':
        # The WebSocket server must be started first
        process_message.consume()

Dependencies:
    pip install websocket-client
"""

import json
import threading
import time
import queue as queue_module
from typing import Optional
import logging
import re
import socket

try:
    import websocket
except ImportError:
    raise ImportError("Please install websocket-client: pip install websocket-client")

from funboost import register_custom_broker, AbstractConsumer, AbstractPublisher
from funboost.core.broker_kind__exclusive_config_default_define import register_broker_exclusive_config_default
from funboost.core.loggers import get_funboost_file_logger

# ============================================================================
# Publisher Implementation
# ============================================================================

class WebSocketPublisher(AbstractPublisher):
    """
    WebSocket Publisher

    Sends messages to the server via a WebSocket connection
    """

    def custom_init(self):
        super().custom_init()
        config = self.publisher_params.broker_exclusive_config
        self._ws_url = config['ws_url']
        self._reconnect_interval = config['reconnect_interval']
        self._ws = None
        self._lock = threading.Lock()
        self._connect()
        self.logger.info(f"WebSocket Publisher initialized, connection: {self._ws_url}")

    def _connect(self):
        """Establish WebSocket connection"""
        try:
            self._ws = websocket.create_connection(
                self._ws_url,
                timeout=10,
            )
            self.logger.debug(f"WebSocket connection successful: {self._ws_url}")
        except Exception as e:
            self.logger.warning(f"WebSocket connection failed: {e}")
            self._ws = None

    def _ensure_connection(self):
        """Ensure the connection is valid"""
        with self._lock:
            if self._ws is None or not self._ws.connected:
                self._connect()

    def _publish_impl(self, msg: str):
        """
        Publish message: send via WebSocket
        """
        self._ensure_connection()
        if self._ws is None:
            raise ConnectionError("WebSocket connection is unavailable")

        # Wrap the message and add the queue name
        envelope = {
            'command': 'publish',
            'queue': self._queue_name,
            'body': msg,
        }
        self._ws.send(json.dumps(envelope))

    def clear(self):
        """Clear the queue (WebSocket does not support this natively; sends a clear command to the server)"""
        self._ensure_connection()
        if self._ws:
            cmd = {'command': 'clear', 'queue': self._queue_name}
            self._ws.send(json.dumps(cmd))

    def get_message_count(self) -> int:
        """Get the number of messages in the queue (requires server support)"""
        # WebSocket itself does not support getting message count; return -1 to indicate unknown
        return -1

    def close(self):
        """Close the connection"""
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None


# ============================================================================
# Consumer Implementation
# ============================================================================

class WebSocketConsumer(AbstractConsumer):
    """
    WebSocket Consumer

    Receives messages via a WebSocket connection and consumes them
    """

    BROKER_KIND = None  # Will be set automatically by the framework
    _server_started = False  # Class variable indicating whether the server has been started
    _server_lock = threading.Lock()

    def _before_start_consuming_message_hook(self):
        super()._before_start_consuming_message_hook()
        config = self.consumer_params.broker_exclusive_config
        self._ws_url = config['ws_url']
        self._reconnect_interval = config['reconnect_interval']
        self._ws = None
        self._running = False
        self._message_queue = queue_module.Queue()

        # Automatically start the WebSocket server (if not already started)
        self._ensure_server_started()

        self.logger.info(f"WebSocket Consumer initialized, connection: {self._ws_url}")

    def _ensure_server_started(self):
        """Ensure the WebSocket server has been started"""
        with WebSocketConsumer._server_lock:
            if WebSocketConsumer._server_started:
                return

            # Parse URL to get host and port
            match = re.match(r'ws://([^:]+):(\d+)', self._ws_url)
            if not match:
                self.logger.warning(f"Unable to parse WebSocket URL: {self._ws_url}")
                return

            host = match.group(1)
            port = int(match.group(2))

            # Check if the port is already in use
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind((host, port))
                sock.close()
                # Port is available, start the server
                self._start_server_in_background(host, port)
                WebSocketConsumer._server_started = True
            except OSError:
                # Port is already in use, server may already be running
                self.logger.info(f"WebSocket server may already be running: {self._ws_url}")
                WebSocketConsumer._server_started = True
            finally:
                try:
                    sock.close()
                except Exception:
                    pass

    def _start_server_in_background(self, host, port):
        """Start the WebSocket server in a background thread"""
        def _run():
            try:
                start_simple_ws_server(host=host, port=port)
            except Exception as e:
                self.logger.error(f"WebSocket server error: {e}")

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        time.sleep(0.5)  # Wait for the server to start
        self.logger.info(f"WebSocket server started in background: ws://{host}:{port}")

    def _connect(self):
        """Establish WebSocket connection"""
        try:
            self._ws = websocket.create_connection(
                self._ws_url,
                timeout=30,
            )
            # Send subscribe command
            subscribe_cmd = {
                'command': 'subscribe',
                'queue': self._queue_name,
            }
            self._ws.send(json.dumps(subscribe_cmd))
            self.logger.info(f"WebSocket connected and subscribed to queue: {self._queue_name}")
            return True
        except Exception as e:
            self.logger.warning(f"WebSocket connection failed: {e}")
            self._ws = None
            return False

    def _dispatch_task(self):
        """
        Core dispatch method.
        Receives WebSocket messages and submits tasks.
        """
        self._running = True

        while self._running:
            # Ensure connection is established
            if self._ws is None or not self._ws.connected:
                if not self._connect():
                    time.sleep(self._reconnect_interval)
                    continue

            try:
                # Receive message (blocking)
                raw_message = self._ws.recv()
                if not raw_message:
                    continue

                # Parse message
                envelope = json.loads(raw_message)

                # Check if this message is for the target queue
                if envelope.get('queue') != self._queue_name:
                    continue

                body = envelope.get('body')
                if body is None:
                    continue

                # If body is a string, parse it as a dict
                if isinstance(body, str):
                    body = json.loads(body)

                # Wrap as kw and submit task
                kw = {
                    'body': body,
                    'message_id': envelope.get('message_id'),
                }
                self._submit_task(kw)

            except websocket.WebSocketTimeoutException:
                # Timeout is normal, continue loop
                continue
            except websocket.WebSocketConnectionClosedException:
                self.logger.warning("WebSocket connection closed, attempting to reconnect...")
                self._ws = None
                time.sleep(self._reconnect_interval)

    def _confirm_consume(self, kw):
        """
        Confirm successful consumption.
        WebSocket usually does not require ACK, but a confirmation command can be sent to the server.
        """
        message_id = kw.get('message_id')
        if message_id and self._ws and self._ws.connected:
            try:
                ack_cmd = {
                    'command': 'ack',
                    'queue': self._queue_name,
                    'message_id': message_id,
                }
                self._ws.send(json.dumps(ack_cmd))
            except Exception as e:
                self.logger.debug(f"Failed to send ACK: {e}")

    def _requeue(self, kw):
        """
        Requeue message.
        Sends a requeue command to the server.
        """
        message_id = kw.get('message_id')
        body = kw.get('body')
        if self._ws and self._ws.connected:
            try:
                requeue_cmd = {
                    'command': 'requeue',
                    'queue': self._queue_name,
                    'message_id': message_id,
                    'body': body,
                }
                self._ws.send(json.dumps(requeue_cmd))
            except Exception as e:
                self.logger.warning(f"Requeue failed: {e}")


# ============================================================================
# Register Broker
# ============================================================================

BROKER_KIND_WEBSOCKET = 'WEBSOCKET'

register_broker_exclusive_config_default(
    BROKER_KIND_WEBSOCKET,
    {
        'ws_url': 'ws://localhost:8765',         # WebSocket server address
        'reconnect_interval': 5,                  # Reconnect interval (seconds)
    }
)

register_custom_broker(BROKER_KIND_WEBSOCKET, WebSocketPublisher, WebSocketConsumer)


# ============================================================================
# Simple WebSocket server (for testing)
# ============================================================================

logger_ws_server = get_funboost_file_logger('websocket_server', log_level_int=logging.INFO)

def start_simple_ws_server(host='localhost', port=8765):
    """
    Start a simple WebSocket server for testing

    Requires: pip install websockets
    """
    try:
        import asyncio
        import websockets
    except ImportError:
        raise ImportError("Please install websockets: pip install websockets")

    # Store subscribers (no message caching; WebSocket is real-time)
    subscribers = {}  # {queue_name: [websocket]}

    async def handler(ws):
        logger_ws_server.info(f"New connection: {ws.remote_address}")
        subscribed_queue = None

        try:
            async for message in ws:
                data = json.loads(message)
                command = data.get('command')
                queue_name = data.get('queue')

                if command == 'subscribe':
                    # Subscribe to queue
                    subscribed_queue = queue_name
                    if queue_name not in subscribers:
                        subscribers[queue_name] = []
                    subscribers[queue_name].append(ws)
                    logger_ws_server.info(f"Client subscribed to queue: {queue_name}")

                elif command == 'clear':
                    # Clear (WebSocket has no buffer, nothing to do)
                    pass

                elif command == 'ack':
                    # ACK (not needed in WebSocket mode)
                    pass

                elif command == 'requeue':
                    # Requeue: send directly to subscribers again
                    body = data.get('body')
                    if queue_name in subscribers:
                        requeue_msg = json.dumps({
                            'queue': queue_name,
                            'body': body,
                            'message_id': data.get('message_id'),
                        })
                        for subscriber in subscribers[queue_name]:
                            try:
                                await subscriber.send(requeue_msg)
                            except Exception as e:
                                logger_ws_server.error(f"Requeue send failed: {e}")

                elif command == 'publish' or command is None:
                    # Publish message: dispatch to subscribers; discard if no subscribers
                    if queue_name in subscribers and subscribers[queue_name]:
                        for subscriber in subscribers[queue_name]:
                            try:
                                await subscriber.send(message)
                            except Exception as e:
                                print(f"Send failed (connection may be closed): {e}")
                        logger_ws_server.debug(f"Message dispatched: {queue_name}")
                    else:
                        logger_ws_server.warning(f"Message discarded (no subscribers): {queue_name}")

        except websockets.ConnectionClosed:
            logger_ws_server.info(f"Connection closed normally: {ws.remote_address}")
        finally:
            # Remove subscriber
            if subscribed_queue and subscribed_queue in subscribers:
                if ws in subscribers[subscribed_queue]:
                    subscribers[subscribed_queue].remove(ws)

    async def main():
        async with websockets.serve(handler, host, port):
            logger_ws_server.info(f"WebSocket server started: ws://{host}:{port}")
            await asyncio.Future()  # Run forever

    asyncio.run(main())


if __name__ == '__main__':
    pass