# test_api_client.py
import requests
import time
import json

# Base URL for the Web API
BASE_URL = "http://127.0.0.1:5000"

def print_step(message):
    """Format and print a step header"""
    print("\n" + "="*50)
    print(f"  {message}")
    print("="*50)

def add_task(task_id, interval, message):
    """Call the API to add a scheduled task"""
    url = f"{BASE_URL}/add_task"
    payload = {
        "task_id": task_id,
        "interval_seconds": interval,
        "message": message
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception if the request fails
        print(f"Task '{task_id}' added successfully: {response.json().get('message')}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to add task '{task_id}': {e}")

def get_tasks():
    """Call the API to list all scheduled tasks"""
    url = f"{BASE_URL}/get_tasks"
    try:
        response = requests.get(url)
        response.raise_for_status()
        tasks = response.json()
        print("Currently scheduled tasks:")
        if not tasks:
            print("  - (none)")
        else:
            for task in tasks:
                print(f"  - ID: {task['id']}, Next run time: {task['next_run_time']}")
        return tasks
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve task list: {e}")
        return []

def remove_task(task_id):
    """Call the API to remove a scheduled task"""
    url = f"{BASE_URL}/remove_task/{task_id}"
    try:
        response = requests.delete(url)
        response.raise_for_status()
        print(f"Task '{task_id}' removed successfully: {response.json().get('message')}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to remove task '{task_id}': {e}")


if __name__ == "__main__":
    print_step("Step 1: Add two scheduled tasks")
    add_task("task_A", 5, "This is task A, running every 5 seconds")
    add_task("task_B", 8, "This is task B, running every 8 seconds")
    time.sleep(1)

    print_step("Step 2: View the current task list")
    get_tasks()

    wait_seconds = 20
    print_step(f"Step 3: Wait {wait_seconds} seconds to observe background Worker output...")
    for i in range(wait_seconds, 0, -1):
        print(f"\rCountdown: {i} seconds...", end="")
        time.sleep(1)
    print("\nWait complete.")

    # print_step("Step 4: Remove task 'task_A'")
    # remove_task("task_A")
    # time.sleep(1)
    #
    # print_step("Step 5: View the task list again to confirm 'task_A' has been removed")
    # get_tasks()
    #
    # print("\nClient test execution complete.")
