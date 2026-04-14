# -*- coding: utf-8 -*-
"""
Start the WebSocket test server

Run this script directly to start the server
"""

from websocket_broker import start_simple_ws_server

if __name__ == '__main__':
    print("=" * 50)
    print("WebSocket Test Server")
    print("=" * 50)
    print("Listening at: ws://localhost:8765")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    start_simple_ws_server(host='localhost', port=8765)
