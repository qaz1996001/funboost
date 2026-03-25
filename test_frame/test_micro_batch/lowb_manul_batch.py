# -*- coding: utf-8 -*-
"""
Manual batch aggregation without encapsulation - not using funboost

This is how many developers write it without funboost:
directly cluttering business code with global variables, locks, threads...

Look how messy and bug-prone it is.
"""

import threading
import time
from queue import Queue

# ============================================================
# Your business code suddenly has a bunch of global variables...
# ============================================================

# Global buffer (you must maintain it yourself)
_buffer = []

# Global lock (you must add it yourself)
_lock = threading.Lock()

# Last flush time (you must track it yourself)
_last_flush_time = time.time()

# Configuration (hard-coded here, annoying to change)
BATCH_SIZE = 10
BATCH_TIMEOUT = 3.0

# Flag to control background thread
_running = True


def batch_insert_to_db(items):
    """Pretend this is your bulk insert function"""
    print(f"{time.strftime('%H:%M:%S')} Batch insert {len(items)} items: {items}")


def _flush_if_needed():
    """
    Check and flush - you need to call this after every data addition

    Problem: what if you forget to call it?
    """
    global _buffer, _last_flush_time

    if len(_buffer) >= BATCH_SIZE:
        batch = _buffer[:]
        _buffer = []
        _last_flush_time = time.time()

        try:
            batch_insert_to_db(batch)
        except Exception as e:
            # What if it fails? Data lost!
            print(f"Failed, lost {len(batch)} items: {e}")


def _timeout_flush_thread():
    """
    Background timeout flush thread - you must write this yourself

    Problems:
    1. daemon=True: data may be lost when main thread exits
    2. non-daemon: program may not exit cleanly
    3. What if you forget to start it?
    """
    global _buffer, _last_flush_time, _running

    while _running:
        time.sleep(1)  # Poll interval - hardcode or configure?

        with _lock:
            elapsed = time.time() - _last_flush_time
            if _buffer and elapsed >= BATCH_TIMEOUT:
                batch = _buffer[:]
                _buffer = []
                _last_flush_time = time.time()

                try:
                    batch_insert_to_db(batch)
                except Exception as e:
                    print(f"Timeout flush failed: {e}")


def add_data(item):
    """
    Add data - business code calls this

    Problems:
    1. Must remember to lock
    2. Must remember to call flush
    3. Called from multiple places, easy to miss
    """
    global _buffer

    with _lock:
        _buffer.append(item)
        _flush_if_needed()


def graceful_shutdown():
    """
    Graceful shutdown - you must call this yourself

    Problem: if you forget to call it, the last batch of data is lost
    """
    global _running, _buffer

    _running = False

    with _lock:
        if _buffer:
            print(f"Flushing remaining {len(_buffer)} items before shutdown...")
            batch = _buffer[:]
            _buffer = []
            batch_insert_to_db(batch)


# ============================================================
# You also need to start the background thread somewhere...
# ============================================================

def init_batch_system():
    """
    Initialization - you must remember to call this at program startup

    Problem: if you forget to call it, timeout flush won't work
    """
    t = threading.Thread(target=_timeout_flush_thread, daemon=True)
    t.start()
    print("Background thread started (remember to call graceful_shutdown)")


# ============================================================
# Tests
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Manual batch aggregation - see how troublesome it is")
    print("=" * 60)

    # You must remember to initialize
    init_batch_system()

    # Simulate business data
    print("\nSimulating 25 data items...\n")
    for i in range(25):
        add_data({"id": i, "value": f"data_{i}"})
        print(f"  {time.strftime('%H:%M:%S')} Added: id={i}")
        time.sleep(0.1)

    # Wait for timeout flush
    print(f"\nWaiting {BATCH_TIMEOUT}s for timeout flush of remaining data...\n")
    time.sleep(BATCH_TIMEOUT + 1)

    # You must remember to call graceful shutdown
    graceful_shutdown()

    print("\n" + "=" * 60)
    print("Summary: problems with manual approach")
    print("=" * 60)
    print("""
1. Global variable pollution: _buffer, _lock, _last_flush_time, _running...
2. Easy to forget:
   - Forgot to start background thread -> timeout flush doesn't work
   - Forgot to lock -> data race
   - Forgot graceful_shutdown -> last batch of data lost
3. Code scattered: init, add, flush, shutdown spread across the codebase
4. Not reusable: have to rewrite from scratch for the next project
5. Hard to test: global state is hard to mock

Whereas funboost MicroBatchConsumerMixin:
   - 0 global variables
   - 2 configuration parameters
   - Automatic lifecycle management
   - Works out of the box
""")
