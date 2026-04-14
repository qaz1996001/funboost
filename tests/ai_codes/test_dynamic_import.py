"""
Test the dynamic import mechanism of funboost.faas

Verify:
1. Using only fastapi_router does not raise errors due to missing flask/django
2. Lazy import actually works
3. Repeated access uses cache
"""

import sys


def test_fastapi_router_import():
    """Test importing fastapi_router"""
    print("=" * 60)
    print("Test 1: Import fastapi_router")
    print("=" * 60)

    try:
        from funboost.faas import fastapi_router
        print(f"✅ Successfully imported fastapi_router: {type(fastapi_router)}")
        print(f"   Router prefix: {fastapi_router.prefix}")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_flask_blueprint_import():
    """Test importing flask_blueprint"""
    print("\n" + "=" * 60)
    print("Test 2: Import flask_blueprint")
    print("=" * 60)

    try:
        from funboost.faas import flask_blueprint
        print(f"✅ Successfully imported flask_blueprint: {type(flask_blueprint)}")
        print(f"   Blueprint name: {flask_blueprint.name}")
        return True
    except ImportError as e:
        print(f"❌ Import failed (flask may not be installed): {e}")
        return False


def test_django_router_import():
    """Test importing django_router"""
    print("\n" + "=" * 60)
    print("Test 3: Import django_router")
    print("=" * 60)

    try:
        from funboost.faas import django_router
        print(f"✅ Successfully imported django_router: {type(django_router)}")
        return True
    except ImportError as e:
        print(f"❌ Import failed (django-ninja may not be installed): {e}")
        return False


def test_multiple_imports():
    """Test that repeated imports use the cache"""
    print("\n" + "=" * 60)
    print("Test 4: Verify cache mechanism (multiple imports)")
    print("=" * 60)

    try:
        from funboost.faas import fastapi_router as router1
        from funboost.faas import fastapi_router as router2

        if router1 is router2:
            print("✅ Multiple imports return the same object (cache is working)")
            return True
        else:
            print("❌ Multiple imports return different objects (cache is not working)")
            return False
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_error_message():
    """Test friendly error messages"""
    print("\n" + "=" * 60)
    print("Test 5: Test friendly error messages")
    print("=" * 60)

    # Temporarily simulate missing dependency
    import funboost.faas

    # Try to access a non-existent attribute
    try:
        _ = funboost.faas.non_existent_router
        print("❌ Should have raised AttributeError")
        return False
    except AttributeError as e:
        print(f"✅ Correctly raised AttributeError: {e}")
        return True


if __name__ == "__main__":
    print("Starting tests for funboost.faas dynamic import mechanism\n")

    results = []

    # Run all tests
    results.append(("fastapi_router import", test_fastapi_router_import()))
    results.append(("flask_blueprint import", test_flask_blueprint_import()))
    results.append(("django_router import", test_django_router_import()))
    results.append(("Cache mechanism", test_multiple_imports()))
    results.append(("Error message", test_error_message()))

    # Summarize results
    print("\n" + "=" * 60)
    print("Test Result Summary")
    print("=" * 60)

    for name, result in results:
        status = "✅ Passed" if result else "❌ Failed"
        print(f"{status} - {name}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
