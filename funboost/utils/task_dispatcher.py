

import inspect
import asyncio
from functools import wraps
from typing import Callable, Any

class LocalFunctionsDispatcher:
    """
    Local in-memory function dispatch and execution.
    """
    def __init__(self):
        self._registry = {}

    def task(self, name: str = None):
        """Decorator to register a task"""
        def decorator(func: Callable):
            task_name = name or func.__name__
            if task_name in self._registry:
                raise ValueError(f"Task '{task_name}' is already registered")
            sig = inspect.signature(func)
            self._registry[task_name] = (func, sig)  # Store the original function directly
            return func
        return decorator

    def run(self, task_name: str, *args, **kwargs) -> Any:
        """Synchronously call a task. Does not support directly awaiting async functions."""
        if task_name not in self._registry:
            raise ValueError(f"Task '{task_name}' not registered")
        
        func, sig = self._registry[task_name]
        sig.bind(*args, **kwargs)  # Parameter validation

        if inspect.iscoroutinefunction(func):
            # If it's an async function, use asyncio.run to call it (available in main thread)
            return asyncio.run(func(*args, **kwargs))
        else:
            return func(*args, **kwargs)

    async def aio_run(self, task_name: str, *args, **kwargs) -> Any:
        """Asynchronously call a task. Regular functions are executed via thread pool."""
        if task_name not in self._registry:
            raise ValueError(f"Task '{task_name}' not registered")
        
        func, sig = self._registry[task_name]
        sig.bind(*args, **kwargs)  # Parameter validation

        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Regular functions run via thread pool, not blocking the event loop
            return await asyncio.to_thread(func, *args, **kwargs)


if __name__ == '__main__':
    dispatcher = LocalFunctionsDispatcher()

    @dispatcher.task()
    def add(a, b):
        return a + b

    @dispatcher.task(name='mul_task')
    async def mul(a, b):
        await asyncio.sleep(0.1)
        return a * b

    print(add(1,2)) # Direct call

    # Synchronous call
    print(dispatcher.run("add", 2, 3))  # 5
    print(dispatcher.run("mul_task", 4, 5))  # 20，asyncio.run 自动运行

    # Asynchronous call
    async def main():
        print(await dispatcher.aio_run("add", 6, 7))  # 13
        print(await dispatcher.aio_run("mul_task", 3, 5))  # 15

    asyncio.run(main())
