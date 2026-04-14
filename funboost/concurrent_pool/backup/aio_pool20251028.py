import asyncio
from typing import Callable, Any, Optional, Coroutine, TypeVar
from asyncio import Queue
from concurrent.futures import Future
import threading
from functools import wraps

T = TypeVar('T')


class AsyncioPool:
    """Async concurrent pool, specifically designed for executing async def functions"""
    
    def __init__(
        self,
        max_workers: int = 10,
        queue_size: int = 0,
        loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        """
        Initialize the concurrent pool

        Args:
            max_workers: Maximum number of concurrent workers
            queue_size: Work queue size, 0 means unlimited
            loop: Event loop, if None it will be automatically obtained
        """
        self.max_workers = max_workers
        self.queue_size = queue_size
        self._loop = loop
        self._work_queue: Optional[Queue] = None
        self._workers = []
        self._started = False
        self._shutdown = False
        self._lock = threading.Lock()
        
    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop"""
        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                # If there's no running loop, try to get the default loop
                try:
                    self._loop = asyncio.get_event_loop()
                except RuntimeError:
                    self._loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self._loop)
        return self._loop
    
    async def start(self):
        """Start the concurrent pool"""
        if self._started:
            return
        
        self._started = True
        self._shutdown = False
        
        # Create work queue
        if self.queue_size > 0:
            self._work_queue = Queue(maxsize=self.queue_size)
        else:
            self._work_queue = Queue()
        
        # Start worker coroutines
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)
    
    async def _worker(self, worker_id: int):
        """Worker coroutine that continuously gets tasks from the queue and executes them"""
        while not self._shutdown:
            try:
                # Wait for task
                task_item = await self._work_queue.get()
                
                if task_item is None:  # Termination signal
                    self._work_queue.task_done()
                    break
                
                coro_func, args, kwargs, future = task_item
                
                try:
                    # Execute async task
                    result = await coro_func(*args, **kwargs)
                    
                    # Set result
                    if not future.done():
                        self.loop.call_soon_threadsafe(future.set_result, result)
                        
                except Exception as e:
                    # Set exception
                    if not future.done():
                        self.loop.call_soon_threadsafe(future.set_exception, e)
                finally:
                    self._work_queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
    
    async def aio_submit(
        self,
        coro_func: Callable[..., Coroutine[Any, Any, T]],
        *args,
        **kwargs
    ) -> T:
        """
        Asynchronously submit a task to the concurrent pool

        Args:
            coro_func: Async function (async def)
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Task execution result

        Raises:
            RuntimeError: If the pool is shutting down
            TypeError: If the submitted function is not async
        """
        if not asyncio.iscoroutinefunction(coro_func):
            raise TypeError(f"{coro_func} is not a coroutine function (async def)")
        
        if not self._started:
            await self.start()
        
        if self._shutdown:
            raise RuntimeError("Pool is shutting down")
        
        # Create asyncio Future object
        future = self.loop.create_future()

        # Put task into queue
        await self._work_queue.put((coro_func, args, kwargs, future))

        # Wait for result
        return await future
    
    def submit(
        self,
        coro_func: Callable[..., Coroutine[Any, Any, T]],
        *args,
        **kwargs
    ) -> Future:
        """
        Synchronously submit a task to the concurrent pool (returns a concurrent.futures.Future object)

        Args:
            coro_func: Async function (async def)
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            concurrent.futures.Future object

        Raises:
            TypeError: If the submitted function is not async
        """
        if not asyncio.iscoroutinefunction(coro_func):
            raise TypeError(f"{coro_func} is not a coroutine function (async def)")
        
        # Create thread-safe Future
        future = Future()
        
        async def _submit_task():
            try:
                if not self._started:
                    await self.start()
                
                if self._shutdown:
                    raise RuntimeError("Pool is shutting down")
                
                # Create asyncio Future
                asyncio_future = self.loop.create_future()
                
                # Put task into queue
                await self._work_queue.put((coro_func, args, kwargs, asyncio_future))
                
                # Wait for result and set it on the thread-safe Future
                result = await asyncio_future
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
        
        # Schedule task in the event loop
        asyncio.run_coroutine_threadsafe(_submit_task(), self.loop)
        
        return future
    
    async def map(
        self,
        coro_func: Callable[..., Coroutine[Any, Any, T]],
        *iterables
    ) -> list[T]:
        """
        Async map operation, applies an async function to each element in the iterables

        Args:
            coro_func: Async function
            *iterables: Iterables

        Returns:
            List of results
        """
        tasks = []
        for args in zip(*iterables):
            task = self.aio_submit(coro_func, *args)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    async def shutdown(self, wait: bool = True):
        """
        Shut down the concurrent pool

        Args:
            wait: Whether to wait for all tasks to complete
        """
        if self._shutdown:
            return
        
        self._shutdown = True
        
        if wait and self._work_queue is not None:
            # Wait for tasks in the queue to complete
            await self._work_queue.join()
        
        # Send termination signal to all workers
        for _ in range(len(self._workers)):
            if self._work_queue is not None:
                await self._work_queue.put(None)
        
        # Wait for all workers to finish
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        
        self._workers.clear()
        self._started = False
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.shutdown(wait=True)
        return False
    
    def qsize(self) -> int:
        """Get current queue size"""
        if self._work_queue is None:
            return 0
        return self._work_queue.qsize()
    
    def pending(self) -> int:
        """Get the number of pending tasks (tasks in the queue)"""
        return self.qsize()
    
    def is_shutdown(self) -> bool:
        """Check if the pool has been shut down"""
        return self._shutdown


# ==================== Usage Examples ====================

async def example_aio_submit():
    """Example: Using aio_submit for async submission"""
    print("\n=== aio_submit async submission example ===")
    
    # Create concurrent pool: max 5 concurrent workers, queue size 10
    pool = AsyncioPool(max_workers=5, queue_size=10)
    
    async def fetch_data(task_id: int, delay: float):
        """Simulate async task"""
        print(f"Task {task_id} started")
        await asyncio.sleep(delay)
        print(f"Task {task_id} completed")
        return f"Result-{task_id}"
    
    async with pool:
        # Submit multiple tasks
        tasks = []
        for i in range(10):
            task = pool.aio_submit(fetch_data, i, 0.5)
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        print(f"\nAll results: {results}")


def example_sync_submit():
    """Example: Using submit for sync submission"""
    print("\n=== submit sync submission example ===")
    
    async def process_item(item_id: int):
        """Process a single item"""
        await asyncio.sleep(0.5)
        return f"Processed-{item_id}"
    
    # Create event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Create concurrent pool
    pool = AsyncioPool(max_workers=3, queue_size=5, loop=loop)

    # Run event loop in a separate thread
    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()
    
    import threading
    loop_thread = threading.Thread(target=run_loop, daemon=True)
    loop_thread.start()
    
    # Synchronously submit tasks
    futures = []
    for i in range(10):
        future = pool.submit(process_item, i)
        futures.append(future)
        print(f"Submitted task {i}")
    
    # Wait for all tasks to complete
    results = []
    for i, future in enumerate(futures):
        result = future.result(timeout=10)
        results.append(result)
        print(f"Task {i} result: {result}")
    
    print(f"\nAll results: {results}")

    # Cleanup
    asyncio.run_coroutine_threadsafe(pool.shutdown(), loop).result()
    loop.call_soon_threadsafe(loop.stop)
    loop_thread.join(timeout=2)


async def example_map():
    """Example: Using map for batch processing"""
    print("\n=== map batch processing example ===")
    
    pool = AsyncioPool(max_workers=4, queue_size=20)
    
    async def square(x: int):
        """Calculate square"""
        await asyncio.sleep(0.1)
        return x * x
    
    async with pool:
        numbers = range(1, 11)
        results = await pool.map(square, numbers)
        print(f"Square results: {results}")


async def example_error_handling():
    """Example: Error handling"""
    print("\n=== Error handling example ===")
    
    pool = AsyncioPool(max_workers=3, queue_size=5)
    
    async def risky_task(task_id: int):
        """A task that may fail"""
        await asyncio.sleep(0.2)
        if task_id % 3 == 0:
            raise ValueError(f"Task {task_id} failed!")
        return f"Success-{task_id}"
    
    async with pool:
        tasks = []
        for i in range(10):
            task = pool.aio_submit(risky_task, i)
            tasks.append(task)
        
        # Collect results, handle exceptions
        for i, task in enumerate(tasks):
            try:
                result = await task
                print(f"Task {i}: {result}")
            except ValueError as e:
                print(f"Task {i}: Error - {e}")


async def example_queue_monitoring():
    """Example: Queue monitoring"""
    print("\n=== Queue monitoring example ===")
    
    pool = AsyncioPool(max_workers=2, queue_size=5)
    
    async def slow_task(task_id: int):
        """Slow task"""
        print(f"  [Worker] Processing task {task_id}")
        await asyncio.sleep(1)
        return task_id
    
    async with pool:
        # Submit tasks and monitor queue
        tasks = []
        for i in range(12):
            print(f"Submitting task {i}, queue size: {pool.qsize()}, pending: {pool.pending()}")
            task = pool.aio_submit(slow_task, i)
            tasks.append(task)
            await asyncio.sleep(0.2)
        
        print(f"\nAll tasks submitted, waiting for completion...")
        results = await asyncio.gather(*tasks)
        print(f"All tasks completed: {len(results)} total")


async def example_real_world_crawler():
    """Example: Simulated web crawler scenario"""
    print("\n=== Web crawler scenario example ===")
    
    # Limit concurrency to 5 to avoid overloading the target server
    pool = AsyncioPool(max_workers=5, queue_size=20)
    
    async def fetch_url(url: str):
        """Simulate fetching a URL"""
        print(f"Fetching {url}...")
        await asyncio.sleep(0.5)  # Simulate network latency
        return f"Content from {url}"
    
    urls = [f"https://example.com/page/{i}" for i in range(20)]
    
    async with pool:
        results = await pool.map(fetch_url, urls)
        print(f"\nSuccessfully fetched {len(results)} pages")


# Run all examples
if __name__ == "__main__":
    print("=" * 60)
    print("AsyncioPool Example Demonstration")
    print("=" * 60)
    
    # Async examples
    asyncio.run(example_aio_submit())
    asyncio.run(example_map())
    asyncio.run(example_error_handling())
    asyncio.run(example_queue_monitoring())
    asyncio.run(example_real_world_crawler())
    
    # Sync examples
    example_sync_submit()