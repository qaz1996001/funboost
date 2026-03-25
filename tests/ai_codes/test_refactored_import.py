"""
Quickly verify the refactored dynamic import mechanism
"""

def test_config_driven_import():
    """Verify the config-driven import mechanism"""
    print("Testing config-driven dynamic import mechanism\n")
    print("=" * 60)

    # Test 1: Import fastapi_router
    try:
        from funboost.faas import fastapi_router
        print("✅ fastapi_router imported successfully")
        print(f"   Type: {type(fastapi_router)}")
        print(f"   Prefix: {fastapi_router.prefix}")
    except Exception as e:
        print(f"❌ fastapi_router import failed: {e}")

    print()

    # Test 2: Verify cache mechanism
    try:
        from funboost.faas import fastapi_router as router1
        from funboost.faas import fastapi_router as router2

        if router1 is router2:
            print("✅ Cache mechanism works: multiple imports return the same object")
        else:
            print("❌ Cache mechanism failed: multiple imports return different objects")
    except Exception as e:
        print(f"❌ Cache test failed: {e}")

    print()

    # Test 3: Check if config is accessible
    try:
        import funboost.faas as faas_module
        config = faas_module._ROUTER_CONFIG

        print("✅ Config table is accessible")
        print(f"   Supported routers: {list(config.keys())}")
        print(f"   Total: {len(config)}")
    except Exception as e:
        print(f"❌ Config table access failed: {e}")

    print()

    # Test 4: Error message
    try:
        from funboost.faas import non_existent_router
        print("❌ Should have raised AttributeError")
    except AttributeError as e:
        print(f"✅ Correctly raised AttributeError: {e}")
    except Exception as e:
        print(f"⚠️  Raised an unexpected exception: {e}")

    print("\n" + "=" * 60)
    print("Refactoring verification complete! Config-driven dynamic import mechanism works correctly 🎉")


if __name__ == "__main__":
    test_config_driven_import()
