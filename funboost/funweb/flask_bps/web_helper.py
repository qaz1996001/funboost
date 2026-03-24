
# -*- coding: utf-8 -*-
"""Maximum duration (in seconds) for SSE real-time log streaming.

The LOG_STREAM_MAX_MS value in the frontend scripts for deployment details and log viewer
must match this value (multiplied by 1000 to convert to milliseconds).
"""
import socket
import os

LOG_STREAM_MAX_SECONDS = 300


def _get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = socket.gethostbyname(socket.gethostname())
    return ip

def _get_local_hostname():
    return socket.gethostname()

# LOCAL_IP = _get_local_ip()  # On Windows with different networks, the IP address can change frequently

LOCAL_IP = _get_local_hostname()

if os.getenv('FUNWEB_LOCAL_IP'): # If the environment variable FUNWEB_LOCAL_IP is set, use its value
    LOCAL_IP = os.getenv('FUNWEB_LOCAL_IP')