

# 0 How to extend and add new broker middleware in funboost in a fixed manner (or customize features different from existing broker_kind)

**There are 3 ways to extend new broker middleware in funboost**

- The first way is static middleware extension. Since I am the author of funboost, I can directly add hardcoded code in the source code folder of the funboost framework. (This is only suitable for myself, users cannot write code in the funboost folder, and only the most core necessary middleware code is recommended to use this method)

- The second way is dynamic middleware extension. Follow the tutorial `funboost_all_docs.md` Chapter 4.21, ``4.21 【Completely free customization and extension (Method 1)】 Use `register_custom_broker` to completely freely customize, extend and modify middleware (consumers and publishers)``

- The third way is dynamic middleware extension. Follow the tutorial `funboost_all_docs.md` Chapter 4.21b, ``4.21b 【Completely free customization and extension (Method 2)】 Use `consumer_override_cls` and `publisher_override_cls` to customize consumers and publishers.``


# 1. Introducing the first method: static middleware extension

Static middleware extension requires directly adding code files in funboost/consumers and funboost/publishers to write code

## Files that need to be modified when statically extending broker

### Add to BrokerConnConfig in funboost_config_deafult.py

If the new middleware requires connection configuration (such as SQS's region, access_key, etc.), add configuration items here.

### In funboost/core/broker_kind__exclusive_config_default_define.py 

Add unique broker dynamic parameters that can be passed additionally

### Add publisher in funboost/publishers

### Add consumer in funboost/consumers

### Add enum in funboost/constant.py BrokerEnum

### In funboost/factories/broker_kind__publsiher_consumer_type_map.py 

Register publisher and consumer in regist_to_funboost

### When statically extending, you can still reference the tutorial in `funboost_all_docs_and_codes.md` Chapter 4.21 to understand which parent class methods need to be inherited and overridden. 
4.21 is for dynamic middleware extension; AI doesn't need to use dynamic approach when adding middleware, just write the code directly and hardcode it in the funboost project.


When dynamically extending middleware, do not modify the above files.


# 2. Dynamic middleware extension with `register_custom_broker`

`register_custom_broker` is more suitable for extending completely new middleware that doesn't exist.

Dynamic addition of new middleware means not writing code in funboost/consumers and funboost/publishers.

AI can reference the tutorial in `funboost_all_docs_and_codes.md` Chapter 4.21
AI can reference the code in the `funboost/contrib/register_custom_broker_contrib` directory, which contains examples of dynamically extending new middleware.



# 3. Dynamic middleware extension with `consumer_override_cls` and `publisher_override_cls`

Although this method can also extend completely new middleware, it's more inclined toward overriding and modifying parent class logic to customize user's own logic and inject logic into various brokers.

AI can reference the tutorial in `funboost_all_docs_and_codes.md` Chapter 4.21b
AI can reference the code in the `funboost/contrib/override_publisher_consumer_cls` directory, which contains examples of overriding parent classes to customize logic.


----------------


# Publisher and consumer implementation

## Publisher needs to inherit AbstractPublisher and implement these methods:

- `custom_init()` - Optional, custom initialization
- `_publish_impl(msg: str)` - **Must implement**, core logic for publishing messages
- `clear()` - **Must implement**, clear the queue
- `get_message_count()` - **Must implement**, get message count in queue
- `close()` - **Must implement**, close connection. This method can be `pass` because funboost doesn't automatically stop, it runs indefinitely.


##  Consumer needs to inherit AbstractConsumer and implement these methods:

- `custom_init()` - Optional, custom initialization
- `_dispatch_task()` - **Must implement**, fetch messages from middleware, call `self._submit_task(kw)` in a loop
- `_confirm_consume(kw)` - **Must implement**, confirm consumption (ack)
- `_requeue(kw)` - **Must implement**, requeue message

##  The kw dictionary must include these fields:

```python
kw = {
    'body': message_body,  # Message body, contains all function input parameters and extra key with various auxiliary fields
    # Other auxiliary fields for ack/requeue, different for each broker, such as:
    # 'receipt_handle': ...,  # For SQS
    # 'message': ...,         # For AMQP
    # 'channel': ...,         # For RabbitMQ
}
self._submit_task(kw)
```

## Convention for accessing broker-specific exclusive configuration:

- Configuration in `broker_exclusive_config` **must use bracket `[]` access**, don't use `.get()`
- Defaults should be declared in the `register_broker_exclusive_config_default` function in `broker_kind__exclusive_config_default_define.py` so users know what parameters they can pass
- If the key doesn't exist, it will directly raise KeyError, making it easy to spot problems

- Access in consumer class through `self.consumer_params.broker_exclusive_config['$key']`
- Access in publisher class through `self.publisher_params.broker_exclusive_config['$key']`

## Reference materials for AI

AI can reference other broker implementations in funboost/publishers and funboost/consumers.

AI can reference Chapters 4.21 and 4.21b in the tutorial `funboost_all_docs_and_codes.md`

AI can reference code in the `funboost/contrib/override_publisher_consumer_cls` directory, which contains examples of dynamically extending middleware.

## AI programming doesn't need overly defensive programming

For example, don't write excessive try-catch blocks or use get() on dictionaries when keys are certain to exist.


# Writing test code 

After adding and extending new middleware, write test code in the test_frame/ directory to verify functionality.
Create a new folder under test_frame/ and write code to verify functionality.

**AI Note:**

When AI agent runs funboost test code, let funboost run for about 1 minute, then kill it.
If funboost runs too briefly, consumers might not have started up yet.
If not actively killed, funboost won't exit automatically because it's designed with infinite loop consumption.
