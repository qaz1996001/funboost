# Unified Response Format Description

## Overview

All `funboost_router_for_webs` interfaces now use unified response format:

```json
{
    "succ": true/false,
    "msg": "Message content",
    "data": {
        // Specific data fields
    }
}
```

## Response Format Details

### Common Fields

| Field | Type | Notes |
|------|------|------|
| succ | bool | Whether request succeeded |
| msg | str | Response message describing operation result or error |
| data | object/null | Specific response data, may be null on failure |

### data Field for Each Interface

#### 1. POST `/funboost/publish` - Publish Message

**Successful Response Example:**
```json
{
    "succ": true,
    "msg": "Message published successfully to test_queue",
    "data": {
        "task_id": "abc123...",
        "status_and_result": null  // or specific result (RPC mode)
    }
}
```

**Failed Response Example:**
```json
{
    "succ": false,
    "msg": "Message publish failed ...",
    "data": {
        "task_id": null,
        "status_and_result": null
    }
}
```

**data Field Notes:**
- `task_id`: Task ID
- `status_and_result`: Task execution result in RPC mode

#### 2. GET `/funboost/get_result` - Get Task Result

**Successful Response Example:**
```json
{
    "succ": true,
    "msg": "Retrieved successfully",
    "data": {
        "task_id": "abc123...",
        "status_and_result": {
            "task_id": "abc123...",
            "result": 100,
            "success": true
        }
    }
}
```

**Failed Response Example:**
```json
{
    "succ": false,
    "msg": "Failed to retrieve result (may be expired or not started executing or timed out)",
    "data": {
        "task_id": "abc123...",
        "status_and_result": null
    }
}
```

**data Field Notes:**
- `task_id`: Task ID
- `status_and_result`: Task execution status and result

#### 3. GET `/funboost/get_msg_count` - Get Message Count

**Successful Response Example:**
```json
{
    "succ": true,
    "msg": "Retrieved successfully",
    "data": {
        "queue_name": "test_queue",
        "count": 42
    }
}
```

**Failed Response Example:**
```json
{
    "succ": false,
    "msg": "Failed to get message count: ...",
    "data": {
        "queue_name": "test_queue",
        "count": -1
    }
}
```

**data Field Notes:**
- `queue_name`: Queue name
- `count`: Message count, -1 on failure

#### 4. GET `/funboost/get_all_queues` - Get All Queues

**Successful Response Example:**
```json
{
    "succ": true,
    "msg": "Retrieved successfully",
    "data": {
        "queues": ["queue1", "queue2", "queue3"],
        "count": 3
    }
}
```

**Failed Response Example:**
```json
{
    "succ": false,
    "msg": "Failed to get all queues: ...",
    "data": {
        "queues": [],
        "count": 0
    }
}
```

**data Field Notes:**
- `queues`: List of all queue names
- `count`: Total queue count

## Usage Examples

### Python Example

```python
import requests

# Call interface
response = requests.get("http://127.0.0.1:5000/funboost/get_all_queues")
result = response.json()

# Check if successful
if result['succ']:
    # Access data
    data = result['data']
    print(f"Total {data['count']} queues")
    for queue_name in data['queues']:
        print(f"  - {queue_name}")
else:
    print(f"Request failed: {result['msg']}")
```

### JavaScript/TypeScript Example

```javascript
// Call interface
const response = await fetch('http://127.0.0.1:5000/funboost/get_all_queues');
const result = await response.json();

// Check if successful
if (result.succ) {
    // Access data
    const { queues, count } = result.data;
    console.log(`Total ${count} queues`);
    queues.forEach(queueName => {
        console.log(`  - ${queueName}`);
    });
} else {
    console.error(`Request failed: ${result.msg}`);
}
```

### TypeScript Type Definition

```typescript
// Base response type
interface BaseResponse<T> {
    succ: boolean;
    msg: string;
    data: T | null;
}

// Publish message response
interface PublishData {
    task_id: string | null;
    status_and_result: any | null;
}
type PublishResponse = BaseResponse<PublishData>;

// Get message count response
interface CountData {
    queue_name: string;
    count: number;
}
type CountResponse = BaseResponse<CountData>;

// Get all queues response
interface AllQueuesData {
    queues: string[];
    count: number;
}
type AllQueuesResponse = BaseResponse<AllQueuesData>;
```

## Advantages

Using unified `{"succ":xx,"msg":xx,"data":{...}}` format has following advantages:

1. **Clear Structure**: Business data uniformly placed in `data` field, separated from metadata
2. **Easy to Parse**: Frontend can uniformly process response format
3. **Type Safe**: Easier to define TypeScript types
4. **Good Extensibility**: Can add other metadata fields at top level in future (like `timestamp`, `request_id`)
5. **Strong Consistency**: All interfaces use same format, reduces learning cost

## Migration Guide

If using old version (data fields directly at top level), need following adjustments:

### Old Version
```python
result = response.json()
queues = result['queues']  # Direct access
count = result['count']
```

### New Version
```python
result = response.json()
queues = result['data']['queues']  # Access via data
count = result['data']['count']
```

## Framework Support

All three web framework versions have been updated to unified format:

- ✅ Flask (`flask_funboost_router.py`)
- ✅ FastAPI (`fastapi_funboost_router.py`)
- ✅ Django Ninja (`django_ninja_funboost_router.py`)

## Summary

Unified response format makes API more standard and easier to use. Recommend all new projects adopt this format. If you have any questions or suggestions, welcome to provide feedback!
