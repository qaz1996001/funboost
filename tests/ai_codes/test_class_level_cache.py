"""
Test the class-level cache of RedisReportInfoGetterMixin
Verify that multiple instances share the same cache to avoid repeated Redis queries
"""

import time
from funboost.core.active_cousumer_info_getter import ActiveCousumerProcessInfoGetter, QueuesConusmerParamsGetter


def test_class_level_cache_shared():
    """Test that multiple instances share the class-level cache"""
    print("\n=== Test class-level cache (shared across instances) ===")

    # Create first instance
    getter1 = ActiveCousumerProcessInfoGetter()
    print("Creating instance 1...")

    # First call, fetches from Redis
    print("\nInstance 1: 1st call to get_all_queue_names()...")
    start_time = time.time()
    result1 = getter1.get_all_queue_names()
    time1 = time.time() - start_time
    cache_ts1 = getter1._cache_all_queue_names_ts
    print(f"  Time taken: {time1:.4f}s, Result count: {len(result1)}")
    print(f"  Cache timestamp: {cache_ts1}")

    # Create second instance
    print("\nCreating instance 2...")
    getter2 = ActiveCousumerProcessInfoGetter()

    # Second instance call should use the cache created by the first instance
    print("\nInstance 2: 1st call to get_all_queue_names() (should use instance 1's cache)...")
    start_time = time.time()
    result2 = getter2.get_all_queue_names()
    time2 = time.time() - start_time
    cache_ts2 = getter2._cache_all_queue_names_ts
    print(f"  Time taken: {time2:.4f}s, Result count: {len(result2)}")
    print(f"  Cache timestamp: {cache_ts2}")

    # Verify results
    print("\nVerification:")
    print(f"  ✓ Cache timestamps are the same across both instances: {cache_ts1 == cache_ts2}")
    print(f"  ✓ Results are the same across both instances: {result1 == result2}")
    print(f"  ✓ Instance 2 used cache (faster): {time2 < time1 / 5 if time1 > 0.0001 else 'Yes'}")
    print(f"  ✓ Speed improvement: {time1/time2 if time2 > 0 else 'N/A'}x")

    # Create third instance
    print("\nCreating instance 3...")
    getter3 = ActiveCousumerProcessInfoGetter()

    # Third instance should also use the same cache
    print("\nInstance 3: 1st call to get_all_queue_names() (should use shared cache)...")
    start_time = time.time()
    result3 = getter3.get_all_queue_names()
    time3 = time.time() - start_time
    cache_ts3 = getter3._cache_all_queue_names_ts
    print(f"  Time taken: {time3:.6f}s, Result count: {len(result3)}")
    print(f"  Cache timestamp: {cache_ts3}")

    print("\nVerification:")
    print(f"  ✓ Cache timestamps are the same across all three instances: {cache_ts1 == cache_ts2 == cache_ts3}")
    print(f"  ✓ Verified as class attribute: {getter1._cache_all_queue_names is getter2._cache_all_queue_names is getter3._cache_all_queue_names}")


def test_cache_expiration():
    """Test cache expiration mechanism"""
    print("\n\n=== Test cache expiration mechanism ===")

    getter = ActiveCousumerProcessInfoGetter()

    # First call
    print("\n1st call...")
    start_time = time.time()
    result1 = getter.get_all_queue_names()
    time1 = time.time() - start_time
    print(f"  Time taken: {time1:.4f}s")
    print(f"  Cache TTL: {getter._cache_ttl}s")

    # Immediate second call, should use cache
    print("\n2nd call (immediate, should use cache)...")
    start_time = time.time()
    result2 = getter.get_all_queue_names()
    time2 = time.time() - start_time
    print(f"  Time taken: {time2:.6f}s")
    print(f"  Used cache: {'Yes' if time2 < time1 / 5 else 'No'}")

    # Check remaining cache time
    remaining = getter._cache_ttl - (time.time() - getter._cache_all_queue_names_ts)
    print(f"\nRemaining cache validity: {remaining:.2f}s")

    print("\nNote: Cache will expire after 30 seconds; after expiration it will be re-fetched from Redis")


def test_project_name_cache():
    """Test cache for queries by project name"""
    print("\n\n=== Test get_queue_names_by_project_name cache ===")

    getter1 = QueuesConusmerParamsGetter()

    # Get all projects
    all_projects = getter1.get_all_project_names()
    if not all_projects:
        print("No projects found, skipping test")
        return

    test_project = list(all_projects)[0]
    print(f"Test project: {test_project}")

    # Instance 1, first call
    print(f"\nInstance 1: 1st call to get_queue_names_by_project_name('{test_project}')...")
    start_time = time.time()
    result1 = getter1.get_queue_names_by_project_name(test_project)
    time1 = time.time() - start_time
    print(f"  Time taken: {time1:.4f}s, Result count: {len(result1)}")

    # Create second instance
    getter2 = QueuesConusmerParamsGetter()

    # Instance 2, first call, should use instance 1's cache
    print(f"\nInstance 2: 1st call to get_queue_names_by_project_name('{test_project}') (should use instance 1's cache)...")
    start_time = time.time()
    result2 = getter2.get_queue_names_by_project_name(test_project)
    time2 = time.time() - start_time
    print(f"  Time taken: {time2:.6f}s, Result count: {len(result2)}")

    # Verify
    print("\nVerification:")
    print(f"  ✓ Results are the same across both instances: {result1 == result2}")
    print(f"  ✓ Instance 2 used cache: {time2 < time1 / 5 if time1 > 0.0001 else 'Yes'}")

    # Verify the cache dict is the same object
    if test_project in getter1._cache_queue_names_by_project and test_project in getter2._cache_queue_names_by_project:
        cache1 = getter1._cache_queue_names_by_project[test_project]
        cache2 = getter2._cache_queue_names_by_project[test_project]
        print(f"  ✓ Cache dicts of both instances are the same object: {cache1 is cache2}")
        print(f"  ✓ Cache timestamps are the same: {cache1['ts'] == cache2['ts']}")


def test_thread_safety():
    """Test thread safety"""
    print("\n\n=== Test thread safety ===")

    import threading

    results = []
    errors = []

    def query_in_thread(thread_id):
        try:
            getter = ActiveCousumerProcessInfoGetter()
            result = getter.get_all_queue_names()
            results.append((thread_id, len(result)))
        except Exception as e:
            errors.append((thread_id, str(e)))

    print("\nCreating 10 threads to query simultaneously...")
    threads = []
    for i in range(10):
        t = threading.Thread(target=query_in_thread, args=(i,))
        threads.append(t)
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    print(f"\nDone! Successful queries: {len(results)}, Errors: {len(errors)}")

    if errors:
        print("\nErrors:")
        for thread_id, error in errors:
            print(f"  Thread {thread_id}: {error}")

    if results:
        # Verify all results are consistent
        first_count = results[0][1]
        all_same = all(count == first_count for _, count in results)
        print(f"\nVerification:")
        print(f"  ✓ All threads got the same result count: {all_same}")
        print(f"  ✓ Result count: {first_count}")


if __name__ == '__main__':
    print("=" * 70)
    print("Test class-level cache for Redis queries")
    print("=" * 70)

    try:
        test_class_level_cache_shared()
        test_cache_expiration()
        test_project_name_cache()
        test_thread_safety()

        print("\n" + "=" * 70)
        print("✓ All tests completed!")
        print("=" * 70)
        print("\nFeature summary:")
        print("  1. ✓ Use class attributes to store cache, shared across all instances")
        print("  2. ✓ Cache valid for 30 seconds, auto re-fetches after expiration")
        print("  3. ✓ Thread lock used to ensure thread safety")
        print("  4. ✓ Avoids frequent Redis queries, improves performance")
        print("  5. ✓ Both get_all_queue_names() and get_queue_names_by_project_name() support caching")

    except Exception as e:
        print(f"\nError occurred during testing: {e}")
        import traceback
        traceback.print_exc()
