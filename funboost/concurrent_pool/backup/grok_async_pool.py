import asyncio
import queue
import threading
from concurrent.futures import Future,ThreadPoolExecutor
import time
from flask.cli import traceback
import nb_log
import uuid

from funboost.concurrent_pool.async_helper import simple_run_in_executor

class AsyncPool:
    def __init__(self, size, loop=None,min_tasks=1,  idle_timeout=1):
        # Initialize parameters
        self.min_tasks = min_tasks
        self.max_tasks = size
        self.sync_queue = queue.Queue(maxsize=size)  # Sync queue
        # self.async_queue = asyncio.Queue(maxsize=size)  # Async queue
        self.loop = asyncio.new_event_loop()  # Create event loop
        self.workers = set()  # Worker coroutine set
        self._lock = threading.Lock()
        self._lock_for_adjust = threading.Lock()
        self.idle_timeout = idle_timeout

        self.async_queue = None
        def create_async_queue():
            self.async_queue = asyncio.Queue(maxsize=size)
        self.loop.call_soon_threadsafe(create_async_queue)

        # Start event loop thread
        self.loop_thread = threading.Thread(target=self._run_loop, daemon=False)
        self.loop_thread.start()
        print("Event loop thread started")

        # Start task transfer coroutine
        asyncio.run_coroutine_threadsafe(self._transfer_tasks(),self.loop )
        print("Task transfer coroutine started")

        # Initialize worker coroutines
        # self._adjust_workers(min_tasks)
        # print(f"Initialized {min_tasks} worker coroutines")

    def _run_loop(self):
        """Run the event loop"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _transfer_tasks(self):
        """Transfer tasks from sync queue to async queue"""
        while True:
            try:
                task =await simple_run_in_executor(self.sync_queue.get,timeout=0.1,async_loop=self.loop)
                await self.async_queue.put(task)
                print("Task transferred to async queue")
            except Exception: 
                print(traceback.format_exc())
                
            # try:
            #     task = self.sync_queue.get(timeout=0.01)
            #     self.sync_queue.task_done()
            #     print("Task transferred to async queue")
            #     await self.async_queue.put(task)
            # except queue.Empty:
            #     await asyncio.sleep(0.01)
         

    async def _worker(self,worker_uuid):
        """Worker coroutine, processes tasks"""
        while True:
            try:
                print(f"Worker coroutine waiting for task...  {self.async_queue.qsize()}")
                coro, args, kwargs, future = await asyncio.wait_for(
                    self.async_queue.get(), timeout=self.idle_timeout
                )
                print("Worker coroutine got a task")
               
                try:
                    result = await coro(*args, **kwargs)  # Execute async task
                    future.set_result(result)
                    print(f"Task completed, result: {result}")
                except Exception as e:
                    future.set_exception(e)
                    print(f"Task failed: {e}")
                finally:
                    pass
                    # self.async_queue.task_done()
                    if len(self.workers) > self.max_tasks:
                        print("Worker coroutine count exceeded, preparing to exit")
                        with self._lock:
                            self.workers.remove(worker_uuid)
                        return
            except asyncio.TimeoutError:
                with self._lock:
                    if len(self.workers) > self.min_tasks:
                        print("Worker coroutine task acquisition timed out, preparing to exit")
                        self.workers.remove(worker_uuid)
                        return
            except Exception as e:
                traceback.print_exc()
                return

    # def _adjust_workers(self, target_count):
    #     """Adjust worker coroutine count"""
    #     with self._lock_for_adjust:
    #         current_count = len(self.workers)
    #         if target_count > current_count and current_count < self.max_tasks:
    #             for _ in range(target_count - current_count):
    #                 worker = asyncio.run_coroutine_threadsafe(self._worker(), self.loop)
    #                 self.workers.add(worker)
    #                 print(f"Added worker coroutine, total: {len(self.workers)}")

    def submit(self, coro, *args, **kwargs):
        """Submit a task"""
        if not asyncio.iscoroutinefunction(coro):
            raise ValueError("Submitted function must be an async def coroutine")

        future = Future()
        task = (coro, args, kwargs, future)
        
        self.sync_queue.put(task)  # Submit task to sync queue
        print("Task submitted to sync queue")
        if len(self.workers) < self.max_tasks:
            uuidx = uuid.uuid4()
            asyncio.run_coroutine_threadsafe(self._worker(uuidx), self.loop)
            self.workers.add(uuidx)
            print(f"Added worker coroutine, total: {len(self.workers)}")
        return future



# Test function
async def example_task(n):
    # print(f"example_task {n} started")
    await asyncio.sleep(1)
    print(f"example_task {n} completed")
    return n * 2

# Main program
if __name__ == "__main__":
    pool = AsyncPool(5)
    for i in range(20):
        pool.submit(example_task, i)
    # for i, f in enumerate(futures):
    #     print(f"Task {i} result: {f.result()}")  # Wait and get result
    # pool.shutdown()

    
    time.sleep(20)
    print('New round of submissions')
    for i in range(20):
        pool.submit(example_task, 100+i)
