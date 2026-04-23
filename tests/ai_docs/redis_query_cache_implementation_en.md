# Redis Query Cache Implementation

## Overview

Added 30-second caching mechanism to `RedisReportInfoGetterMixin` class to cache Redis query results, reducing frequent Redis queries and improving performance.

## Implementation Method

### Class Attribute Cache (Shared Among All Instances)

Using **class attributes** instead of instance attributes because:
- `RedisReportInfoGetterMixin` allows multiple instantiation
- Using class attributes allows all instances to share same cache
- Avoid each instance repeatedly querying Redis

### Cache Class Attributes

```python
class RedisReportInfoGetterMixin:
    # Class attributes: cache shared by all instances
    _cache_all_queue_names = None              # Cache all queue names
    _cache_all_queue_names_ts = 0              # Cache timestamp
    _cache_queue_names_by_project = {}         # Cache by project name {project_name: {'data': [...], 'ts': timestamp}}
    _cache_ttl = 30                            # Cache validity period 30 seconds
    _cache_lock = threading.Lock()             # Thread lock for thread safety
```

## Cached Methods

### 1. `get_all_queue_names()`

Get all queue names with 30-second cache.

**Workflow:**
1. Check if cache exists and not expired (within 30 seconds)
2. If cache valid, return cached result directly
3. If cache expired, query from Redis
4. Update cache and timestamp

**Example:**
```python
# Create instance1
getter1 = ActiveCousumerProcessInfoGetter()
result1 = getter1.get_all_queue_names()  # Query from Redis

# Create instance2
getter2 = ActiveCousumerProcessInfoGetter()
result2 = getter2.get_all_queue_names()  # Use instance1's cache, no Redis query
```

### 2. `get_queue_names_by_project_name(project_name)`

Get queue names by project name with 30-second cache.

**Workflow:**
1. Check if this project's cache exists and not expired
2. If cache valid, return cached result directly
3. If cache expired, query from Redis
4. Update this project's cache

**Example:**
```python
getter = QueuesConusmerParamsGetter()
result1 = getter.get_queue_names_by_project_name('project1')  # Query from Redis
result2 = getter.get_queue_names_by_project_name('project1')  # Use cache
result3 = getter.get_queue_names_by_project_name('project2')  # Different project, query from Redis
```

## Thread Safety

Using `threading.Lock()` to ensure thread safety:
- Acquire lock before reading cache
- Acquire lock when updating cache
- Avoid race conditions when multiple threads access simultaneously

```python
with self._cache_lock:
    if self._cache_all_queue_names is not None and (current_time - self._cache_all_queue_names_ts) < self._cache_ttl:
        return self._cache_all_queue_names
```

## Performance Improvement

### Performance Improvement on Cache Hit

- **First query:** Needs to access Redis, takes approximately 0.001-0.01 seconds
- **Cache hit:** Returns memory data directly, takes approximately 0.000001-0.00001 seconds
- **Speed improvement:** Approximately 100-1000 times faster

### Applicable Scenarios

Particularly suitable for:
1. Web admin panel frequently refreshing queue list
2. Monitoring dashboard periodically polling queue status
3. Multiple consumer instances simultaneously querying queue information
4. High concurrency queue information queries

## Cache Expiration Mechanism

- **Cache time:** 30 seconds
- **After expiration:** Automatically query from Redis again
- **No manual cleanup needed:** Cache automatically expires and updates

## Affected Classes

Since using Mixin pattern, following classes inherit cache functionality:

1. **ActiveCousumerProcessInfoGetter** - Get active consumer process information
2. **QueuesConusmerParamsGetter** - Get all queue configuration parameters and running information  
3. **SingleQueueConusmerParamsGetter** - Get single queue configuration parameters and running information

All instances of these classes share same cache.

## Testing

Run test file to verify functionality:

```bash
python tests/ai_codes/test_class_level_cache.py
```

Test content includes:
- ✓ Multiple instances share class-level cache
- ✓ Cache expiration mechanism
- ✓ Cache by project name query
- ✓ Thread safety

## Precautions

1. **Cache validity period:** Default 30 seconds, can modify `_cache_ttl` class attribute
2. **Real-time requirement:** If real-time data needed, wait for cache expiration or restart application
3. **Memory usage:** Cache data is small, negligible impact on memory
4. **Thread safety:** Already using thread lock, can use in multi-threaded environment

## Configuration Adjustment

To adjust cache time, can modify class attribute:

```python
# Change cache time to 60 seconds
RedisReportInfoGetterMixin._cache_ttl = 60

# Or override in subclass
class MyGetter(ActiveCousumerProcessInfoGetter):
    _cache_ttl = 60  # 60-second cache
```

## Summary

This cache mechanism improves performance by:
1. ✓ Using class attributes to let all instances share cache
2. ✓ 30-second cache time balances real-time and performance
3. ✓ Thread lock ensures multi-thread safety
4. ✓ Automatic expiration mechanism requires no manual management
5. ✓ Greatly reduces Redis query count
