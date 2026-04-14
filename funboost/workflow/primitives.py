# -*- coding: utf-8 -*-
"""
Funboost Workflow - Orchestration Primitives

Provides orchestration primitives similar to Celery Canvas:
- Chain: Sequential execution
- Group: Parallel execution
- Chord: Parallel + aggregation

Design philosophy:
- Declarative definition, imperative execution
- Reuses funboost's existing RPC mechanism
- Does not modify funboost core code
"""

import typing
import uuid
from .signature import Signature
from .workflow_mixin import WorkflowPublisherMixin
from funboost.core.msg_result_getter import AsyncResult
from funboost.core.function_result_status_saver import FunctionResultStatus


def _ensure_workflow_context() -> bool:
    """
    Ensure workflow context exists, creating an initial context if it doesn't

    :return: True means a new context was created (caller needs to clean up at the end), False means context already exists
    """
    existing = WorkflowPublisherMixin.get_workflow_context()
    if existing:
        return False  # Already exists, no need to create

    # Create initial workflow context
    initial_ctx = {
        'workflow_id': str(uuid.uuid4()),
        'chain_depth': 0,
        'current_task_id': None,
        'parent_task_id': None,
    }
    WorkflowPublisherMixin.set_workflow_context(initial_ctx)
    return True  # Newly created, caller needs to clean up


class Chain:
    """
    Sequential execution: Executes multiple tasks in order, upstream results automatically passed to downstream

    Usage:
    ```python
    # Method 1: Constructor
    workflow = Chain(task1.s(x), task2.s(), task3.s())

    # Method 2: Convenience function
    workflow = chain(task1.s(x), task2.s(), task3.s())

    # Method 3: | operator
    workflow = task1.s(x) | task2.s() | task3.s()

    # Execute
    result = workflow.apply()
    ```

    Execution flow:
    1. Execute task1, get result r1
    2. Pass r1 as task2's first argument, execute task2, get result r2
    3. Pass r2 as task3's first argument, execute task3, get result r3
    4. Return r3
    """
    
    def __init__(self, *tasks):
        """
        :param tasks: List of tasks, can be Signature, Chain, Group, Chord
        """
        self.tasks = []
        for task in tasks:
            if isinstance(task, Chain):
                # Flatten nested Chain
                self.tasks.extend(task.tasks)
            else:
                self.tasks.append(task)
    
    def apply(self, prev_result=None) -> FunctionResultStatus:
        """
        Synchronously execute the entire chain

        :param prev_result: Externally provided initial result (optional)
        :return: The last task's execution result
        """
        # Ensure workflow context exists (auto-create if not present)
        created_new_ctx = _ensure_workflow_context()
        
        try:
            result = prev_result
            result_status = None
            
            for task in self.tasks:
                if isinstance(task, (Chain, Group, Chord)):
                    result_status = task.apply(prev_result=result)
                    result = result_status.result if isinstance(result_status, FunctionResultStatus) else result_status
                elif isinstance(task, Signature):
                    result_status = task.apply(prev_result=result)
                    result = result_status.result
                else:
                    raise TypeError(f"Unsupported task type: {type(task)}")
            
            return result_status
        finally:
            # Only clean up if this method created the context
            if created_new_ctx:
                WorkflowPublisherMixin.clear_workflow_context()

    def apply_async(self, prev_result=None) -> AsyncResult:
        """
        Asynchronously execute the first task, returning AsyncResult

        Note: For Chain, complete async execution requires a callback mechanism.
        Current implementation only starts the first task.
        """
        if not self.tasks:
            raise ValueError("Chain is empty")
        
        first_task = self.tasks[0]
        if isinstance(first_task, Signature):
            return first_task.apply_async(prev_result)
        else:
            raise NotImplementedError("Async chain with nested primitives not yet supported")
    
    def __or__(self, other):
        """Support | operator to append tasks"""
        if isinstance(other, Signature):
            return Chain(*self.tasks, other)
        elif isinstance(other, Chain):
            return Chain(*self.tasks, *other.tasks)
        else:
            raise TypeError(f"unsupported operand type(s) for |: 'Chain' and '{type(other).__name__}'")
    
    def __repr__(self):
        task_names = [repr(t) for t in self.tasks]
        return f"Chain({', '.join(task_names)})"


class Group:
    """
    Parallel execution: Executes multiple tasks simultaneously, collects all results

    Usage:
    ```python
    # Method 1: Constructor
    g = Group(task.s(1), task.s(2), task.s(3))

    # Method 2: Convenience function
    g = group(task.s(1), task.s(2), task.s(3))

    # Method 3: Generator
    g = group(task.s(i) for i in range(10))

    # Execute
    results = g.apply()  # Returns result list [r1, r2, r3]
    ```
    """
    
    def __init__(self, *tasks):
        """
        :param tasks: List of tasks, supports generators
        """
        # Support passing generators
        if len(tasks) == 1 and hasattr(tasks[0], '__iter__') and not isinstance(tasks[0], (Signature, Chain, Chord)):
            self.tasks = list(tasks[0])
        else:
            self.tasks = list(tasks)
    
    def apply(self, prev_result=None) -> typing.List:
        """
        Execute all tasks in parallel, wait for all to complete

        :param prev_result: Initial result passed to each task (optional)
        :return: List of all task results
        """
        if not self.tasks:
            return []
        
        # Ensure workflow context exists (auto-create if not present)
        created_new_ctx = _ensure_workflow_context()
        
        try:
            # Publish all tasks in parallel
            async_results = []
            for task in self.tasks:
                if isinstance(task, Signature):
                    async_results.append(task.apply_async(prev_result))
                elif isinstance(task, (Chain, Group, Chord)):
                    # For nested structures, execute synchronously (simplified implementation)
                    result = task.apply(prev_result)
                    # Wrap into AsyncResult-like structure for unified processing
                    async_results.append(_WrapperResult(result))
                else:
                    raise TypeError(f"Unsupported task type: {type(task)}")
            
            # Wait for all results
            results = []
            last_task_id = None
            for ar in async_results:
                if isinstance(ar, _WrapperResult):
                    results.append(ar.result)
                else:
                    # AsyncResult
                    status = ar.wait_rpc_data_or_raise(raise_exception=True)
                    results.append(status.result)
                    last_task_id = status.task_id
            
            # Update workflow context after Group completes
            # Use the last task's task_id as current_task_id,
            # so the chord callback's parent_task_id can point to a task in the group
            # Note: _update_workflow_context_after_task also increments chain_depth
            if last_task_id:
                from .signature import _update_workflow_context_after_task
                _update_workflow_context_after_task(last_task_id)
            
            return results
        finally:
            # Only clean up if this method created the context
            if created_new_ctx:
                WorkflowPublisherMixin.clear_workflow_context()
    
    def apply_async(self, prev_result=None) -> typing.List[AsyncResult]:
        """
        Asynchronously publish all tasks

        :return: List of AsyncResults
        """
        async_results = []
        for task in self.tasks:
            if isinstance(task, Signature):
                async_results.append(task.apply_async(prev_result))
            else:
                raise NotImplementedError("Async group with nested primitives not yet supported")
        return async_results
    
    def __repr__(self):
        return f"Group({len(self.tasks)} tasks)"


class _WrapperResult:
    """Helper class for wrapping synchronous execution results"""
    def __init__(self, result):
        if isinstance(result, FunctionResultStatus):
            self.result = result.result
        else:
            self.result = result


class Chord:
    """
    Parallel + aggregation: header executes in parallel, result list passed to body

    Usage:
    ```python
    # Define chord
    c = chord(
        group(task.s(i) for i in range(3)),  # header: parallel execution
        callback.s()  # body: receives result list
    )

    # Execute
    result = c.apply()
    ```

    Execution flow:
    1. Execute all tasks in header in parallel
    2. Collect all results into list [r0, r1, r2]
    3. Execute body with result list as its first argument
    4. Return body's execution result
    """
    
    def __init__(self, header: Group, body: Signature):
        """
        :param header: Task group for parallel execution (Group)
        :param body: Aggregation callback task (Signature)
        """
        if not isinstance(header, Group):
            # Auto-wrap into Group
            if isinstance(header, (list, tuple)):
                header = Group(*header)
            else:
                raise TypeError(f"header must be a Group, got {type(header)}")
        
        self.header = header
        self.body = body
    
    def apply(self, prev_result=None) -> FunctionResultStatus:
        """
        Execute chord

        :param prev_result: Initial result passed to each task in header
        :return: body task's execution result
        """
        # Ensure workflow context exists (auto-create if not present)
        created_new_ctx = _ensure_workflow_context()
        
        try:
            # 1. Execute header (in parallel)
            header_results = self.header.apply(prev_result)
            
            # 2. Execute body with header results list as its first argument
            return self.body.apply(prev_result=header_results)
        finally:
            # Only clean up if this method created the context
            if created_new_ctx:
                WorkflowPublisherMixin.clear_workflow_context()
    
    def __repr__(self):
        return f"Chord(header={self.header}, body={self.body})"


# ============================================================
# Convenience functions
# ============================================================

def chain(*tasks) -> Chain:
    """
    Create a sequential execution workflow

    Usage:
    ```python
    workflow = chain(task1.s(x), task2.s(), task3.s())
    result = workflow.apply()
    ```
    """
    return Chain(*tasks)


def group(*tasks) -> Group:
    """
    Create a parallel execution workflow

    Usage:
    ```python
    g = group(task.s(1), task.s(2), task.s(3))
    results = g.apply()  # [r1, r2, r3]

    # Supports generators
    g = group(task.s(i) for i in range(10))
    ```
    """
    return Group(*tasks)


def chord(header, body) -> Chord:
    """
    Create a parallel+aggregation workflow

    Usage:
    ```python
    c = chord(
        group(task.s(i) for i in range(3)),
        callback.s()
    )
    result = c.apply()
    ```
    """
    if not isinstance(header, Group):
        header = Group(header) if not isinstance(header, (list, tuple)) else Group(*header)
    return Chord(header, body)
