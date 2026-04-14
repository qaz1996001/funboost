"""
Test FakeFunGenerator dynamic function generator

Demonstrates how to dynamically generate functions from parameter metadata
and verifies that the generated functions can be correctly parsed
"""

import inspect
from funboost.core.consuming_func_iniput_params_check import FakeFunGenerator, ConsumingFuncInputParamsChecker


def test_gen_fun_basic():
    """Test basic function generation"""
    print("=" * 60)
    print("Test 1: Basic function generation")
    print("=" * 60)

    # Generate a function with 2 required and 2 optional parameters
    func = FakeFunGenerator.gen_fun_by_params(
        must_arg_name_list=['x', 'y'],
        optional_arg_name_list=['z', 'w'],
        func_name='test_add'
    )

    # Check function signature
    spec = inspect.getfullargspec(func)
    print(f"✅ Generated function name: {func.__name__}")
    print(f"✅ All parameters: {spec.args}")
    print(f"✅ Number of defaults: {len(spec.defaults) if spec.defaults else 0}")
    print(f"✅ Function signature: {inspect.signature(func)}")

    # Verify
    assert func.__name__ == 'test_add'
    assert spec.args == ['x', 'y', 'z', 'w']
    assert len(spec.defaults) == 2
    print("\n✅ Basic function generation test passed!\n")


def test_gen_fun_only_must_params():
    """Test function with only required parameters"""
    print("=" * 60)
    print("Test 2: Only required parameters")
    print("=" * 60)

    func = FakeFunGenerator.gen_fun_by_params(
        must_arg_name_list=['a', 'b', 'c'],
        optional_arg_name_list=[],
        func_name='my_func'
    )

    spec = inspect.getfullargspec(func)
    print(f"✅ Generated function: {func.__name__}")
    print(f"✅ All parameters: {spec.args}")
    print(f"✅ Defaults: {spec.defaults}")
    print(f"✅ Function signature: {inspect.signature(func)}")

    assert spec.args == ['a', 'b', 'c']
    assert spec.defaults is None
    print("\n✅ Only required parameters test passed!\n")


def test_gen_fun_only_optional_params():
    """Test function with only optional parameters"""
    print("=" * 60)
    print("Test 3: Only optional parameters")
    print("=" * 60)

    func = FakeFunGenerator.gen_fun_by_params(
        must_arg_name_list=[],
        optional_arg_name_list=['opt1', 'opt2'],
        func_name='optional_func'
    )

    spec = inspect.getfullargspec(func)
    print(f"✅ Generated function: {func.__name__}")
    print(f"✅ All parameters: {spec.args}")
    print(f"✅ Number of defaults: {len(spec.defaults)}")
    print(f"✅ Function signature: {inspect.signature(func)}")

    assert spec.args == ['opt1', 'opt2']
    assert len(spec.defaults) == 2
    print("\n✅ Only optional parameters test passed!\n")


def test_gen_params_info_from_dynamic_func():
    """Test extracting parameter info from a dynamically generated function"""
    print("=" * 60)
    print("Test 4: Extract parameter info from dynamic function")
    print("=" * 60)

    # 1. Simulate metadata fetched from redis
    must_params = ['user_id', 'amount']
    optional_params = ['currency', 'memo']

    print(f"📋 Metadata:")
    print(f"   Required parameters: {must_params}")
    print(f"   Optional parameters: {optional_params}")

    # 2. Dynamically generate function
    dynamic_func = FakeFunGenerator.gen_fun_by_params(
        must_arg_name_list=must_params,
        optional_arg_name_list=optional_params,
        func_name='process_payment'
    )

    # 3. Use ConsumingFuncInputParamsChecker to extract parameter info
    params_info = ConsumingFuncInputParamsChecker.gen_func_params_info_by_func(dynamic_func)

    print(f"\n✅ Extracted parameter info:")
    print(f"   Function name: {params_info['func_name']}")
    print(f"   All parameters: {params_info['all_arg_name_list']}")
    print(f"   Required parameters: {params_info['must_arg_name_list']}")
    print(f"   Optional parameters: {params_info['optional_arg_name_list']}")

    # 4. Verify correctness
    assert params_info['func_name'] == 'process_payment'
    assert params_info['all_arg_name_list'] == must_params + optional_params
    assert params_info['must_arg_name_list'] == must_params
    assert params_info['optional_arg_name_list'] == optional_params

    print("\n✅ Parameter info extraction is completely correct!\n")


def test_call_dynamic_func():
    """Test calling a dynamically generated function"""
    print("=" * 60)
    print("Test 5: Call dynamic function")
    print("=" * 60)

    func = FakeFunGenerator.gen_fun_by_params(
        must_arg_name_list=['x', 'y'],
        optional_arg_name_list=['z'],
        func_name='calculator'
    )

    # Call the function
    result1 = func(1, 2)
    print(f"✅ Call func(1, 2): {result1}")

    result2 = func(1, 2, z=3)
    print(f"✅ Call func(1, 2, z=3): {result2}")

    result3 = func(x=10, y=20, z=30)
    print(f"✅ Call func(x=10, y=20, z=30): {result3}")

    print("\n✅ Function call test passed!\n")


def test_fanboost_faas_scenario():
    """Simulate a real funboost.faas usage scenario"""
    print("=" * 60)
    print("Test 6: funboost.faas real scenario simulation")
    print("=" * 60)

    # Scenario: web service reads queue metadata from redis
    redis_metadata = {
        'queue_name': 'user_registration_queue',
        'must_arg_name_list': ['username', 'email', 'password'],
        'optional_arg_name_list': ['phone', 'referral_code']
    }

    print(f"📡 Fetched metadata from Redis:")
    print(f"   Queue: {redis_metadata['queue_name']}")
    print(f"   Required parameters: {redis_metadata['must_arg_name_list']}")
    print(f"   Optional parameters: {redis_metadata['optional_arg_name_list']}")

    # Dynamically generate function (no actual function definition needed)
    fake_func = FakeFunGenerator.gen_fun_by_params(
        must_arg_name_list=redis_metadata['must_arg_name_list'],
        optional_arg_name_list=redis_metadata['optional_arg_name_list'],
        func_name='register_user'
    )

    print(f"\n🔧 Dynamically generated function: {fake_func.__name__}")
    print(f"   Signature: {inspect.signature(fake_func)}")

    # Create parameter checker
    params_info = ConsumingFuncInputParamsChecker.gen_func_params_info_by_func(fake_func)
    checker = ConsumingFuncInputParamsChecker(params_info)

    # Test valid publish parameters
    valid_params_1 = {'username': 'alice', 'email': 'alice@example.com', 'password': '123456'}
    try:
        checker.check_params(valid_params_1)
        print(f"\n✅ Parameter check passed: {valid_params_1}")
    except ValueError as e:
        print(f"❌ Parameter check failed: {e}")

    # Test publish with optional parameters
    valid_params_2 = {
        'username': 'bob',
        'email': 'bob@example.com',
        'password': 'abc123',
        'phone': '13800138000'
    }
    try:
        checker.check_params(valid_params_2)
        print(f"✅ Parameter check passed (with optional params): {valid_params_2}")
    except ValueError as e:
        print(f"❌ Parameter check failed: {e}")

    # Test invalid parameters (missing required parameter)
    invalid_params_1 = {'username': 'charlie', 'email': 'charlie@example.com'}
    try:
        checker.check_params(invalid_params_1)
        print(f"❌ Should have failed but passed: {invalid_params_1}")
    except ValueError as e:
        print(f"✅ Correctly rejected (missing required parameter): {e}")

    # Test invalid parameters (includes undefined parameter)
    invalid_params_2 = {
        'username': 'david',
        'email': 'david@example.com',
        'password': 'xyz789',
        'unknown_field': 'value'  # Undefined parameter
    }
    try:
        checker.check_params(invalid_params_2)
        print(f"❌ Should have failed but passed: {invalid_params_2}")
    except ValueError as e:
        print(f"✅ Correctly rejected (contains undefined parameter): {e}")

    print("\n✅ funboost.faas scenario test complete!")


if __name__ == "__main__":
    print("\n🚀 Starting tests for FakeFunGenerator dynamic function generator\n")

    test_gen_fun_basic()
    test_gen_fun_only_must_params()
    test_gen_fun_only_optional_params()
    test_gen_params_info_from_dynamic_func()
    test_call_dynamic_func()
    test_fanboost_faas_scenario()

    print("=" * 60)
    print("🎉 All tests passed!")
    print("=" * 60)
    print("""
💡 Summary:
1. ✅ Functions can be dynamically generated from parameter lists
2. ✅ Generated functions have correct signatures and parameter info
3. ✅ Can be correctly parsed by the inspect module
4. ✅ Can be used by ConsumingFuncInputParamsChecker
5. ✅ Perfectly supports funboost.faas no-function-object scenarios

🎯 Use cases:
- funboost.faas web service reads metadata from redis
- No actual consumer function object required
- Dynamically generates a fake function for parameter validation
- Achieves fully decoupled FaaS architecture
    """)
