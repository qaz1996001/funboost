# -*- coding: utf-8 -*-
"""
Start the WebSocket consumer

The Consumer will automatically start the WebSocket server; no manual startup needed
"""

import time
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent))

from funboost import BrokerEnum
from funboost import boost, BoosterParams


@boost(BoosterParams(
    queue_name='test_websocket_queue',
    broker_kind=BrokerEnum.WEBSOCKET,
    # qps=10,
    concurrent_num=3,
    log_level=logging.INFO,
    broker_exclusive_config={
        'ws_url': 'ws://localhost:8765',
        'reconnect_interval': 3,
    }
))
def process_message(x, y):
    """Process WebSocket message"""
    result = x + y
    if x % 1000 == 0:
        print(f"Processing message: {x} + {y} = {result}")
    return result


if __name__ == '__main__':
    print("=" * 50)
    print("WebSocket Consumer")
    print("=" * 50)
    print("Server will start automatically. Press Ctrl+C to stop.")
    print("=" * 50)
    
    process_message.consume()
