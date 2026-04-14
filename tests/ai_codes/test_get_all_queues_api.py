"""
Example code for testing the get_all_queues API

This file shows how to use the newly added /funboost/get_all_queues endpoint
"""

import requests

# Test Flask version
def test_flask_get_all_queues():
    """Test the Flask version of the get_all_queues endpoint"""
    url = "http://127.0.0.1:5000/funboost/get_all_queues"

    try:
        response = requests.get(url)
        result = response.json()

        print("=" * 50)
        print("Flask endpoint test result:")
        print(f"Success: {result['succ']}")
        print(f"Message: {result['msg']}")
        if result.get('data'):
            print(f"Total queues: {result['data']['count']}")
            print(f"Queue list: {result['data']['queues']}")
        print("=" * 50)

        return result
    except Exception as e:
        print(f"Request failed: {e}")
        return None


# Test FastAPI version
def test_fastapi_get_all_queues():
    """Test the FastAPI version of the get_all_queues endpoint"""
    url = "http://127.0.0.1:16666/funboost/get_all_queues"

    try:
        response = requests.get(url)
        result = response.json()

        print("=" * 50)
        print("FastAPI endpoint test result:")
        print(f"Success: {result['succ']}")
        print(f"Message: {result['msg']}")
        if result.get('data'):
            print(f"Total queues: {result['data']['count']}")
            print(f"Queue list: {result['data']['queues']}")
        print("=" * 50)

        return result
    except Exception as e:
        print(f"Request failed: {e}")
        return None


# Test Django Ninja version
def test_django_ninja_get_all_queues():
    """Test the Django Ninja version of the get_all_queues endpoint"""
    url = "http://127.0.0.1:8000/api/funboost/get_all_queues"

    try:
        response = requests.get(url)
        result = response.json()

        print("=" * 50)
        print("Django Ninja endpoint test result:")
        print(f"Success: {result['succ']}")
        print(f"Message: {result['msg']}")
        if result.get('data'):
            print(f"Total queues: {result['data']['count']}")
            print(f"Queue list: {result['data']['queues']}")
        print("=" * 50)

        return result
    except Exception as e:
        print(f"Request failed: {e}")
        return None


if __name__ == "__main__":
    print("Starting tests for the get_all_queues endpoint...")
    print("\nPlease make sure the corresponding web service is already running\n")

    # Test Flask version
    print("Testing Flask version (port 5000):")
    test_flask_get_all_queues()

    print("\n")

    # Test FastAPI version
    print("Testing FastAPI version (port 16666):")
    test_fastapi_get_all_queues()

    print("\n")

    # Test Django Ninja version
    print("Testing Django Ninja version (port 8000):")
    test_django_ninja_get_all_queues()
