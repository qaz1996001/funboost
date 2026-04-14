Celery test.
The primary goal is to schedule the same function as this framework. Under identical conditions — the same local Redis middleware, running on the same machine, both using gevent mode, no consumption result callbacks, and the same concurrency count — this tests the difference in publishing and consumption performance between the two frameworks.
