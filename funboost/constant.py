# coding= utf-8



class BrokerEnum:
    """
    In funboost, anything can serve as a message queue broker. funboost has built-in support for all well-known classic message queues as brokers,
    as well as brokers based on memory, various databases, file systems, and tcp/udp/http sockets.
    funboost also has built-in support for various Python third-party packages and consumer frameworks as brokers, such as sqlalchemy, kombu, celery, rq, dramatiq, huey, nameko, etc.

    Users can also easily extend any concept as a funboost broker following the documentation section 4.21.
    """
    
    # funboost framework easily supports various message queue working modes: pull/push/polling, single message fetch, batch fetch
    """
    funboost's consumer _dispatch_task is very flexible. Users submit messages fetched from the queue to the
    concurrency pool via the _submit_task method. It does not force users to implement a _get_one_message method,
    which would be inflexible and limit extending arbitrary things as brokers. Instead, users write fully flexible code.
    So whether fetching messages uses pull mode, push mode, or polling mode, whether single or batch fetch,
    no matter how different your new broker's API is from RabbitMQ's, you can easily extend anything as a funboost broker.
    That's why you can see in funboost's source code that virtually anything can be implemented as a funboost broker.
    """


    EMPTY = 'EMPTY'  # Empty implementation, needs to be used with boost's consumer_override_cls and publisher_override_cls parameters, or be subclassed.

    RABBITMQ_AMQPSTORM = 'RABBITMQ_AMQPSTORM'  # Uses the amqpstorm package to operate RabbitMQ as a distributed message queue with consumer acknowledgment support. Strongly recommended as a funboost broker.
    RABBITMQ = RABBITMQ_AMQPSTORM

    # 2025-10 newly built-in, supports all RabbitMQ routing modes including fanout, direct, topic, headers. More complex usage concepts.
    # See demo code in test_frame/test_broker_rabbitmq/test_rabbitmq_complex_routing.
    RABBITMQ_COMPLEX_ROUTING = 'RABBITMQ_COMPLEX_ROUTING'

    RABBITMQ_RABBITPY = 'RABBITMQ_RABBITPY'  # Uses the rabbitpy package to operate RabbitMQ as a distributed message queue with consumer acknowledgment support. Not recommended.

    RABBITMQ_AMQP = 'RABBITMQ_AMQP'  # Uses the amqp package to operate RabbitMQ. Celery/Kombu's underlying client with better performance than pika.

    “””
    Below are various Redis data structures and methods used to implement message queues. The author has explored Redis in every possible way.
    Since Redis is fundamentally a cache/database and not a message queue (it doesn't implement the classic AMQP protocol), Redis only simulates message queues rather than being a true MQ.
    For example, to implement consumer acknowledgment where messages are safe through arbitrary restarts, a simple redis.blpop that pops and deletes messages simply won't work — messages are lost on restart even if they haven't started or are still running.

    The challenge of implementing ACK in Redis is not how to implement the acknowledgment itself, but rather when to return orphaned unacknowledged messages from crashed/stopped consumer processes back to the queue.
    The real difficulty of implementing ACK on Redis is not the “acknowledge” action itself, but building a reliable distributed failure detection mechanism that can accurately determine “when it is safe and timely to recover tasks.”
    So if you think simply using brpoplpush or REDIS_STREAM will easily solve the ACK problem, that's too naive — Redis server doesn't natively have the automatic message recovery mechanism for crashed consumers like RabbitMQ does. You need to maintain this mechanism on the Redis client side.
    “””
    REDIS = 'REDIS'  # Uses Redis list structure with brpop as a distributed message queue. Arbitrary restarts will lose many messages. No consumer acknowledgment support. Choose this for performance when message loss is acceptable.
    REDIS_ACK_ABLE = 'REDIS_ACK_ABLE'  # Based on Redis list + temporary unack set. Uses Lua scripts for atomic task fetch and pending addition. Detects disconnected processes via heartbeat loss. No task loss on restarts or disconnections.
    REIDS_ACK_USING_TIMEOUT = 'reids_ack_using_timeout'  # Based on Redis list + temporary unack set. Messages automatically return to queue if not acknowledged within timeout seconds. Be careful with ack_timeout vs function duration to avoid repeated re-queuing. Set ack timeout via broker_exclusive_config={'ack_timeout': 1800}. Drawback: cannot distinguish slow execution from actual crashes.
    REDIS_PRIORITY = 'REDIS_PRIORITY'  # Based on Redis multiple lists + temporary unack set, blpop monitors multiple keys. Like RabbitMQ's x-max-priority, supports task priority. See documentation section 4.29 for priority queue details.
    REDIS_STREAM = 'REDIS_STREAM'  # Based on Redis 5.0+, uses stream data structure as distributed message queue. Supports consumer acknowledgment, persistence, and consumer groups. Redis officially recommended queue form, more suitable than list structure.
    REDIS_BRPOP_LPUSH = 'RedisBrpopLpush'  # Based on Redis list structure using brpoplpush dual-queue pattern. Similar to redis_ack_able but uses native commands instead of Lua scripts for fetch and unack operations.
    REDIS_PUBSUB = 'REDIS_PUBSUB'  # Based on Redis pub/sub. Publishing a message allows multiple consumers to receive the same message, but does not support persistence.
    
    """
    MEMORY_QUEUE: (The absolute most core broker in funboost, bar none)
    Python in-memory queue. Although it doesn't support cross-process, cross-script, or cross-machine task sharing, nor persistence,
    MEMORY_QUEUE is the most important broker in funboost — far from being a toy or only suitable for simple scenarios. Its versatility in funboost far exceeds that of traditional server-side MQs.
    MEMORY_QUEUE's importance in funboost is SSS-tier, far exceeding Redis, Kafka, RabbitMQ, etc. as brokers.
    Main reasons:
    1. queue.Queue has ultra-high performance with no socket I/O.
    2. When queue.Queue is used as a message queue, serialization/deserialization is skipped,
       meaning any type that cannot be JSON-serialized or pickle-serialized can be sent as function parameters to the in-memory Queue. Its compatibility and flexibility far surpass other brokers.
    3. Not all users/scenarios need distributed persistence. In-memory queues are frequently used for backpressure, decoupling, rate limiting, callbacks, etc.
       For example, ThreadPoolExecutor has an unbounded _work_queue attribute — in-memory queues are used everywhere.
    4. With in-memory queue, you can use the @boost decorator like the tomorrow package or a thread pool/asyncio coroutine pool. But funboost's @boost decorator
       far surpasses concurrency pools and the tomorrow decorator, because @boost not only provides one-click multiple concurrency modes, but also qps control, retries, timeout killing, function parameter cache filtering, and 30+ other features.
       With in-memory queue, @boost acts as a super decorator — one @boost covers all common decorator functionalities, equivalent to 10 regular decorators stacked together.
    5. Why doesn't Celery recommend memory as a broker? Because Celery workers are typically started separately via CLI, making them cross-process/cross-interpreter from the publishing scripts, unable to share in-memory queue tasks.
       funboost starts consumers as regular Python programs — publishing and consuming happen in the same process, so they can share an in-memory queue.
       Due to this difference in how the two frameworks start consumers, memory queue is a sixth-class citizen in Celery, but a super-first-class citizen in funboost.
    6. Special feature support:
     - Supports result retrieval in RPC mode without relying on external storage like Redis
     - Can retrieve results via get_future() and get_aio_future() methods without Redis RPC
     - High-performance micro-batch processing mode for improved throughput
    """
    MEMORY_QUEUE = 'MEMORY_QUEUE'  # Uses Python queue.Queue for an in-process message queue. Does not support cross-process, cross-script, or cross-machine task sharing. No persistence. Suitable for one-time short-lived simple tasks.
    LOCAL_PYTHON_QUEUE = MEMORY_QUEUE  # Alias. Python local queue is based on Python's built-in queue.Queue. Messages are stored in the Python program's memory. Does not support restart/resume.
    
    # High-performance in-memory queue using collections.deque instead of queue.Queue, eliminating unnecessary task_done/join overhead.
    # 2-5x performance improvement over MEMORY_QUEUE. Supports batch message fetching (via broker_exclusive_config={'pull_msg_batch_size': 1000}).
    FASTEST_MEM_QUEUE = 'FASTEST_MEM_QUEUE'

    RABBITMQ_PIKA = 'RABBITMQ_PIKA'  # Uses the pika package to operate RabbitMQ as a distributed message queue. Not recommended.

    MONGOMQ = 'MONGOMQ'  # Uses MongoDB collection rows to simulate a distributed message queue. Supports consumer acknowledgment.

    SQLITE_QUEUE = 'sqlite3'  # Uses sqlite3 to simulate a message queue. Supports consumer acknowledgment and persistence but not cross-machine task sharing. Supports cross-script and cross-process task sharing on the same machine. No middleware installation required.
    PERSISTQUEUE = SQLITE_QUEUE  # Alias for PERSISTQUEUE

    NSQ = 'NSQ'  # Uses NSQ as a distributed message queue. Supports consumer acknowledgment.

    KAFKA = 'KAFKA'  # Uses Kafka as a distributed message queue. Messages may be lost on arbitrary restarts. Recommended to use BrokerEnum.CONFLUENT_KAFKA instead.

    """Based on the confluent-kafka package, which is 10x faster than kafka-python. Also handles scenarios with frequent arbitrary restarts/deployments. This consumer implements at-least-once delivery, while BrokerEnum.KAFKA implements at-most-once delivery."""
    KAFKA_CONFLUENT = 'KAFKA_CONFLUENT'
    CONFLUENT_KAFKA = KAFKA_CONFLUENT

    KAFKA_CONFLUENT_SASlPlAIN = 'KAFKA_CONFLUENT_SASlPlAIN'  # Kafka with username/password authentication support

    SQLACHEMY = 'SQLACHEMY'  # Uses SQLAlchemy connections as a distributed message queue broker. Supports persistence and consumer acknowledgment. Supports MySQL, Oracle, SQL Server, and 5 other databases.

    ROCKETMQ = 'ROCKETMQ'  # Uses RocketMQ as a distributed message queue. This broker must run on Linux; Windows is not supported.
    ROCKETMQ5 = 'ROCKETMQ5'  # Uses RocketMQ 5.x as a distributed message queue with SimpleConsumer class, suitable for individual message acknowledgment.

    ZEROMQ = 'ZEROMQ'  # Uses ZeroMQ as a distributed message queue. No middleware installation required. Supports cross-machine but not persistence.


    “””
    Both kombu and celery are god-tier broker_kinds in funboost.
    They allow funboost to effortlessly support all current and future message queues supported by kombu.
    By directly supporting kombu, funboost instantly inherits all current and future message queue capabilities of kombu. Regardless of what new cloud messaging services (e.g., Google
    Pub/Sub, Azure Service Bus) or niche MQs the kombu community adds support for in the future, funboost automatically gains that capability without modifying its own code.
    This is a “wait at ease for the exhausted enemy” strategy that greatly expands funboost's applicability.

    The kombu package can serve as a funboost broker. This package is also Celery's middleware dependency and can operate 10+ types of middleware (e.g., RabbitMQ, Redis), but does not include Kafka, NSQ, ZeroMQ, etc.
    However, kombu's performance is very poor — comparing native Redis lpush vs kombu publish, and brpop vs kombu drain_events, the difference is 5-10x.
    Due to poor performance, only choose kombu for brokers not natively implemented in funboost (e.g., kombu supports Amazon SQS, Qpid, Pyro queues). Otherwise, strongly recommended to use funboost's native broker implementations instead of kombu.
    “””
    KOMBU = 'KOMBU'

    """ Based on EMQ as the broker. This is very different from the brokers above — the server does not store messages. So you cannot publish hundreds of thousands of messages first and then start consuming. MQTT's advantage is that web frontend and backend can interact —
    the frontend cannot operate Redis/RabbitMQ/Kafka, but can easily operate MQTT. This is suitable for high-real-time internet interfaces.
    """
    MQTT = 'MQTT'

    HTTPSQS = 'HTTPSQS'  # Uses HTTPSQS broker, operated via HTTP protocol. Easy Docker installation.

    PULSAR = 'PULSAR'  # The most promising next-generation distributed messaging system. Expected to replace both RabbitMQ and Kafka in 5 years.

    UDP = 'UDP'  # Based on socket UDP. Consumer must be started before publisher. Supports distributed but not persistence. No middleware installation required.

    TCP = 'TCP'  # Based on socket TCP. Consumer must be started before publisher. Supports distributed but not persistence. No middleware installation required.

    HTTP = 'HTTP'  # Based on HTTP. Publishing uses urllib3, consuming server uses aiohttp.server. Supports distributed but not persistence. No middleware installation required.

    GRPC = 'GRPC'  # Uses the well-known gRPC as a broker. Can use sync_call method to synchronously get gRPC results. Far simpler than hand-writing native gRPC client/server code.

    NATS = 'NATS'  # High-performance NATS broker. The broker server has excellent performance.

    TXT_FILE = 'TXT_FILE'  # Uses disk txt files as a message queue. Supports single-machine persistence but not multi-machine distributed. Not recommended; use sqlite instead.

    PEEWEE = 'PEEWEE'  # Uses peewee package to operate MySQL, simulating a message queue with database tables.

    CELERY = 'CELERY'  # funboost supports Celery framework for publishing and consuming tasks, with Celery handling task scheduling/execution. The usage is far simpler than using Celery directly.
    # Users never need to worry about Celery object instances, task_routes, or includes configuration — funboost automatically sets up all Celery configurations.
    # funboost incorporates Celery itself into its broker system. Being able to “absorb” another major framework is brilliant and demonstrates funboost's architectural inclusiveness, elegance, and sophistication.

    DRAMATIQ = 'DRAMATIQ'  # funboost uses the Dramatiq framework as a message queue. Dramatiq is a task queue framework similar to Celery. Users operate Dramatiq's core scheduling through the funboost API.

    HUEY = 'HUEY'  # Huey task queue framework as funboost's scheduling core.

    RQ = 'RQ'  # RQ task queue framework as funboost's scheduling core.

    NAMEKO = 'NAMEKO'  # funboost supports the Python microservice framework Nameko. Users can work with Python Nameko microservices without learning the Nameko API syntax.

    
    """
    MYSQL_CDC is a unique and extraordinary broker in funboost.
    MySQL binlog CDC automatically becomes messages — users don't need to manually publish messages, just write the logic to process binlog content.
    One line of code can achieve lightweight mysql2mysql, mysql2kafka, mysql2rabbitmq, etc.
    Unlike other brokers, no manual message publishing is needed — any database insert, update, or delete automatically becomes a funboost message.
    This is essentially a lightweight replacement for Canal and Flink CDC.

    By extension, log files can also serve as brokers — whenever another program writes to a log file, it can trigger funboost consumption.
    You can then send messages to Kafka in your function logic (although ELK already exists for this, this is just an example scenario demonstrating funboost broker flexibility).

    Log files, file system changes (inotify), and even hardware sensor signals can all be wrapped as funboost Brokers following documentation section 4.21.

    This fully demonstrates that funboost can transform into a universal, event-driven function scheduling platform, not just a traditional message-driven system like Celery.
    """
    """
    funboost can consume binlog messages sent to Kafka by Canal, and can also capture CDC data independently without relying on Canal.
    """
    MYSQL_CDC = 'MYSQL_CDC'
    
    SQS = 'SQS'  # AWS SQS. Although funboost supports kombu which supports SQS (so funboost indirectly supports SQS), the native implementation has clearer logic and better performance than kombu.
    
    """
    Native PostgreSQL broker, fully utilizing PostgreSQL-specific features:
    1. FOR UPDATE SKIP LOCKED - Lock-free high concurrency, multiple consumers don't block each other
    2. LISTEN/NOTIFY - Native pub/sub mechanism, real-time push without polling
    3. Supports task priority
    Better performance and real-time capability compared to the generic SQLAlchemy implementation
    """
    POSTGRES = 'POSTGRES'
    
    WATCHDOG = 'WATCHDOG'  # Uses Python watchdog library to monitor file/folder change events and automatically trigger Python function consumption. Supports existing files and debouncing, which native watchdog does not.

    WEBSOCKET = 'WEBSOCKET'  # Uses WebSocket as a broker, supports real-time bidirectional communication.

    



class ConcurrentModeEnum:
    """
    funboost supports threading, gevent, eventlet, asyncio, and single-thread concurrency modes.
    There is no multiprocessing enum here because funboost intends multiprocessing to be stacked with these modes.
    booster.mp_consume(8) means 8 processes stacked with n threads or coroutines concurrently.
    funboost's multiprocessing and threading/asyncio are additive, not mutually exclusive.
    """
    THREADING = 'threading'  # Runs in threading mode. Also compatible with async def functions.
    GEVENT = 'gevent'
    EVENTLET = 'eventlet'
    ASYNC = 'async'  # asyncio concurrency, suitable for functions defined with async def.
    SINGLE_THREAD = 'single_thread'  # If you don't want concurrency and don't want to pre-fetch messages from the broker into Python's in-memory queue buffer, this concurrency mode is suitable.
    SOLO = SINGLE_THREAD
    


# is_fsdf_remote_run = 0

class FunctionKind:
    """
    funboost is more powerful than Celery. funboost not only supports functions and static methods,
    but also directly supports applying @boost to class methods and instance methods (though this requires following the tutorial, not guessing).
    """
    CLASS_METHOD = 'CLASS_METHOD'
    INSTANCE_METHOD = 'INSTANCE_METHOD'
    STATIC_METHOD = 'STATIC_METHOD'
    COMMON_FUNCTION = 'COMMON_FUNCTION'


class ConstStrForClassMethod:
    FIRST_PARAM_NAME = 'first_param_name'
    CLS_NAME = 'cls_name'
    OBJ_INIT_PARAMS = 'obj_init_params'
    CLS_MODULE = 'cls_module'
    CLS_FILE = 'cls_file'


class RedisKeys:

    REDIS_KEY_PAUSE_FLAG  = 'funboost_pause_flag' 
    REDIS_KEY_STOP_FLAG = 'funboost_stop_flag'
    QUEUE__MSG_COUNT_MAP = 'funboost_queue__msg_count_map'
    FUNBOOST_QUEUE__CONSUMER_PARAMS= 'funboost_queue__consumer_parmas'
    FUNBOOST_QUEUE__RUN_COUNT_MAP = 'funboost_queue__run_count_map'
    FUNBOOST_QUEUE__RUN_FAIL_COUNT_MAP = 'funboost_queue__run_fail_count_map'
    FUNBOOST_ALL_QUEUE_NAMES = 'funboost_all_queue_names'
    FUNBOOST_ALL_IPS = 'funboost_all_ips'
    FUNBOOST_ALL_PROJECT_NAMES = 'funboost_all_project_names'
    FUNBOOST_LAST_GET_QUEUES_PARAMS_AND_ACTIVE_CONSUMERS_AND_REPORT__UUID_TS = 'funboost_last_get_queues_params_and_active_consumers_and_report__uuid_ts'

    FUNBOOST_HEARTBEAT_QUEUE__DICT_PREFIX = 'funboost_hearbeat_queue__dict:'
    FUNBOOST_HEARTBEAT_SERVER__DICT_PREFIX = 'funboost_hearbeat_server__dict:'
    FUNBOOST_UNACK_REGISTRY_PREFIX = 'funboost_unack_registry:'


    @staticmethod
    def gen_funboost_apscheduler_redis_lock_key_by_queue_name(queue_name):
        return f'funboost.BackgroundSchedulerProcessJobsWithinRedisLock:{queue_name}'

    @staticmethod
    def gen_funboost_hearbeat_queue__dict_key_by_queue_name(queue_name):
        return f'{RedisKeys.FUNBOOST_HEARTBEAT_QUEUE__DICT_PREFIX}{queue_name}'

    @staticmethod
    def gen_funboost_hearbeat_server__dict_key_by_ip(ip):
        return f'{RedisKeys.FUNBOOST_HEARTBEAT_SERVER__DICT_PREFIX}{ip}'
    
    @staticmethod
    def gen_funboost_queue_time_series_data_key_by_queue_name(queue_name):
        return f'funboost_queue_time_series_data:{queue_name}'
    
    @staticmethod
    def gen_funboost_redis_apscheduler_jobs_key_by_queue_name(queue_name):
        jobs_key=f'funboost.apscheduler.jobs:{queue_name}'
        return jobs_key
    
    @staticmethod
    def gen_funboost_redis_apscheduler_run_times_key_by_queue_name(queue_name):
        run_times_key=f'funboost.apscheduler.run_times:{queue_name}'
        return run_times_key

    @staticmethod
    def gen_funboost_project_name_key(project_name):
        prject_name_key = f'funboost.project_name:{project_name}'
        return prject_name_key

    @staticmethod
    def gen_redis_hearbeat_set_key_by_queue_name(queue_name):
        return f'funboost_hearbeat_queue__str:{queue_name}'

    @staticmethod
    def gen_funboost_unack_registry_key_by_queue_name(queue_name):
        “””
        Approach C:
        Maintain a separate unack key registry (set) solely responsible for “full indexing”, not cleaned up by heartbeat threads.
        The registry stores the specific unack Redis key names, e.g.:
        - redis_ack_able:  {queue_name}__unack_id_{consumer_id}
        - brpoplpush:      unack_{queue_name}_{consumer_id}
        “””
        return f'{RedisKeys.FUNBOOST_UNACK_REGISTRY_PREFIX}{queue_name}'

class ConsumingFuncInputParamsCheckerField:
    is_manual_func_input_params = 'is_manual_func_input_params'
    all_arg_name_list = 'all_arg_name_list'
    must_arg_name_list = 'must_arg_name_list'
    optional_arg_name_list = 'optional_arg_name_list'
    func_name = 'func_name' 
    func_position = 'func_position'
    

class MongoDbName:
    TASK_STATUS_DB = 'funboost_task_status'
    MONGOMQ_DB ='funboost_mongomq'

class StrConst:
    BOOSTER_REGISTRY_NAME_DEFAULT = 'booster_registry_default'
    NO_RESULT = 'no_result'
    _ADVANCED_RETRY_COUNT = '_advanced_retry_count'
    FILTERED_TASK_RESULT = 'filtered_task_result'

class EnvConst:
    FUNBOOST_FAAS_CARE_PROJECT_NAME = 'funboost.faas.care_project_name'
    FUNBOOST_FAAS_IS_USE_LOCAL_BOOSTER = 'funboost.faas.is_use_local_booster'