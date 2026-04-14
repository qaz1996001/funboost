Tests the usage of the framework. You can change the broker_kind to test different types of middleware.

Even without any middleware installed, you can use this framework's SQLite persist-queue based local distribution (set broker_kind to 6) — compared to Python's built-in Queue object, this supports sharing a message queue across scripts and processes that are not running in the same interpreter.

For production use, it is strongly recommended to install the RabbitMQ middleware.
