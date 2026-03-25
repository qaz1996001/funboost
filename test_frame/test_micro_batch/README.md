# MicroBatch Consumption Test

This directory contains test and example code for funboost's **MicroBatch** consumption feature.

## Feature Overview

Micro-batch consumption is an advanced funboost feature that allows accumulating N messages and processing them in a batch, rather than consuming them one by one.

**Core value**: Trade a tiny amount of latency for extremely high throughput.

## File Descriptions

| File | Description |
|------|------|
| `test_micro_batch_consumer.py` | Synchronous mode (THREADING) micro-batch consumption test |
| `test_micro_batch_async.py` | Asynchronous mode (ASYNC) micro-batch consumption test |
| `lowb_manul_batch.py` | For comparison: how cumbersome it is to manually implement batch aggregation without funboost |

## Quick Start

```python
from funboost import boost, BoosterParams, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.funboost_micro_batch_mixin import MicroBatchConsumerMixin

@boost(BoosterParams(
    queue_name='my_batch_queue',
    broker_kind=BrokerEnum.REDIS,
    consumer_override_cls=MicroBatchConsumerMixin,
    user_options={
        'micro_batch_size': 100,       # process after accumulating 100 messages
        'micro_batch_timeout': 5.0,    # or process after waiting 5 seconds
    },
    should_check_publish_func_params=False,  # must be disabled
))
def batch_insert(items: list):
    """items is a list containing multiple messages"""
    db.bulk_insert(items)
```

## Use Cases

| Scenario | Benefit |
|------|------|
| Bulk database writes | Reduces DB connection overhead; throughput improved 10-100x |
| Bulk external API calls | Reduces HTTP connection overhead |
| Bulk notification sending | Merges pushes, reduces number of requests |

## Related Documentation

- Core implementation: [funboost/contrib/override_publisher_consumer_cls/funboost_micro_batch_mixin.py](../../funboost/contrib/override_publisher_consumer_cls/funboost_micro_batch_mixin.py)
- Usage documentation: [funboost/contrib/override_publisher_consumer_cls/README.md](../../funboost/contrib/override_publisher_consumer_cls/README.md)
