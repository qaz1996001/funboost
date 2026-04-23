# New get_all_queues Interface Description

## Overview

Successfully added new interface `/funboost/get_all_queues` to `funboost_router_for_webs` for getting all registered queue names.

## Modified Files

### 1. Flask Version - `flask_funboost_router.py`

**New Content:**
- Added `get_all_queues()` route function
- Interface path: `/funboost/get_all_queues`
- HTTP method: GET
- Updated startup information including explanation of new interface

**Interface Implementation:**
```python
@funboost_blueprint_for_flask.route("/get_all_queues", methods=['GET'])
def get_all_queues():
    """
    Get all registered queue names
    
    Returns list of all queue names registered via @boost decorator
    """
    try:
        # Get all queue names
        all_queues = list(BoostersManager.get_all_queues())
        
        return jsonify({
            "succ": True,
            "msg": "Retrieved successfully",
            "queues": all_queues,
            "count": len(all_queues)
        })
        
    except Exception as e:
        return jsonify({
            "succ": False,
            "msg": f"Failed to get all queues: {str(e)}",
            "queues": [],
            "count": 0
        }), 500
```

### 2. FastAPI Version - `fastapi_funboost_router.py`

**New Content:**
- Added `AllQueuesResponse` response model
- Added `get_all_queues()` route function
- Interface path: `/funboost/get_all_queues`
- HTTP method: GET
- Updated startup information

**Response Model:**
```python
class AllQueuesResponse(BaseModel):
    succ: bool
    msg: str
    queues: typing.List[str] = []
    count: int = 0
```

**Interface Implementation:**
```python
@fastapi_router.get("/get_all_queues", response_model=AllQueuesResponse)
def get_all_queues():
    """
    Get all registered queue names
    
    Returns list of all queue names registered via @boost decorator
    """
    try:
        # Get all queue names
        all_queues = list(BoostersManager.get_all_queues())
        
        return AllQueuesResponse(
            succ=True,
            msg="Retrieved successfully",
            queues=all_queues,
            count=len(all_queues)
        )
    except Exception as e:
        return AllQueuesResponse(
            succ=False,
            msg=f"Failed to get all queues: {str(e)}",
            queues=[],
            count=0
        )
```

### 3. Django Ninja Version - `django_ninja_funboost_router.py`

**New Content:**
- Added `AllQueuesResponse` response model
- Added `get_all_queues()` route function
- Interface path: `/funboost/get_all_queues`
- HTTP method: GET

**Response Model:**
```python
class AllQueuesResponse(BaseResponse):
    queues: typing.List[str] = []
    count: int = 0
```

**Interface Implementation:**
```python
@funboost_router_for_django_ninja.get("/get_all_queues", response=AllQueuesResponse, summary="Get all queue names")
def get_all_queues(request):
    """
    Get all registered queue names
    
    Returns list of all queue names registered via @boost decorator
    """
    try:
        # Get all queue names
        all_queues = list(BoostersManager.get_all_queues())
        
        return {
            "succ": True,
            "msg": "Retrieved successfully",
            "queues": all_queues,
            "count": len(all_queues)
        }
    except Exception as e:
        return {
            "succ": False,
            "msg": f"Failed to get all queues: {str(e)}",
            "queues": [],
            "count": 0
        }
```

## API Interface Description

### Request

- **URL**: `/funboost/get_all_queues`
- **Method**: GET
- **Parameters**: None

### Response

**Successful Response Example:**
```json
{
    "succ": true,
    "msg": "Retrieved successfully",
    "queues": ["queue1", "queue2", "queue3"],
    "count": 3
}
```

**Failed Response Example:**
```json
{
    "succ": false,
    "msg": "Failed to get all queues: error message",
    "queues": [],
    "count": 0
}
```

### Response Field Description

| Field | Type | Notes |
|------|------|------|
| succ | bool | Whether request was successful |
| msg | str | Response message |
| queues | List[str] | List of all registered queue names |
| count | int | Total number of queues |

## Usage Examples

### Flask Example

```python
import requests

# Get all queues
response = requests.get("http://127.0.0.1:5000/funboost/get_all_queues")
result = response.json()

if result['succ']:
    print(f"Total {result['count']} queues")
    for queue_name in result['queues']:
        print(f"  - {queue_name}")
else:
    print(f"Failed: {result['msg']}")
```

### FastAPI Example

```python
import requests

# Get all queues
response = requests.get("http://127.0.0.1:16666/funboost/get_all_queues")
result = response.json()

if result['succ']:
    print(f"Total {result['count']} queues")
    for queue_name in result['queues']:
        print(f"  - {queue_name}")
else:
    print(f"Failed: {result['msg']}")
```

### Django Ninja Example

```python
import requests

# Get all queues
response = requests.get("http://127.0.0.1:8000/api/funboost/get_all_queues")
result = response.json()

if result['succ']:
    print(f"Total {result['count']} queues")
    for queue_name in result['queues']:
        print(f"  - {queue_name}")
else:
    print(f"Failed: {result['msg']}")
```

### cURL Example

```bash
# Flask
curl http://127.0.0.1:5000/funboost/get_all_queues

# FastAPI
curl http://127.0.0.1:16666/funboost/get_all_queues

# Django Ninja
curl http://127.0.0.1:8000/api/funboost/get_all_queues
```

## Technical Implementation

Interface uses `BoostersManager.get_all_queues()` method to get all registered queue names. This method returns all keys from `queue_name__boost_params_map` dictionary (i.e., queue names).

**Core Logic:**
```python
all_queues = list(BoostersManager.get_all_queues())
```

This method returns all queue names corresponding to functions registered via `@boost` decorator.

## Complete Interface List

Updated `funboost_router_for_webs` provides following interfaces:

1. **POST `/funboost/publish`** - Publish message to specified queue
2. **GET `/funboost/get_result`** - Get task execution result by task_id
3. **GET `/funboost/get_msg_count`** - Get message count by queue_name
4. **GET `/funboost/get_all_queues`** ⭐ **New** - Get all registered queue names

## Test File

Created test file `tests/ai_codes/test_get_all_queues_api.py` for testing new interface functionality. This file includes test functions for Flask, FastAPI, and Django Ninja three versions.

## Precautions

1. Interface returns list of all queues registered via `@boost` decorator
2. If no queues registered, will return empty list
3. Need to ensure consuming function definitions are loaded before starting web service (via import or BoosterDiscovery)
4. Interface doesn't need any parameters, just GET request

## Summary

✅ Successfully added `/funboost/get_all_queues` interface for Flask, FastAPI, and Django Ninja three versions  
✅ Interface implementation complete, includes error handling  
✅ Updated startup information and documentation  
✅ Created test example files supporting three frameworks  
✅ README.md includes interface description
