"""
Test whether _reset_non_json_serializable_fields correctly handles various types
"""
import sys
sys.path.insert(0, r'D:\codes\funboost')

from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter
from funboost.core.func_params_model import BoosterParams

# Simulate booster_params fetched from Redis
test_booster_params = {
    'queue_name': 'test_queue',
    'broker_kind': 'REDIS',
    'concurrent_mode': 'threading',
    'concurrent_num': 50,
    'delay_task_apscheduler_jobstores_kind': 'redis',  # Literal type, should not be reset
    'qps': None,
    'log_level': 10,
    'is_send_consumer_heartbeat_to_redis': 'True',  # Boolean value as string
    'specify_concurrent_pool': '<FunboostBaseConcurrentPool object>',  # Should be reset to None
    'specify_async_loop': '<asyncio.AbstractEventLoop object>',  # Should be reset to None
    'consuming_function_decorator': '<function decorator>',  # Should be reset to None
    'user_custom_record_process_info_func': '<function custom_func>',  # Should be reset to None
    'consumer_override_cls': '<class ConsumerOverride>',  # Should be reset to None
    'publisher_override_cls': '<class PublisherOverride>',  # Should be reset to None
}

print("Original booster_params:")
for k, v in test_booster_params.items():
    print(f"  {k}: {v}")

# Call the reset method
SingleQueueConusmerParamsGetter._reset_non_json_serializable_fields(test_booster_params)

print("\nbooster_params after reset:")
for k, v in test_booster_params.items():
    print(f"  {k}: {v}")

# Verify key fields
print("\n=== Verification Results ===")
assert test_booster_params['delay_task_apscheduler_jobstores_kind'] == 'redis', "❌ Literal type was incorrectly reset!"
print("✅ delay_task_apscheduler_jobstores_kind retains original value 'redis'")

assert test_booster_params['specify_concurrent_pool'] is None, "❌ specify_concurrent_pool was not reset!"
print("✅ specify_concurrent_pool correctly reset to None")

assert test_booster_params['specify_async_loop'] is None, "❌ specify_async_loop was not reset!"
print("✅ specify_async_loop correctly reset to None")

assert test_booster_params['consuming_function_decorator'] is None, "❌ consuming_function_decorator was not reset!"
print("✅ consuming_function_decorator correctly reset to None")

print("\n✅ All tests passed!")
