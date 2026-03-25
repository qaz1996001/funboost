Demonstrates the usage of the framework, showing the simplest usage based on a local persistent message queue. Running this example does not require installing any middleware — a Python environment is all you need.


Automatically creates an SQLite database file under the `\sqllite_queues` directory at the root of the current drive. You can open and inspect the database with PyCharm Professional Edition.


For production use, it is strongly recommended to install the RabbitMQ middleware; using RabbitMQ as the message queue is the best choice. Redis is not recommended — Redis's list is just an array structure and lacks many message queue features. Even the most critical feature, consumption acknowledgment, is not supported, which means that arbitrarily stopping a running program, sudden shutdowns, or power outages can cause some tasks to be lost.

This example does not make use of the framework's 10 additional features beyond distribution.


### For the decorator-based usage, see the test_decorator_run_example.
