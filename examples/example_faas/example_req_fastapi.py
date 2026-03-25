"""
funboost.faas FastAPI Router interface test examples

This example demonstrates how to use the interfaces provided by funboost.faas:

1. test_publish_and_get_result - demonstrates publishing a message and waiting for the result (RPC mode)
2. test_get_msg_count - demonstrates getting the number of messages in a queue
3. test_publish_async_then_get_result - demonstrates async publishing, first getting the task_id, then retrieving the result by task_id
4. test_get_all_queues - demonstrates getting all registered queue names

"""

import requests
import time
import json

base_url = "http://127.0.0.1:8000"

def test_publish_and_get_result():
    """Test publishing a message and waiting for the result (RPC mode)

    The endpoint validates whether the queue_name exists and whether the message content is correct,
    so you don't need to worry about cross-team users providing a wrong queue_name or incorrect message content.
    Users can first call /get_queues_config to get configuration info for all queues, which shows
    what queues exist and what input parameters each queue's consumer function expects.
    """
    print("=" * 60)
    print("1. Testing publish and get result (RPC mode)...")
    print("=" * 60)

    url = f"{base_url}/funboost/publish"
    data = {
        "queue_name": "test_funboost_faas_queue",
        "msg_body": {"x": 10, "y": 20},
        "need_result": True,
        "timeout": 10
    }
    # publish
    try:
        resp = requests.post(url, json=data)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")

        if resp.status_code == 200:
            result_data = resp.json()
            if result_data['succ']:
                # New format: data is in the 'data' field
                task_id = result_data['data']['task_id']
                status_and_result = result_data['data']['status_and_result']
                print(f"\n✅ Success!")
                print(f"Task ID: {task_id}")
                print(f"Result: {status_and_result}")
            else:
                print(f"\n❌ Failed: {result_data['msg']}")
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

def test_get_msg_count():
    """Test getting the number of messages in a queue"""
    print("\n" + "=" * 60)
    print("2. Testing get message count...")
    print("=" * 60)

    url = f"{base_url}/funboost/get_msg_count"
    params = {"queue_name": "test_funboost_faas_queue"}

    try:
        resp = requests.get(url, params=params)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")

        if resp.status_code == 200:
            result_data = resp.json()
            if result_data['succ']:
                # New format: data is in the 'data' field
                queue_name = result_data['data']['queue_name']
                count = result_data['data']['count']
                print(f"\n✅ Success!")
                print(f"Queue: {queue_name}")
                print(f"Message Count: {count}")
            else:
                print(f"\n❌ Failed: {result_data['msg']}")
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

def test_publish_async_then_get_result():
    """Test async publishing: first get the task_id, then retrieve the result by task_id"""
    print("\n" + "=" * 60)
    print("3. Testing publish async then get result by task_id...")
    print("=" * 60)

    # Step 1: Publish message (without waiting for result)
    url_pub = f"{base_url}/funboost/publish"
    data = {
        "queue_name": "test_funboost_faas_queue",
        "msg_body": {"x": 33, "y": 44},
        "need_result": False,  # Do not wait for result; return immediately
    }

    try:
        resp = requests.post(url_pub, json=data)
        print(f"Publish Status Code: {resp.status_code}")
        print(f"Publish Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")

        if resp.status_code == 200:
            result_data = resp.json()
            if result_data['succ']:
                # New format: data is in the 'data' field
                task_id = result_data['data']['task_id']
                print(f"\n✅ Message published!")
                print(f"Task ID: {task_id}")

                if task_id:
                    # Step 2: Retrieve result by task_id
                    print("\nWaiting for task to complete...")
                    time.sleep(0.2)  # Wait a short time for the task to finish

                    url_get = f"{base_url}/funboost/get_result"
                    params = {"task_id": task_id, "timeout": 5}
                    resp_get = requests.get(url_get, params=params)

                    print(f"\nGet Result Status Code: {resp_get.status_code}")
                    print(f"Get Result Response: {json.dumps(resp_get.json(), indent=2, ensure_ascii=False)}")

                    if resp_get.status_code == 200:
                        get_result_data = resp_get.json()
                        if get_result_data['succ']:
                            # New format: data is in the 'data' field
                            status_and_result = get_result_data['data']['status_and_result']
                            print(f"\n✅ Got result!")
                            print(f"Result: {status_and_result}")
                        else:
                            print(f"\n⚠️  {get_result_data['msg']}")
            else:
                print(f"\n❌ Publish failed: {result_data['msg']}")
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

def test_get_all_queues():
    """Test getting all registered queue names"""
    print("\n" + "=" * 60)
    print("4. Testing get all queues...")
    print("=" * 60)

    url = f"{base_url}/funboost/get_all_queues"

    try:
        resp = requests.get(url)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")

        if resp.status_code == 200:
            result_data = resp.json()
            if result_data['succ']:
                # New format: data is in the 'data' field
                queues = result_data['data']['queues']
                count = result_data['data']['count']
                print(f"\n✅ Success!")
                print(f"Total Queues: {count}")
                print(f"Queue List:")
                for i, queue in enumerate(queues, 1):
                    print(f"  {i}. {queue}")
            else:
                print(f"\n❌ Failed: {result_data['msg']}")
    except Exception as e:
        print(f"\n❌ Request failed: {e}")


def test_get_one_queue_config():
    """Test getting the configuration of a single registered queue"""
    print("\n" + "=" * 60)
    print("4. Testing get all queues...")
    print("=" * 60)

    url = f"{base_url}/funboost/get_one_queue_config"
    params = {"queue_name": "test_funboost_faas_queue"}
    resp = requests.get(url, params=params)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")

    if resp.status_code == 200:
        result_data = resp.json()
        if result_data['succ']:
            print(f"\n✅ Success!")
            print(f"Queue Config: {result_data['data']}")
        else:
            print(f"\n❌ Failed: {result_data['msg']}")



if __name__ == "__main__":
    print("\n" + "🚀 " * 20)
    print("FastAPI Funboost faas Interface Tests")
    print("🚀 " * 20)

    # Test all 4 interfaces
    test_publish_and_get_result()
    test_get_msg_count()
    test_publish_async_then_get_result()
    test_get_all_queues()
    test_get_one_queue_config()

    print("\n" + "✅ " * 20)
    print("Tests complete!")
    print("✅ " * 20 + "\n")
