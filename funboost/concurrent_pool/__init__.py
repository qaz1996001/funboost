# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 9:46
"""
Concurrent pools including:
- Bounded queue thread pool with error reporting
- Eventlet coroutine pool
- Gevent coroutine pool
- Custom bounded queue thread pool with error reporting, where thread count can automatically shrink when there are fewer tasks. This is the default concurrency method used in the project.

This folder contains 5 types of concurrent pools that can be used independently in any project, even without this function scheduling framework.
"""
from .base_pool_type import FunboostBaseConcurrentPool
from .async_pool_executor import AsyncPoolExecutor
from .bounded_threadpoolexcutor import BoundedThreadPoolExecutor
from .custom_threadpool_executor import CustomThreadPoolExecutor
from .flexible_thread_pool import FlexibleThreadPool
from .pool_commons import ConcurrentPoolBuilder