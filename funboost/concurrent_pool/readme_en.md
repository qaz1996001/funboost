#### This directory contains implementations of various concurrent pools. The framework uses different types of concurrent pools to execute function tasks with different concurrency modes.

```python

'''
All concurrent pool APIs implement submit, which then automatically executes the function. Similar to the concurrent.futures package API.
'''


def fun(x):
    print(x)

pool = Pool(50)
pool.submit(fun,1)


```

```text
Implemented pools include:


gevent

eventlet

asyncio

custom_threadpool_executor.py - ThreadPoolExecutorShrinkAble is a resizable bounded thread pool. Resizable means the thread pool can automatically expand, and most impressively, it can automatically shrink the number of threads, a feature the official implementation lacks. If thread pool submit tasks are sparse, even if set to 500 concurrency, it won't create 500 threads. The official implementation lacks this feature.

flexible_thread_pool.py - Rewritten from scratch, a completely custom intelligent scalable thread pool with no official code involved. It has the same functionality as custom_threadpool_executor.py: a resizable bounded thread pool that can automatically expand and shrink, with added support for running async def functions.

flxed_thread_pool.py - Fixed-size thread pool, the simplest way to implement a thread pool, anyone can write it. The downside is that the code won't automatically end because each thread in the pool has a non-daemon while 1 loop, which cannot automatically determine whether the code needs to end. If your code needs to run long-term without needing to end, you can use this type of thread pool.
```


#### The framework's default multi-threaded concurrent pool is flexible_thread_pool.py, which can support concurrent execution of both def functions and async def functions.

#### The framework's default asyncio concurrent pool is AsyncPoolExecutor
