# typing.TYPE_CHECKING Explained

## What is TYPE_CHECKING?

`typing.TYPE_CHECKING` is a special constant that is **False at runtime** but **True during type checking**.

```python
import typing
print(typing.TYPE_CHECKING)  # Output: False
```

## Main Uses

### 1. Avoiding Circular Imports

**Problem scenario:**
```python
# teacher.py
from student import Student  # Import Student

class Teacher:
    def __init__(self):
        self.students: List[Student] = []

# student.py  
from teacher import Teacher  # Import Teacher - circular import!

class Student:
    def __init__(self):
        self.teacher: Teacher = None
```

**Solution:**
```python
# teacher.py
import typing
if typing.TYPE_CHECKING:
    from student import Student  # Only import during type checking

class Teacher:
    def __init__(self):
        self.students: typing.List['Student'] = []  # Use string annotation
```

### 2. Performance Optimization - Avoiding Expensive Module Imports

**Problem scenario:**
```python
import pandas as pd  # Heavy library, slow to import
import numpy as np   # Heavy library, slow to import

def simple_function(data: pd.DataFrame) -> np.ndarray:
    # This function might be simple and doesn't really need pandas
    return data
```

**Solution:**
```python
import typing
if typing.TYPE_CHECKING:
    import pandas as pd  # Only import during type checking
    import numpy as np

def simple_function(data: 'pd.DataFrame') -> 'np.ndarray':
    # pandas won't be imported at runtime, improving startup speed
    return data
```

### 3. Forward References

**Problem scenario:**
```python
class Node:
    def add_child(self, child: Node) -> None:  # Error! Node is not fully defined yet
        pass
```

**Solution:**
```python
class Node:
    def add_child(self, child: 'Node') -> None:  # Use string
        pass
    
    # Or use TYPE_CHECKING
    if typing.TYPE_CHECKING:
        def method(self, other: Node) -> None:  # Can use directly
            pass
```

### 4. Conditional Type Definitions

```python
if typing.TYPE_CHECKING:
    # Complex type definitions, only needed during type checking
    ComplexType = typing.Union[str, int, typing.Dict[str, typing.Any]]
else:
    # Use simple type at runtime
    ComplexType = object
```

## Why Did the Original Code Raise an Error?

In the original `broker_kind__exclusive_config_default_define.py`:

```python
import typing
if typing.TYPE_CHECKING:
    import logging  # Only import during type checking

def generate_broker_exclusive_config(
    broker_kind: str, 
    user_broker_exclusive_config: dict, 
    logger: logging.Logger  # Accessing logging at runtime, but logging is not imported!
):
    pass
```

**Problem:**
1. `logging` is only imported when `TYPE_CHECKING=True`
2. But at runtime `TYPE_CHECKING=False`, so `logging` is not imported
3. The function signature `logger: logging.Logger` needs to access `logging` at runtime
4. Result: `NameError: name 'logging' is not defined`

**Correct approaches:**

**Approach 1:** Move out of TYPE_CHECKING (the approach we adopted)
```python
import logging  # Import at runtime too
```

**Approach 2:** Use string annotations
```python
if typing.TYPE_CHECKING:
    import logging

def generate_broker_exclusive_config(
    broker_kind: str, 
    user_broker_exclusive_config: dict, 
    logger: 'logging.Logger'  # Use string
):
    pass
```

## Summary

The core idea of `TYPE_CHECKING`:
- **During type checking**: Provide complete type information
- **At runtime**: Avoid unnecessary imports and performance overhead

Use cases:
1. Resolving circular imports
2. Avoiding importing heavy libraries
3. Handling forward references
4. Conditional type definitions

**Key principle:** If type annotations are accessed at runtime (e.g., in function signatures), either truly import the module, or use string-form type annotations.
