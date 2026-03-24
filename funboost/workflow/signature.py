# -*- coding: utf-8 -*-
"""
Funboost Workflow - Signature (Task Signature)

Signature represents a "pending" task, containing:
- A reference to a booster (function decorated with @boost)
- The call parameters (args, kwargs)
- Whether to ignore upstream results (immutable)

Similar to Celery's signature / s() concept.
"""

import typing
from funboost.core.msg_result_getter import AsyncResult
from funboost.core.function_result_status_saver import FunctionResultStatus
from .workflow_mixin import WorkflowPublisherMixin


def _update_workflow_context_after_task(task_id: str):
    """
    Update workflow_context's current_task_id and chain_depth after a task completes

    This solves the problem in primitives orchestration scenarios:
    - Publisher publishes task A, waits for RPC result
    - A completes, publisher needs to know A's task_id
    - When publisher publishes task B, B's parent_task_id should be A's task_id
    - Also increments chain_depth so B's level is one deeper than A's
    """
    ctx = WorkflowPublisherMixin.get_workflow_context()
    if ctx:
        ctx = ctx.copy()
        ctx['current_task_id'] = task_id
        ctx['chain_depth'] = ctx.get('chain_depth', 0) + 1  # Increment level
        WorkflowPublisherMixin.set_workflow_context(ctx)


class Signature:
    """
    Task Signature - represents a pending task and its parameters

    Usage:
    ```python
    # Method 1: Create directly
    sig = Signature(my_task, args=(1, 2), kwargs={'name': 'test'})

    # Method 2: Via convenience function (recommended)
    sig = my_task.s(1, 2, name='test')

    # Execute signature
    result = sig.apply()  # Synchronous
    async_result = sig.apply_async()  # Asynchronous
    ```
    """
    
    def __init__(self, 
                 booster, 
                 args: tuple = None, 
                 kwargs: dict = None, 
                 immutable: bool = False):
        """
        :param booster: Function decorated with @boost
        :param args: Positional arguments
        :param kwargs: Keyword arguments
        :param immutable: Whether to ignore upstream results (used in chain scenarios)
        """
        self.booster = booster
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.immutable = immutable
    
    def s(self, *args, **kwargs) -> 'Signature':
        """
        Create a new signature with merged parameters (similar to Celery's .s() method)
        
        用法：
        ```python
        sig = my_task.s(1, 2, name='test')
        ```
        """
        merged_args = self.args + args
        merged_kwargs = {**self.kwargs, **kwargs}
        return Signature(self.booster, merged_args, merged_kwargs, self.immutable)
    
    def si(self, *args, **kwargs) -> 'Signature':
        """
        Create an immutable signature (ignores upstream results)

        When used in a chain, the upstream task's result will not be passed as the first argument.
        """
        merged_args = self.args + args
        merged_kwargs = {**self.kwargs, **kwargs}
        return Signature(self.booster, merged_args, merged_kwargs, immutable=True)
    
    def set_immutable(self, immutable: bool = True) -> 'Signature':
        """Set whether to ignore upstream results"""
        self.immutable = immutable
        return self
    
    def clone(self) -> 'Signature':
        """Clone the current signature"""
        return Signature(
            self.booster, 
            self.args, 
            self.kwargs.copy(), 
            self.immutable
        )
    
    def _build_args(self, prev_result=None) -> tuple:
        """Build actual execution parameters, handling upstream result passing"""
        if prev_result is not None and not self.immutable:
            # Pass upstream result as the first argument
            return (prev_result,) + self.args
        return self.args
    
    def apply(self, prev_result=None) -> FunctionResultStatus:
        """
        Synchronously execute the task and wait for result

        :param prev_result: Upstream task's result (used in chain scenarios)
        :return: FunctionResultStatus containing execution result
        """
        args = self._build_args(prev_result)
        async_result = self.booster.push(*args, **self.kwargs)
        result_status = async_result.wait_rpc_data_or_raise(raise_exception=True)
        
        # After task completes, update workflow_context's current_task_id
        # So when the next task is published, parent_task_id will be the current task's task_id
        _update_workflow_context_after_task(result_status.task_id)
        
        return result_status
    
    def apply_async(self, prev_result=None) -> AsyncResult:
        """
        Asynchronously execute the task, returning AsyncResult

        :param prev_result: Upstream task's result (used in chain scenarios)
        :return: AsyncResult that can be used to wait for the result later
        """
        args = self._build_args(prev_result)
        return self.booster.push(*args, **self.kwargs)
    
    def __repr__(self):
        return f"Signature({self.booster.queue_name}, args={self.args}, kwargs={self.kwargs}, immutable={self.immutable})"
    
    def __or__(self, other):
        """
        Support | operator to create Chain

        Usage: task1.s() | task2.s() | task3.s()
        """
        from .primitives import Chain
        if isinstance(other, Signature):
            return Chain(self, other)
        elif isinstance(other, Chain):
            return Chain(self, *other.tasks)
        else:
            raise TypeError(f"unsupported operand type(s) for |: 'Signature' and '{type(other).__name__}'")


def signature(booster, *args, **kwargs) -> Signature:
    """
    Convenience function: create a task signature
    
    用法：
    ```python
    sig = signature(my_task, 1, 2, name='test')
    ```
    """
    return Signature(booster, args, kwargs)
