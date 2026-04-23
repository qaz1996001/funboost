# FakeFunGenerator Dynamic Function Generator Guide

## Functional Overview

`FakeFunGenerator` is a utility class that can dynamically generate function objects based on parameter metadata. Primarily used in **funboost.faas** scenarios, allowing web services to perform parameter validation without actual function definitions.

## Core Method

### `gen_fun_by_params(must_arg_name_list, optional_arg_name_list, func_name)`

Dynamically generates a function with correct signature based on required and optional parameter lists.

**Parameters:**
- `must_arg_name_list`: List of required parameters (positional parameters without default values)
- `optional_arg_name_list`: List of optional parameters (keyword parameters with default values)
- `func_name`: Name of generated function

**Return:**
- Dynamically generated function object with correct parameter signature

## Usage Examples

### Example 1: Basic Usage

```python
from funboost.core.consuming_func_iniput_params_check import FakeFunGenerator
import inspect

# Generate a function: def my_func(x, y, z=None, w=None)
func = FakeFunGenerator.gen_fun_by_params(
    must_arg_name_list=['x', 'y'],
    optional_arg_name_list=['z', 'w'],
    func_name='my_func'
)

# Check function signature
print(inspect.signature(func))
# Output: (x, y, z=None, w=None)

# Get parameter information
spec = inspect.getfullargspec(func)
print(spec.args)        # ['x', 'y', 'z', 'w']
print(spec.defaults)    # (None, None)
```

### Example 2: Only Required Parameters

```python
# Generate: def process(a, b, c)
func = FakeFunGenerator.gen_fun_by_params(
    must_arg_name_list=['a', 'b', 'c'],
    optional_arg_name_list=[],
    func_name='process'
)

spec = inspect.getfullargspec(func)
print(spec.args)        # ['a', 'b', 'c']
print(spec.defaults)    # None (no default values)
```

### Example 3: Only Optional Parameters

```python
# Generate: def config(opt1=None, opt2=None)
func = FakeFunGenerator.gen_fun_by_params(
    must_arg_name_list=[],
    optional_arg_name_list=['opt1', 'opt2'],
    func_name='config'
)

spec = inspect.getfullargspec(func)
print(spec.args)        # ['opt1', 'opt2']
print(len(spec.defaults))  # 2 (both parameters have default values)
```

## Using with ConsumingFuncInputParamsChecker

Dynamically generated functions can be correctly parsed by `ConsumingFuncInputParamsChecker`:

```python
from funboost.core.consuming_func_iniput_params_check import (
    FakeFunGenerator, 
    ConsumingFuncInputParamsChecker
)

# 1. Dynamically generate function
func = FakeFunGenerator.gen_fun_by_params(
    must_arg_name_list=['user_id', 'amount'],
    optional_arg_name_list=['currency', 'memo'],
    func_name='process_payment'
)

# 2. Extract parameter information
params_info = ConsumingFuncInputParamsChecker.gen_func_params_info_by_func(func)

print(params_info)
# {
#     'func_name': 'process_payment',
#     'func_position': '<function process_payment at 0x...>',
#     'is_manual_func_input_params': False,
#     'all_arg_name_list': ['user_id', 'amount', 'currency', 'memo'],
#     'must_arg_name_list': ['user_id', 'amount'],
#     'optional_arg_name_list': ['currency', 'memo']
# }

# 3. Create parameter checker
checker = ConsumingFuncInputParamsChecker(params_info)

# 4. Validate published parameters
checker.check_params({'user_id': 123, 'amount': 100})  # ✅ Pass
checker.check_params({'user_id': 123, 'amount': 100, 'currency': 'USD'})  # ✅ Pass
checker.check_params({'user_id': 123})  # ❌ Missing required parameter amount
checker.check_params({'user_id': 123, 'amount': 100, 'unknown': 'x'})  # ❌ Contains undefined parameter
```

## funboost.faas Application Scenario

### Problems with Traditional Approach

In traditional web service + task queue architecture:
- Web service needs to import consuming function
- Web service and consuming service are tightly coupled
- Modifying consuming function requires restarting web service

### funboost.faas Solution

Using `FakeFunGenerator`, web service completely doesn't need real function objects:

```python
# === Consuming Service Side ===
from funboost import boost

@boost('user_queue', qps=10, project_name='my_project')
def register_user(username, email, password, phone=None):
    # User registration logic
    pass

# After consuming function starts, parameter information is automatically saved to redis


# === Web Service Side (FastAPI) ===
from funboost.faas import fastapi_router, SingleQueueConusmerParamsGetter
from funboost.core.consuming_func_iniput_params_check import FakeFunGenerator

# 1. Read metadata from redis
queue_params = SingleQueueConusmerParamsGetter('user_queue').get_one_queue_params_use_cache()
func_params_info = queue_params['auto_generate_info']['final_func_input_params_info']

# 2. Dynamically generate fake function (no need for real function definition)
fake_func = FakeFunGenerator.gen_fun_by_params(
    must_arg_name_list=func_params_info['must_arg_name_list'],
    optional_arg_name_list=func_params_info['optional_arg_name_list'],
    func_name=func_params_info['func_name']
)

# 3. Create parameter checker
checker = ConsumingFuncInputParamsChecker(func_params_info)

# 4. Validate user-published parameters
# Now web service can validate parameters before publishing without importing real consuming function!
```

## Summary of Advantages

1. **Complete Decoupling**
   - Web service doesn't need to import consuming function
   - No need for consuming function source code
   - Only depends on metadata in redis

2. **Dynamic Updates**
   - After modifying consuming function, web service automatically gets new parameter information
   - No need to restart web service
   - True hot updates

3. **Flexible Deployment**
   - Web service and consuming service can be deployed independently
   - Consuming function can be implemented in different languages (as long as metadata is compatible)
   - Support multiple versions coexisting

4. **Parameter Validation**
   - Can validate parameters at web layer
   - Avoid invalid tasks entering queue
   - Provide friendly error messages

## Implementation Principle

Use Python's `exec` to dynamically execute code to generate functions:

```python
def gen_fun_by_params(must_arg_name_list, optional_arg_name_list, func_name):
    # Build parameter string
    must_params = 'x, y'  # Required parameters
    optional_params = 'z=None, w=None'  # Optional parameters
    all_params = 'x, y, z=None, w=None'
    
    # Dynamically generate function code
    func_code = f'''
def {func_name}({all_params}):
    return locals()
'''
    
    # Execute code in separate namespace
    namespace = {}
    exec(func_code, {}, namespace)
    
    # Return generated function object
    return namespace[func_name]
```

Generated functions have:
- Correct `__name__` attribute
- Correct parameter signature
- Can be parsed by `inspect` module
- Can be called normally

## Related Documentation

- `ConsumingFuncInputParamsChecker`: Parameter validator
- `funboost.faas`: Metadata-based FaaS architecture
- `SingleQueueConusmerParamsGetter`: Get queue metadata from redis
