"""
Demo of the dynamic import mechanism of funboost.faas

Scenarios:
1. Projects using only FastAPI do not need to install Flask or Django
2. Projects using only Flask do not need to install FastAPI or Django
3. Import whichever you need; they do not interfere with each other
"""

# Example 1: Use only FastAPI
def example_fastapi_only():
    """Case of using only FastAPI"""
    print("=" * 60)
    print("Example 1: Use only FastAPI")
    print("=" * 60)

    from fastapi import FastAPI
    from funboost.faas import fastapi_router

    app = FastAPI()
    app.include_router(fastapi_router)

    print("✅ FastAPI app created successfully, funboost_router included")
    print(f"   Routes: {[route.path for route in app.routes]}")
    return app


# Example 2: Use only Flask
def example_flask_only():
    """Case of using only Flask"""
    print("\n" + "=" * 60)
    print("Example 2: Use only Flask")
    print("=" * 60)

    try:
        from flask import Flask
        from funboost.faas import flask_blueprint

        app = Flask(__name__)
        app.register_blueprint(flask_blueprint)

        print("✅ Flask app created successfully, flask_blueprint registered")
        print(f"   Blueprints: {list(app.blueprints.keys())}")
        return app
    except ImportError as e:
        print(f"⚠️  Flask not installed: {e}")
        return None


# Example 3: Use only Django
def example_django_only():
    """Case of using only Django"""
    print("\n" + "=" * 60)
    print("Example 3: Use only Django-Ninja")
    print("=" * 60)

    try:
        from ninja import NinjaAPI
        from funboost.faas import django_router

        api = NinjaAPI()
        api.add_router("/funboost", django_router)

        print("✅ Django NinjaAPI created successfully, django_router added")
        return api
    except ImportError as e:
        print(f"⚠️  Django-Ninja not installed: {e}")
        return None


# Example 4: Dynamic selection
def example_dynamic_selection(framework: str):
    """Dynamically select a framework based on configuration"""
    print("\n" + "=" * 60)
    print(f"Example 4: Dynamically select framework - {framework}")
    print("=" * 60)

    if framework == "fastapi":
        try:
            from funboost.faas import fastapi_router
            print(f"✅ Successfully imported {framework} router")
            return fastapi_router
        except ImportError as e:
            print(f"❌ Import failed: {e}")

    elif framework == "flask":
        try:
            from funboost.faas import flask_blueprint
            print(f"✅ Successfully imported {framework} blueprint")
            return flask_blueprint
        except ImportError as e:
            print(f"❌ Import failed: {e}")

    elif framework == "django":
        try:
            from funboost.faas import django_router
            print(f"✅ Successfully imported {framework} router")
            return django_router
        except ImportError as e:
            print(f"❌ Import failed: {e}")

    else:
        print(f"⚠️  Unknown framework: {framework}")
        return None


if __name__ == "__main__":
    print("Funboost FAAS Dynamic Import Mechanism Demo\n")

    # Run examples
    fastapi_app = example_fastapi_only()
    flask_app = example_flask_only()
    django_api = example_django_only()

    # Dynamic selection example
    dynamic_router = example_dynamic_selection("fastapi")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("""
Advantages:
1. ✅ Import on demand: only import the framework adapter actually used
2. ✅ Friendly hints: clear installation instructions when dependencies are missing
3. ✅ Zero intrusiveness: does not affect existing code, fully backward compatible
4. ✅ IDE support: maintain code hints and type checking via TYPE_CHECKING

Usage:
    from funboost.faas import fastapi_router     # only need fastapi
    from funboost.faas import flask_blueprint    # only need flask
    from funboost.faas import django_router      # only need django-ninja
    """)
