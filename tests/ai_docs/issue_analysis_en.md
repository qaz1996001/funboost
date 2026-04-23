# Issue Analysis: @flyweight Decorator Unhashable Type Error

The issue occurs because the code uses `@flyweight` decorator, and the parameters passed to the decorated function contain unhashable types (such as `list`).

**Detailed Reason:**

1. **Error location**: Your traceback points to `funboost/utils/decorators.py` in `_make_key` function at `return (args, frozenset(kwds.items()))` line.

2. **Principle**: `@flyweight` is a flyweight pattern (or singleton pattern variant) decorator that caches class instances. To distinguish different instances, it needs to generate a unique **Cache Key** based on passed parameters (`args` and `kwargs`).

3. **Conflict point**: When generating Key, it uses `frozenset` and `tuple`, which require their contained elements to be **hashable**. 
    * In your scenario, the `__init__` method of `BoosterDiscovery` class received parameter `booster_dirs`, which is a list (e.g., `['your_booster_dir']`).
    * **Python's `list` is not hashable** (because it's mutable), so when `_make_key` tries to put it into `frozenset`, it throws `TypeError: unhashable type: 'list'`.

**Solution:**

I've modified `funboost/utils/decorators.py` file, enhancing `_make_key` function. Now it automatically detects parameter types. If it finds `list`, `dict`, or `set`, it automatically converts them to hashable `tuple` or `frozenset`. This means you don't need to modify any business code - the original calling method now works normally.

**Modified core code logic:**

```python
    def _make_hashable(value):
        if isinstance(value, dict):
            return tuple(sorted((k, _make_hashable(v)) for k, v in value.items()))
        elif isinstance(value, (list, tuple)):
            return tuple(_make_hashable(v) for v in value)
        elif isinstance(value, set):
            return frozenset(_make_hashable(v) for v in value)
        return value

    def _make_key(args, kwds):
        # ...
        key_args = _make_hashable(args)
        key_kwargs = frozenset((k, _make_hashable(v)) for k, v in kwds.items())
        # ...
```

Now you can retry running your code, it should no longer throw this error.
