# -*- coding: utf-8 -*-
"""
Funboost Workflow - Publisher/Consumer Mixin

Provides WorkflowPublisherMixin and WorkflowConsumerMixin
for injecting and extracting workflow context in messages, enabling cross-task context passing.

Usage:
1. Use the pre-configured WorkflowBoosterParams directly (recommended)
2. Or manually specify consumer_override_cls and publisher_override_cls
"""

import copy
import typing
import contextvars

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer

# Use contextvars for unified context management, supporting both multi-threading and async coroutine scenarios
# Refer to funboost/core/current_task.py implementation
_workflow_context_var: contextvars.ContextVar[typing.Optional[dict]] = contextvars.ContextVar(
    'workflow_context', default=None
)


class WorkflowPublisherMixin(AbstractPublisher):
    """
    Workflow Publisher Mixin

    Features:
    1. When publishing messages, checks if there is workflow information in the current context
    2. If so, injects the workflow context into the message's extra field
    3. Supports trace tracking: can trace which upstream task triggered a task

    Workflow context in messages contains:
    - workflow_id: Unique workflow identifier
    - parent_task_id: Parent task ID (who triggered this task)
    - chain_depth: Chain depth (for debugging)

    Note: current_task_id is only used in runtime contextvars, not stored in messages.
    A task's own ID is obtained via extra.task_id.
    """
    
    @classmethod
    def set_workflow_context(cls, workflow_ctx: dict):
        """Set the workflow context for the current thread/coroutine"""
        _workflow_context_var.set(workflow_ctx)
    
    @classmethod
    def get_workflow_context(cls) -> typing.Optional[dict]:
        """Get the workflow context for the current thread/coroutine"""
        return _workflow_context_var.get()
    
    @classmethod
    def clear_workflow_context(cls):
        """Clear the workflow context for the current thread/coroutine"""
        _workflow_context_var.set(None)
    
    def _get_workflow_context_from_msg_or_contextvars(self, msg: dict) -> typing.Optional[dict]:
        """
        Get workflow context, preferring from message (aio_publish scenario), otherwise from contextvars

        This solves the issue of contextvars being lost when aio_publish uses run_in_executor across threads:
        1. aio_publish first gets workflow_context from contextvars in the asyncio thread
        2. Injects it into the message's extra._workflow_context_from_aio
        3. When publish executes in the executor thread, it preferentially recovers context from the message
        """
        # Prefer from message (cross-thread passing in aio_publish scenario)
        aio_ctx = msg.get('extra', {}).get('_workflow_context_from_aio')
        if aio_ctx:
            return aio_ctx
        # Otherwise get from contextvars (synchronous call scenario)
        return self.get_workflow_context()
    
    def _inject_workflow_context_to_msg(self, msg: dict):
        """
        Inject the workflow context from current contextvars into the message
        Used in aio_publish scenario: capture context in asyncio thread first, then pass to executor thread via message
        """
        workflow_ctx = self.get_workflow_context()
        if workflow_ctx:
            if 'extra' not in msg:
                msg['extra'] = {}
            # Use a special key, different from the final injected workflow_context
            msg['extra']['_workflow_context_from_aio'] = workflow_ctx
    
    def publish(self, msg, task_id=None, task_options=None):
        """
        Publish message, injecting workflow context
        """
        msg = copy.deepcopy(msg)  # Prevent modifying the user's original dictionary

        # Get current workflow context (prefer from message, solving aio_publish cross-thread issue)
        workflow_ctx = self._get_workflow_context_from_msg_or_contextvars(msg)
        
        if workflow_ctx:
            if 'extra' not in msg:
                msg['extra'] = {}
            
            # Create context in message (only necessary fields, without current_task_id)
            msg_ctx = {
                'workflow_id': workflow_ctx.get('workflow_id'),
                'parent_task_id': workflow_ctx.get('current_task_id'),  # Parent task = currently executing task
                'chain_depth': workflow_ctx.get('chain_depth', 0) + 1,
            }
            
            msg['extra']['workflow_context'] = msg_ctx
            
            # Clean up temporary fields
            msg['extra'].pop('_workflow_context_from_aio', None)
        
        return super().publish(msg, task_id, task_options)
    
    async def aio_publish(self, msg, task_id=None, task_options=None):
        """
        Publish message in asyncio ecosystem, handling cross-thread workflow context passing

        Key issue: The parent's aio_publish uses run_in_executor to execute publish in a thread pool,
        but contextvars are not automatically passed across threads.

        Solution:
        1. Get workflow_context in the current asyncio thread first
        2. Inject it into the message's extra._workflow_context_from_aio
        3. Then call the parent's aio_publish (which executes publish in the executor thread)
        4. The publish method detects _workflow_context_from_aio and uses it as the context
        """
        msg = copy.deepcopy(msg)  # Prevent modifying the user's original dictionary

        # Capture workflow context in the current asyncio thread and inject into the message
        # So when publish executes in the executor thread, it can recover the correct context from the message
        self._inject_workflow_context_to_msg(msg)
        
        # Call parent's aio_publish, which will call self.publish in the executor
        # The publish method will detect msg['extra']['_workflow_context_from_aio'] and use it
        return await super().aio_publish(msg, task_id, task_options)


class WorkflowConsumerMixin(AbstractConsumer):
    """
    Workflow Consumer Mixin

    Features:
    1. Before executing a task, extracts workflow context from the message
    2. Saves context to contextvars so child tasks can inherit it (supports both multi-threading and async coroutines)
    3. Cleans up context after execution

    This way, when the consumer function internally calls other_task.push(),
    WorkflowPublisherMixin can get the context from contextvars and inject it into the child task's message.
    """
    
    def _extract_workflow_context(self, kw: dict) -> typing.Optional[dict]:
        """Extract workflow context from the message"""
        return kw['body'].get('extra', {}).get('workflow_context')
    
    def _run(self, kw: dict):
        """
        Synchronous consumer function execution, injecting workflow context
        """
        # 1. Extract workflow context
        msg_ctx = self._extract_workflow_context(kw)
        
        if msg_ctx:
            # Build runtime context (add current_task_id, used to set parent_task_id when publishing child tasks)
            runtime_ctx = {
                'workflow_id': msg_ctx.get('workflow_id'),
                'parent_task_id': msg_ctx.get('parent_task_id'),
                'chain_depth': msg_ctx.get('chain_depth', 0),
                'current_task_id': kw['body']['extra'].get('task_id'),  # Current task's own ID
            }

            # Save to contextvars (supports both multi-threading and asyncio)
            WorkflowPublisherMixin.set_workflow_context(runtime_ctx)
        
        try:
            return super()._run(kw)
        finally:
            # Clean up context
            WorkflowPublisherMixin.clear_workflow_context()
    
    async def _async_run(self, kw: dict):
        """
        Asynchronous consumer function execution, injecting workflow context
        """
        # 1. Extract workflow context
        msg_ctx = self._extract_workflow_context(kw)
        
        if msg_ctx:
            # Build runtime context (add current_task_id, used to set parent_task_id when publishing child tasks)
            runtime_ctx = {
                'workflow_id': msg_ctx.get('workflow_id'),
                'parent_task_id': msg_ctx.get('parent_task_id'),
                'chain_depth': msg_ctx.get('chain_depth', 0),
                'current_task_id': kw['body']['extra'].get('task_id'),  # Current task's own ID
            }

            # Save to contextvars (automatically supports asyncio coroutine isolation)
            WorkflowPublisherMixin.set_workflow_context(runtime_ctx)
        
        try:
            return await super()._async_run(kw)
        finally:
            # Clean up context
            WorkflowPublisherMixin.clear_workflow_context()


def get_current_workflow_context() -> typing.Optional[dict]:
    """
    Get the current workflow context (for use in user code)
    
    用法：
    ```python
    from funboost.workflow import get_current_workflow_context
    
    @boost(WorkflowBoosterParams(queue_name='my_task'))
    def my_task(x):
        ctx = get_current_workflow_context()
        if ctx:
            print(f"Workflow ID: {ctx.get('workflow_id')}")
            print(f"Parent Task: {ctx.get('parent_task_id')}")
    ```
    """
    return WorkflowPublisherMixin.get_workflow_context()
