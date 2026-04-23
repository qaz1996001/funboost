
# 0 How AI Can Extend and Add New Broker Middleware to funboost in a Standardized Way (or Customize Behavior Different from Existing broker_kind)

**There are 3 ways to extend new broker middleware in funboost:**

- Static middleware extension. Because I am the author of funboost, I can directly add hard-coded files inside the funboost framework source folder. (This approach is only suitable for the author himself; users should not write code inside the funboost folder, and only the most core and essential middleware code is recommended to use this approach.)

- Dynamic middleware extension method 1: Follow the tutorial in `funboost_all_docs.md`, section 4.21: `4.21 [Completely Free Custom Extension (Method 1)] Using register_custom_broker to fully and freely customize, extend, and modify middleware (consumers and publishers).`

- Dynamic middleware extension method 2: Follow the tutorial in `funboost_all_docs.md`, section 4.21b: `4.21b [Completely Free Custom Extension (Method 2)] Using consumer_override_cls and publisher_override_cls to customize consumers and publishers.`


# 1. Introduction to Static Middleware Extension

Static middleware extension means you need to directly add code files inside `funboost/consumers` and `funboost/publishers`.

## Files That Need to Be Modified When Statically Extending a Broker

### Add to `BrokerConnConfig` in `funboost_config_deafult.py`
If the new middleware requires connection configuration (e.g., fixed connection settings like SQS's region, access_key, etc.), you need to add configuration entries here.

### In `funboost/core/broker_kind__exclusive_config_default_define.py`
Add additional unique dynamic broker parameters that can be passed.

### Add a publisher in `funboost/publishers`

### Add a consumer in `funboost/consumers`

### Add an enum entry to `BrokerEnum` in `funboost/constant.py`

### In `funboost/factories/broker_kind__publsiher_consumer_type_map.py`
Register the publisher and consumer using `regist_to_funboost`.

### When doing a static extension, you can still refer to section 4.21 of `funboost_all_docs_and_codes.md` to understand which parent class methods need to be inherited and overridden.
Section 4.21 covers dynamic broker extension; when AI is adding middleware, there is no need to use dynamic extension — just hard-code the code directly into the funboost project.

When doing dynamic middleware extension, do not modify the files listed above.


# 2. Dynamic Middleware Extension Method 1: `register_custom_broker`

Dynamic middleware addition means you do not write code inside `funboost/consumers` and `funboost/publishers`.

`register_custom_broker` is better suited for extending entirely new middleware that does not yet exist.

The user-defined `YourPublisher` and `YourConsumer` classes can inherit from `AbstractPublisher` and `AbstractConsumer`, or from `EmptyPublisher` and `EmptyConsumer`.

AI can refer to section 4.21 of the tutorial in `funboost_all_docs_and_codes.md`.
AI can refer to the code in the `funboost/contrib/register_custom_broker_contrib` directory, which contains examples of dynamically extending new middleware.



# 3. Dynamic Middleware Extension Method 2: `consumer_override_cls` and `publisher_override_cls`

The `override_cls` extension approach is more oriented toward overriding and modifying parent class logic, customizing user-specific logic, and mixing logic into various brokers.

The user-defined `YourPublisherMixin` and `YourConsumerMixin` classes can inherit from `AbstractPublisher` and `AbstractConsumer`, or from `EmptyPublisher` and `EmptyConsumer`.

The user-defined `YourPublisherMixin` and `YourConsumerMixin` classes can also choose not to inherit from any parent class, since they are mixins — and from a fundamental design principle, mixin classes should not inherit from a parent class.
Why do the Mixin class code files in `funboost/contrib/override_publisher_consumer_cls` inherit from a parent class? Mainly to make it easier to get IDE auto-completion for instance attributes and method names when writing code. `funboost`'s `AbstractConsumer` and `AbstractPublisher` have rich instance attributes and methods. If the mixin class does not inherit from a parent class, funboost will run without any issues — it just becomes less convenient for your IDE to provide auto-completion hints, and you are more likely to make typos.



AI can refer to section 4.21b of the tutorial in `funboost_all_docs_and_codes.md`.

AI can refer to the code in the `funboost/contrib/override_publisher_consumer_cls` directory, which contains examples of overriding parent class logic for customization.



----------------

# 4. Both `register_custom_broker` and `override_cls` Can Theoretically Implement New Broker Addition and Custom Runtime Logic

## 4.1 Why Can `register_custom_broker` Also Customize Runtime Logic?
`register_custom_broker` uses classical inheritance to override methods of `AbstractPublisher` or a specific subclass of `AbstractPublisher`.
It is recommended to override methods related to message queue operations, such as `_publish_impl`.

But why can `register_custom_broker` also customize runtime logic? Because you are completely free to override general function execution control methods such as `_submit_task` and `_run` — there is no restriction preventing you from overriding those methods.

## 4.2 Why Can `override_cls` Also Add Entirely New Middleware?

`override_cls` uses mixin composition; the framework automatically mixes the new middleware class into the parent class. Users can override parent class methods in the new middleware class to implement custom logic, and the mixin class's methods have the highest priority in MRO lookup order.

In addition to specifying `consumer_override_cls` and `publisher_override_cls`, you also need to specify `broker_kind=BrokerEnum.EMPTY` in `@boost`.
```python
    @boost(BoosterParams(
        queue_name='my_task',
        consumer_override_cls=YourConsumerMixin,
        publisher_override_cls=YourPublisherMixin,
        broker_kind=BrokerEnum.EMPTY,
    ))
    def my_task(x):
        return x * 2
   
```



# How to Write a Publisher and Consumer

## Rules AI Must Follow
```
Note:
1. Read section 4.21 of `funboost_all_docs_and_codes.md`: `4.21 funboost Completely Free Custom Extension`
2. Read `funboost/md_for_ai/如何扩展增加新的中间件.md` in `funboost_all_docs_and_codes.md`
3. Refer to existing funboost extension code implementations in the `funboost/contrib/override_publisher_consumer_cls` and `funboost/contrib/register_custom_broker_contrib` folders.
4. Read the AbstractConsumer base class logic in `funboost/consumers/base_consumer.py`
5. Read the AbstractPublisher base class logic in `funboost/publishers/base_publisher.py`
```

## Publisher Inherits AbstractPublisher — Methods That Need to Be Implemented:

- `custom_init()` - Optional, custom initialization
- `_publish_impl(msg: str)` - **Must implement**, the core logic for publishing messages
- `clear()` - **Must implement**, clear the queue
- `get_message_count()` - **Must implement**, get the number of messages in the queue
- `close()` - **Must implement**, close the connection; this method can be a `pass`, because funboost does not automatically stop — it runs indefinitely.


## Consumer Inherits AbstractConsumer — Methods That Need to Be Implemented:

- `custom_init()` - Optional, custom initialization
- `_dispatch_task()` - **Must implement**, retrieves messages from the middleware and calls `self._submit_task(kw)` in a loop
- `_confirm_consume(kw)` - **Must implement**, acknowledge consumption (ack)
- `_requeue(kw)` - **Must implement**, requeue a message
- If function execution control is involved, ensure compatibility with both `_run` and `_async_run` (synchronous and asynchronous)

## When Overriding Parent Class Methods, Do Not Forget to Call super().xx()

### Rules

- When overriding a method of the same name in `AbstractPublisher` / `AbstractConsumer`, **you must call super().xx()**

- Even if the parent class method is an empty `pass`, call it anyway for future extensibility.
  For example, although `AbstractConsumer` has no concrete implementation of `_both_sync_and_aio_frame_custom_record_process_info_func` (it is just a `pass`),
  both `PrometheusConsumerMixin` and `CircuitBreakerConsumerMixin` override this method.
  Users may need to combine multiple mixins, e.g., `class MyCombinedMixin(CircuitBreakerConsumerMixin, PrometheusConsumerMixin)`.
  It is precisely because both call `super()._both_sync_and_aio_frame_custom_record_process_info_func()` that the MRO chain remains unbroken and both mixins' logic can execute.

- The following two cases **do not need to call** super():
  1. The parent class method raises `raise NotImplementedError` (a pure abstract method), e.g., `_publish_impl`, `_dispatch_task`, `_confirm_consume`, `_requeue`, etc.
  2. You truly need to completely replace the parent class logic and cannot allow the parent class code to execute (e.g., `MicroBatchConsumerMixin` completely overrides `_submit_task`)

### Where to Place the super() Call

- **Initialization methods** (`custom_init`, `_before_start_consuming_message_hook`): Call `super()` first, then execute your own initialization
- **Pre-intercept methods** (`_submit_task` with quota checks, circuit-breaker blocking): Execute your own logic first, then call `super()`
- **Post-recording methods** (`_after_publish`, `_both_sync_and_aio_frame_custom_record_process_info_func`): Calling `super()` before or after your own logic is fine, since the parent class is currently `pass`
- **Methods with logic both before and after** (e.g., `_run`, `_async_run` with tracing): Call `super()` in the middle of your own logic. For example, `AutoOtelConsumerMixin._run` opens a span first, then calls `super()._run(kw)` while the span is active, and records exceptions to the span afterward — `super()` is sandwiched in the middle of your own logic.

### Correct Example vs. Incorrect Example

```python
# Correct — call super() first during initialization
def custom_init(self):
    super().custom_init()
    self._my_config = self.consumer_params.user_options.get('my_key', 10)

# Correct — call super() after pre-intercept logic
def _submit_task(self, kw):
    self._check_something()       # your pre-logic
    super()._submit_task(kw)      # then follow the parent class flow

# Correct — wrap the parent class call
def _run(self, kw: dict):
    with some_context():
        return super()._run(kw)   # call parent class inside the context

# Incorrect — forgot to call super()
def custom_init(self):
    self._my_config = self.consumer_params.user_options.get('my_key', 10)
    # Missing super().custom_init() — future initialization logic in the parent class will be skipped
```

## The `kw` Dict Passed to the Consumer's `_submit_task(kw)` Method Must Contain the Following Fields:

```python
kw = {
    'body': message_body,  # The message body, which contains the function input parameters and an 'extra' key with various auxiliary fields
    # Other auxiliary fields for ack/requeue, which differ for each broker, e.g.:
    # 'receipt_handle': ...,  # Used by SQS
    # 'message': ...,         # Used by AMQP
    # 'channel': ...,         # Used by RabbitMQ
}
self._submit_task(kw)
```

## When AI Uses override_cls to Extend a Mixin Class, It Is Best to Group Multiple New Configuration Parameters Under a Single Key in the user_options Dict

For example, the circuit breaker configuration of `CircuitBreakerConsumerMixin` can be placed under the key `'circuit_breaker_options'` in the `user_options` dict.
This prevents key conflicts between the circuit breaker config and other keys already in `user_options`.


## When AI Extends a Mixin Class and Needs to Use the Framework's Hook Functions for Recording Results, Use the Following Methods

- `_both_sync_and_aio_frame_custom_record_process_info_func`
  Called by both synchronous and asynchronous execution. Use this if it involves only CPU computation with no I/O.
- `_frame_custom_record_process_info_func`
  If the logic involves I/O operations, you cannot use `_both_sync_and_aio_frame_custom_record_process_info_func` — override this instead.
- `_aio_frame_custom_record_process_info_func`
  If the logic involves I/O operations, you cannot use `_both_sync_and_aio_frame_custom_record_process_info_func` — override this instead.
  To avoid duplicating code with the synchronous `_frame_custom_record_process_info_func`, you can quickly convert the async logic to sync using `simple_run_in_executor`.
  ```python
  await super()._aio_frame_custom_record_process_info_func(current_function_result_status, kw)
  await simple_run_in_executor(self._frame_custom_record_process_info_func, current_function_result_status, kw)
  ```




## Access Convention for Broker-Exclusive Configuration:

- Configuration in `broker_exclusive_config` **must be accessed using bracket notation `[]`**, not `.get()`
- Default values should preferably be declared in the `register_broker_exclusive_config_default` function in `broker_kind__exclusive_config_default_define.py`, so users know which parameters can be passed
- If a key does not exist, a `KeyError` will be raised immediately, making it easy to spot problems

- In a consumer class, access via `self.consumer_params.broker_exclusive_config['$key']`
- In a publisher class, access via `self.publisher_params.broker_exclusive_config['$key']`

## References AI Can Use

AI can refer to other broker implementations in `funboost/publishers` and `funboost/consumers`.

AI can refer to sections 4.21 and 4.21b of the tutorial in `funboost_all_docs_and_codes.md`.

AI can refer to the code in the `funboost/contrib/override_publisher_consumer_cls` directory, which contains examples of dynamically extending middleware.

## AI Should Avoid Overly Conservative Defensive Programming

For example, wrapping too much in try blocks, or using `.get()` on dicts whose keys are guaranteed to exist.


# Writing Test Code
After adding and extending new middleware, you need to write tests to verify functionality under the `test_frame/` directory.
Create a new subfolder under `test_frame/` and write test code to verify the functionality.

**Note for AI:**
When AI agent runs funboost test code, let funboost run for about 1 minute, then kill it.
If funboost runs for too short a time, the consumer may not have had a chance to start.
If not killed manually, funboost will not terminate on its own, because funboost is designed as an infinite consumption loop.
