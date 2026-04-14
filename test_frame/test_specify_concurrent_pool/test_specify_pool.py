from funboost import boost
from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble
from funboost.concurrent_pool.custom_gevent_pool_executor import GeventPoolExecutor

"""
This demonstrates multiple different function consumers sharing the same global concurrent pool.
If too many functions are started at once, use this approach to avoid each consumer creating
its own concurrent pool, reducing thread/coroutine resource waste.
"""

# There are 5 types of concurrent pools in total; users can choose freely.
pool = ThreadPoolExecutorShrinkAble(300)  # Specify multiple consumers to share the same thread pool


# pool = GeventPoolExecutor(200)

@boost('test_f1_queue', specify_concurrent_pool=pool, qps=3)
def f1(x):
    print(f'x : {x}')


@boost('test_f2_queue', specify_concurrent_pool=pool, qps=2)
def f2(y):
    print(f'y : {y}')


@boost('test_f3_queue', specify_concurrent_pool=pool)
def f3(m, n):
    print(f'm : {m} , n : {n}')


if __name__ == '__main__':
    for i in range(1000):
        f1.push(i)
        f2.push(i)
        f3.push(i, 1 * 2)
    f1.consume()
    f2.consume()
    f3.consume()
