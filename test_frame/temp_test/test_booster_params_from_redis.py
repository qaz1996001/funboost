import sys
import os
import pprint
import typing
# Ensure funboost is in path
sys.path.insert(0, r'D:\codes\funboost')

from funboost.core.func_params_model import BoosterParams, FunctionResultStatusPersistanceConfig
from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter
from funboost.concurrent_pool.base_pool_type import FunboostBaseConcurrentPool
from funboost.core.pydantic_compatible_base import get_cant_json_serializable_fields

# 1. Define test Mock classes
class MyPool(FunboostBaseConcurrentPool):
    def __init__(self, n):
        self.n = n

    def submit(self, func, *args, **kwargs):
        pass

    def shutdown(self, wait=True):
        pass

def my_decorator(f):
    return f

class MyConsumerCls:
    pass

class MyPublisherCls:
    pass

def demo():
    print("=== BoosterParams Serialization and Deserialization Reset Demo ===\n")

    print(get_cant_json_serializable_fields(BoosterParams))

    # 2. Create BoosterParams with various non-serializable objects
    print("1. Creating original BoosterParams object...")
    bp_original = BoosterParams(
        queue_name="demo_queue_serialization_test",
        # Pass non-serializable objects
        specify_concurrent_pool=MyPool(10),
        consuming_function_decorator=my_decorator,
        consumer_override_cls=MyConsumerCls,
        publisher_override_cls=MyPublisherCls,
        # Pass special types that are serializable
        delay_task_apscheduler_jobstores_kind='memory',

    )

    print(f"   [Original] specify_concurrent_pool type: {type(bp_original.specify_concurrent_pool)}")
    print(f"   [Original] consuming_function_decorator type: {type(bp_original.consuming_function_decorator)}")

    # 3. Simulate storing in Redis: convert to string dict (get_str_dict)
    # This is a BaseJsonAbleModel feature, converting non-json-serializable objects to str
    print("\n2. Simulating serialization (get_str_dict) - the format stored in Redis...")
    redis_data = bp_original.get_str_dict()

    # Show what the data looks like in Redis
    print("   [Redis data] Some key field values:")
    keys_to_show = [
        'specify_concurrent_pool',
        'consuming_function_decorator',
        'consumer_override_cls',
        'delay_task_apscheduler_jobstores_kind'
    ]
    for k in keys_to_show:
        print(f"     {k}: {redis_data.get(k)} (type: {type(redis_data.get(k)).__name__})")

    # Verify it has indeed become a string
    pool_str = redis_data['specify_concurrent_pool']
    print(f"     -> specify_concurrent_pool str value: {pool_str}")
    assert isinstance(pool_str, str)
    assert 'MyPool' in pool_str

    # 4. Simulate retrieving from Redis and executing automatic cleanup
    print("\n3. Executing _reset_non_json_serializable_fields automatic cleanup...")

    # Call static method to clean up
    SingleQueueConusmerParamsGetter._reset_non_json_serializable_fields(redis_data)

    redis_data['function_result_status_persistance_conf'] = FunctionResultStatusPersistanceConfig(
        is_save_status=False,is_save_result=False)
    print("   [After cleanup] Key field values:")
    for k in keys_to_show:
        val = redis_data.get(k)
        print(f"     {k}: {val}")

    # 5. Verify cleanup results
    print("\n4. Verifying cleanup logic correctness...")

    # Fields that should be reset to None
    assert redis_data['specify_concurrent_pool'] is None, "❌ specify_concurrent_pool not reset to None"
    assert redis_data['consuming_function_decorator'] is None, "❌ consuming_function_decorator not reset to None"
    assert redis_data['consumer_override_cls'] is None, "❌ consumer_override_cls not reset to None"

    # Fields that should retain their original values
    assert redis_data['delay_task_apscheduler_jobstores_kind'] == 'memory', "❌ delay_task_apscheduler_jobstores_kind incorrectly reset"

    print("   ✅ All assertion checks passed!")

    # 6. Verify re-instantiation
    print("\n5. Trying to re-instantiate BoosterParams with cleaned data...")
    try:
        bp_new = BoosterParams(**redis_data)
        print("   ✅ Re-instantiation successful!")
        print(f"   [New object] specify_concurrent_pool: {bp_new.specify_concurrent_pool}")
        print(f"   [New object] delay_task_apscheduler_jobstores_kind: {bp_new.delay_task_apscheduler_jobstores_kind}")
    except Exception as e:
        print(f"   ❌ Re-instantiation failed: {e}")
        raise

if __name__ == '__main__':
    demo()
