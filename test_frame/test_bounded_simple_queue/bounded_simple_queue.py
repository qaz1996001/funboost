# -*- coding: utf-8 -*-
"""
Bounded SimpleQueue: SimpleQueue + Semaphore
"""

import threading
from queue import SimpleQueue, Empty as QueueEmpty


class BoundedSimpleQueue:
    """Bounded SimpleQueue, implements backpressure using a semaphore"""

    __slots__ = ('_queue', '_semaphore', '_maxsize')

    def __init__(self, maxsize: int = 0):
        self._queue = SimpleQueue()
        self._maxsize = maxsize if maxsize > 0 else 0
        self._semaphore = threading.Semaphore(maxsize) if maxsize > 0 else None

    def put(self, item, block=True, timeout=None):
        """Put a message; blocks when queue is full"""
        if self._semaphore is not None:
            acquired = self._semaphore.acquire(blocking=block, timeout=timeout)
            if not acquired:
                raise Full()
            try:
                self._queue.put(item)
            except:
                self._semaphore.release()
                raise
        else:
            self._queue.put(item)

    def get(self, block=True, timeout=None):
        """Get a message"""
        try:
            item = self._queue.get(block=block, timeout=timeout)
        except QueueEmpty:
            raise Empty()
        if self._semaphore is not None:
            self._semaphore.release()
        return item

    def qsize(self):
        return self._queue.qsize()

    def empty(self):
        return self._queue.empty()


class Empty(Exception):
    pass


class Full(Exception):
    pass


class BoundedSimpleQueues:
    """Bounded SimpleQueue manager"""

    _queues = {}
    _lock = threading.Lock()

    @classmethod
    def get_queue(cls, queue_name: str, maxsize: int = 10000):
        if queue_name not in cls._queues:
            with cls._lock:
                if queue_name not in cls._queues:
                    cls._queues[queue_name] = BoundedSimpleQueue(maxsize=maxsize)
        return cls._queues[queue_name]


if __name__ == '__main__':
    import time
    import queue

    n = 1000000
    print(f"Testing {n:,} put + get operations:")

    # q = BoundedSimpleQueue(maxsize=n)
    q = queue.Queue(maxsize=n)
    t0 = time.time()
    for i in range(n):
        q.put(i)
    print(f"  put: {time.time()-t0:.3f}s, {n/(time.time()-t0):,.0f} ops/sec")

    t0 = time.time()
    for i in range(n):
        q.get()
    print(f"  get: {time.time()-t0:.3f}s, {n/(time.time()-t0):,.0f} ops/sec")
