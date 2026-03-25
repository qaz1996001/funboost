# -*- coding: utf-8 -*-
"""
Publish WebSocket messages

Run this script directly to publish test messages
Note: The WebSocket server (start_ws_server.py) must be started first
"""

from start_consume import process_message

if __name__ == '__main__':
    print("=" * 50)
    print("Publishing WebSocket Messages")
    print("=" * 50)

    total_cnt = 20000

    for i in range(total_cnt):
        process_message.push(x=i, y=i * 10)
        if i%1000==0:
            print(f"Published: {i}/{total_cnt}")

    print("=" * 50)
    print(f"Publishing complete! Total {total_cnt} messages")
    print("=" * 50)
