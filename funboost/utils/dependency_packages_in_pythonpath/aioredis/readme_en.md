## 1 The aioredis Package Will No Longer Be Updated, Python 3.11 Import Error

Related issue: https://github.com/aio-libs/aioredis-py/issues/1443

## 2 aioredis.exceptions.py TimeoutError Has Issues in Python 3.11

### 2.1 Current Incorrect Version

```python
class TimeoutError(asyncio.TimeoutError, builtins.TimeoutError, RedisError):
    pass
```

### 2.2 Adapted for Python 3.11

```python
class TimeoutError(asyncio.TimeoutError, RedisError):
    pass
```

The main change is here. Since importing causes an error immediately, it's inconvenient to use monkey patching to replace it. Therefore, funboost no longer uses the aioredis package directly, but instead imports the code from here.
