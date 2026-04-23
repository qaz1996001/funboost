# Funboost FAAS Dynamic Import Implementation

## Background

Users don't want to get errors when using only FastAPI just because Flask or Django are not installed. Need to implement on-demand import mechanism.

## Solution

Use Python's `__getattr__` magic method to implement module-level lazy import.

## Implementation Architecture

### 1. Configuration-Driven Design

Use `_ROUTER_CONFIG` dictionary to configure all supported routers:

```python
_ROUTER_CONFIG = {
    'fastapi_router': {
        'module': 'fastapi_adapter',      # Module name
        'attr': 'fastapi_router',         # Exported attribute name
        'package': 'fastapi',             # Dependency package name
        'cache_var': '_fastapi_router',   # Cache variable name (backup)
    },
    'flask_blueprint': {...},
    'django_router': {...},
}
```

**Advantages:**
- ✅ Centralized configuration management, easy to maintain
- ✅ Adding new router only requires adding one item to configuration
- ✅ Eliminate hardcoded if-elif judgments
- ✅ Improve code extensibility

### 2. Lazy Import Mechanism

```python
def __getattr__(name: str):
    # 1. Check if in configuration
    if name not in _ROUTER_CONFIG:
        raise AttributeError(...)
    
    # 2. Check cache
    if name in _cache:
        return _cache[name]
    
    # 3. Dynamically import and cache
    config = _ROUTER_CONFIG[name]
    module = __import__(f"{__package__}.{config['module']}", ...)
    router_obj = getattr(module, config['attr'])
    _cache[name] = router_obj
    return router_obj
```

**Workflow:**
1. User accesses `from funboost.faas import fastapi_router`
2. Python triggers `__getattr__('fastapi_router')`
3. Check if configuration exists
4. Check cache, return directly if already cached
5. Otherwise dynamically import and cache result
6. Return router object

### 3. IDE Type Support

```python
if typing.TYPE_CHECKING:
    from .fastapi_adapter import fastapi_router 
    from .flask_adapter import flask_blueprint
    from .django_adapter import django_router
```

**Purpose:**
- Only effective during type checking (won't actually execute)
- Provides IDE code completion and type hints
- Doesn't affect runtime on-demand import

## Key Features

### 1. On-Demand Import
```python
# Only using FastAPI, no need to install Flask/Django
from funboost.faas import fastapi_router  # ✅ Success
```

### 2. Friendly Error Messages
```python
# When fastapi not installed
ImportError: Cannot import fastapi_router, please install fastapi first: pip install fastapi
Original error: No module named 'fastapi'
```

### 3. Automatic Caching
```python
from funboost.faas import fastapi_router as r1
from funboost.faas import fastapi_router as r2
assert r1 is r2  # ✅ True, same object
```

### 4. Backward Compatibility
```python
# All existing code works normally
from funboost.faas import fastapi_router, flask_blueprint, django_router
```

## Comparison: Before and After Refactoring

### Before Refactoring (Hardcoded):
```python
def __getattr__(name: str):
    if name == 'fastapi_router':
        # ...lots of repeated code
    elif name == 'flask_blueprint':
        # ...lots of repeated code
    elif name == 'django_router':
        # ...lots of repeated code
```

**Problems:**
- ❌ Hardcoded judgments
- ❌ Code repetition
- ❌ Difficult to extend
- ❌ Adding new router requires modifying multiple places

### After Refactoring (Configuration-Driven):
```python
_ROUTER_CONFIG = {...}  # Configuration table

def __getattr__(name: str):
    config = _ROUTER_CONFIG[name]
    # Unified import logic
```

**Advantages:**
- ✅ Configuration-driven
- ✅ No code repetition
- ✅ Easy to extend
- ✅ Adding new router only requires modifying configuration

## How to Add New Router

Suppose you want to add a `tornado_router`:

```python
# 1. Add item in configuration
_ROUTER_CONFIG = {
    # ... existing configuration ...
    'tornado_router': {
        'module': 'tornado_adapter',
        'attr': 'tornado_router',
        'package': 'tornado',
        'cache_var': '_tornado_router',
    },
}

# 2. Add to __all__
__all__ = [
    # ... existing exports ...
    'tornado_router',
]

# 3. Add type support in TYPE_CHECKING
if typing.TYPE_CHECKING:
    # ... existing imports ...
    from .tornado_adapter import tornado_router
```

**That's it!** No need to modify the `__getattr__` function.

## Summary

This refactoring achieves:
1. ✅ **Eliminate hardcoding**: Replace multiple if judgments with configuration table
2. ✅ **Improve maintainability**: Code is more concise, logic is clearer
3. ✅ **Enhance extensibility**: Adding new router becomes very easy
4. ✅ **Keep all advantages**: On-demand import, friendly hints, automatic cache, IDE support

## Technical Key Points

- `__getattr__`: Python module-level attribute access interception
- `__import__`: Dynamic module import
- `typing.TYPE_CHECKING`: Distinguish between type checking and runtime
- Configuration-driven design: Use data to drive code logic
- Cache optimization: Avoid repeated imports
