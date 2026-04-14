# -*- coding: utf-8 -*-
"""
Funboost Workflow - Declarative Task Orchestration Module

Provides a declarative task orchestration API similar to Celery Canvas, allowing users to define workflows with concise syntax.

Core concepts:
- Signature: Task signature, representing a pending task and its parameters
- Chain: Sequential execution, executes multiple tasks in order, upstream results automatically passed to downstream
- Group: Parallel execution, executes multiple tasks simultaneously, collects all results
- Chord: Parallel + aggregation, header executes in parallel, result list passed to body

Usage example:
```python
from funboost.workflow import chain, group, chord, WorkflowBoosterParams

@boost(WorkflowBoosterParams(queue_name='my_task'))
def my_task(x):
    return x * 2

# Define workflow
workflow = chain(
    task1.s(input_data),
    group(task2.s(), task3.s()),
    task4.s()
)

# Execute
result = workflow.apply()
```

See funboost/workflow/examples/ for detailed documentation.
"""

from .signature import Signature, signature
from .primitives import Chain, Group, Chord, chain, group, chord
from .workflow_mixin import WorkflowPublisherMixin, WorkflowConsumerMixin
from .params import WorkflowBoosterParams


# ============================================================
# Monkey patch: Add .s() and .si() methods to the Booster class
# This way all @boost decorated consumer functions automatically have signature creation methods
# ============================================================

def _patch_booster_with_signature_methods():
    """
    Patch the Booster class to add .s() and .si() methods

    This way users don't need to manually add .s() method for each booster:

    Before (manual addition required):
        download_video.s = lambda *args, **kw: Signature(download_video, args, kw)

    After (automatically available):
        sig = download_video.s(url)  # Directly usable
    """
    from funboost.core.booster import Booster
    
    def s(self, *args, **kwargs) -> Signature:
        """
        Create a task signature (similar to Celery's .s() method)

        Usage:
            sig = my_task.s(1, 2, name='test')
            workflow = chain(task1.s(), task2.s())
        """
        return Signature(self, args, kwargs, immutable=False)
    
    def si(self, *args, **kwargs) -> Signature:
        """
        Create an immutable task signature (ignores upstream results)

        When used in a chain, the upstream task's result will not be passed as the first argument.

        Usage:
            sig = my_task.si(1, 2)  # Ignores upstream results
        """
        return Signature(self, args, kwargs, immutable=True)
    
    # Apply patches
    Booster.s = s
    Booster.si = si


# Automatically apply patches on module import
_patch_booster_with_signature_methods()


__all__ = [
    # Signature
    'Signature',
    'signature',
    
    # Primitives
    'Chain',
    'Group', 
    'Chord',
    'chain',
    'group',
    'chord',
    
    # Mixin
    'WorkflowPublisherMixin',
    'WorkflowConsumerMixin',
    
    # Params
    'WorkflowBoosterParams',
]
