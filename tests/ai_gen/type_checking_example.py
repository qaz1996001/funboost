"""
Demonstrate the purpose and usage of typing.TYPE_CHECKING
"""
import typing

# Case 1: Avoid circular imports
if typing.TYPE_CHECKING:
    # These imports are only executed during type checking, not at runtime
    from some_heavy_module import HeavyClass
    from collections.abc import Callable
    import logging

# Case 2: Forward reference issue
class Node:
    def __init__(self, value: int, parent: typing.Optional['Node'] = None):
        self.value = value
        self.parent = parent
        self.children: typing.List['Node'] = []

    # In TYPE_CHECKING the type can be used directly
    if typing.TYPE_CHECKING:
        def add_child(self, child: Node) -> None:  # Can use Node directly
            pass
    else:
        def add_child(self, child: 'Node') -> None:  # At runtime a string is needed
            self.children.append(child)

# Case 3: Avoid importing expensive modules
def process_data(data: typing.Any) -> typing.Any:
    """
    If we need to import a large module only for type annotations,
    we can put the import inside TYPE_CHECKING
    """
    # Actual processing logic
    return data

# Direct import would affect performance
if typing.TYPE_CHECKING:
    import pandas as pd
    import numpy as np

def analyze_dataframe(df: 'pd.DataFrame') -> 'np.ndarray':
    """
    Use string-form type annotations to avoid importing pandas and numpy at runtime
    """
    # The actual function may not need these libraries; they are only for type hints
    return df.values

# Case 4: Resolving circular imports
# Assume two modules reference each other
class Teacher:
    def __init__(self, name: str):
        self.name = name
        if typing.TYPE_CHECKING:
            # Only import during type checking to avoid circular imports
            from student_module import Student
        self.students: typing.List['Student'] = []

# Case 5: Different behavior at runtime vs. during type checking
if typing.TYPE_CHECKING:
    # Use precise type during type checking
    LoggerType = logging.Logger
else:
    # Use simple type or Any at runtime
    LoggerType = typing.Any

def setup_logging(logger: LoggerType) -> None:
    """
    This allows avoiding importing the logging module at runtime (if not needed)
    """
    pass

# Case 6: Conditional type definitions
if typing.TYPE_CHECKING:
    # Only define these complex types during type checking
    JsonDict = typing.Dict[str, typing.Any]
    CallbackFunc = typing.Callable[[str], None]
else:
    # Use simple definitions at runtime
    JsonDict = dict
    CallbackFunc = object

def process_json(data: JsonDict, callback: CallbackFunc) -> None:
    """Use conditionally defined types"""
    pass

print("Value of TYPE_CHECKING at runtime:", typing.TYPE_CHECKING)
print("This file can run normally without importing modules inside the TYPE_CHECKING block")
