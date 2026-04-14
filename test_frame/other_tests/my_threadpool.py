import threading
import queue
import time
import atexit


class DynamicThreadPool:
    """
    A dynamic thread pool that automatically scales the number of threads based on load.
    """

    def __init__(self, min_workers=2, max_workers=10, idle_timeout=60):
        if min_workers <= 0 or max_workers < min_workers:
            raise ValueError("Unreasonable thread count configuration (0 < min_workers <= max_workers)")

        self.min_workers = min_workers
        self.max_workers = max_workers
        self.idle_timeout = idle_timeout  # seconds

        self._task_queue = queue.Queue()
        self._workers = set()  # Use a set for fast add/remove
        self._workers_lock = threading.Lock()

        self._is_shutdown = False
        self._shutdown_lock = threading.Lock()

        # Initialize core threads
        for _ in range(self.min_workers):
            self._create_worker()

        # Create a "manager" thread responsible for monitoring and scaling up
        self._manager_thread = threading.Thread(target=self._manager_loop)
        self._manager_thread.daemon = True
        self._manager_thread.start()

        atexit.register(self.shutdown)

    def _create_worker(self):
        """Safely create a worker thread."""
        with self._workers_lock:
            if len(self._workers) >= self.max_workers:
                return  # Already at maximum thread count

            worker = threading.Thread(target=self._worker_loop)
            worker.daemon = True
            worker.start()
            self._workers.add(worker)
            print(f"📈 Thread count in pool: {len(self._workers)}. Created a new thread: {worker.name}")

    def _remove_worker(self, worker):
        """Safely remove a worker thread, ensuring the count doesn't drop below core count."""
        with self._workers_lock:
            # Add safety check to prevent over-removal
            if len(self._workers) <= self.min_workers:
                return
            if worker in self._workers:
                self._workers.remove(worker)
                # This line can now be triggered!
                print(f"📉 Thread count in pool: {len(self._workers)}. Removed an idle thread: {worker.name}")

    def _worker_loop(self):
        """
        Worker thread loop.
        Core threads wait indefinitely; temporary threads exit after idle timeout.
        """
        while True:
            try:
                with self._workers_lock:
                    is_temporary_worker = len(self._workers) > self.min_workers

                timeout = self.idle_timeout if is_temporary_worker else None
                func, args, kwargs = self._task_queue.get(timeout=timeout)

                try:
                    func(*args, **kwargs)
                except Exception as e:
                    print(f"Error occurred while executing task: {e}")
                finally:
                    self._task_queue.task_done()

            except queue.Empty:
                # Only temporary threads reach here after timeout.
                # Since it timed out, it should be destroyed. Remove with double-check.
                self._remove_worker(threading.current_thread())
                return  # Thread self-terminates

    def _manager_loop(self):
        """
        "Manager" thread loop, responsible for scaling up on demand.
        """
        while not self._is_shutdown:
            time.sleep(1)  # Check once per second

            # Scale-up strategy: when pending tasks > current thread count and max not reached, scale up
            if self._task_queue.qsize() > len(self._workers) and len(self._workers) < self.max_workers:
                print("🚀 Task backlog detected, manager decided to scale up...")
                self._create_worker()

    def submit(self, func, *args, **kwargs):
        """Submit a task to the task queue."""
        with self._shutdown_lock:
            if self._is_shutdown:
                raise RuntimeError("Thread pool has been shut down, cannot submit new tasks")
            self._task_queue.put((func, args, kwargs))

    def shutdown(self, wait=True):
        """
        Gracefully shut down the thread pool, including the manager thread and all worker threads.
        """
        with self._shutdown_lock:
            if self._is_shutdown:
                return
            print("\n--- atexit: Program exit detected, starting thread pool shutdown... ---")
            self._is_shutdown = True

        if wait:
            self._task_queue.join()
            # Wait for manager thread to exit
            # self._manager_thread.join() # No need to manually join since it's a daemon thread

        print("--- atexit: All tasks completed, program will exit cleanly. ---")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        return False


# --- Test code ---
if __name__ == '__main__':
    import random


    def simple_task(task_id, duration):
        print(f"Thread {threading.current_thread().name} starting task {task_id}...")
        time.sleep(duration)
        print(f"✅ Thread {threading.current_thread().name} completed task {task_id}.")


    print("\n--- Testing Dynamic Thread Pool DynamicThreadPool ---")

    # Create a pool with 2 core threads, max 10, idle threads destroyed after 5 seconds
    pool = DynamicThreadPool(min_workers=1, max_workers=10, idle_timeout=5)

    # First wave: submit a large number of tasks at once to trigger scale-up
    print("\n>>> First wave: Submit 15 tasks, observe scale-up...")
    for i in range(15):
        pool.submit(simple_task, task_id=f"B1-{i}", duration=2)

    # Wait for a while for tasks to be consumed, and observe threads shrinking due to idleness
    print("\n>>> Wait 20 seconds, observe whether temporary threads will be automatically destroyed...")
    time.sleep(20)

    # Second wave: submit a small number of tasks again
    print("\n>>> Second wave: Submit 3 tasks...")
    for i in range(3):
        pool.submit(simple_task, task_id=f"B2-{i}", duration=1)

    print("\nAll tasks submitted. Main thread is about to end, waiting for atexit to auto-cleanup...")
    # After the main thread ends, atexit calls shutdown, waiting for all tasks to complete
    # You will see the thread count first increase, then decrease to min_workers when idle
