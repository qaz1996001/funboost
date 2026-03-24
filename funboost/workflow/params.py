# -*- coding: utf-8 -*-
"""
Funboost Workflow - Pre-configured BoosterParams

Provides WorkflowBoosterParams with pre-configured settings required for workflow orchestration:
1. Enables RPC mode (workflow orchestration depends on RPC to get results)
2. Injects WorkflowPublisherMixin and WorkflowConsumerMixin

Usage:
```python
from funboost import boost
from funboost.workflow import WorkflowBoosterParams

@boost(WorkflowBoosterParams(queue_name='my_task'))
def my_task(x):
    return x * 2
```
"""

import typing
from funboost.core.func_params_model import BoosterParams
from .workflow_mixin import WorkflowPublisherMixin, WorkflowConsumerMixin


class WorkflowBoosterParams(BoosterParams):
    """
    BoosterParams pre-configured with workflow orchestration support

    Features:
    1. is_using_rpc_mode=True: Enables RPC mode for retrieving task execution results
    2. consumer_override_cls: WorkflowConsumerMixin, extracts workflow context
    3. publisher_override_cls: WorkflowPublisherMixin, injects workflow context

    Use cases:
    - Tasks that need chain/group/chord orchestration
    - Scenarios that require passing context between tasks

    Example:
    ```python
    @boost(WorkflowBoosterParams(queue_name='download_task'))
    def download(url):
        # ...
        return file_path

    @boost(WorkflowBoosterParams(queue_name='process_task'))
    def process(file_path):
        # ...
        return result

    # Workflow orchestration
    workflow = chain(download.s(url), process.s())
    result = workflow.apply()
    ```
    """

    # Enable RPC mode - workflow orchestration needs to retrieve task results
    is_using_rpc_mode: bool = True

    # Inject Mixins
    consumer_override_cls: typing.Type[WorkflowConsumerMixin] = WorkflowConsumerMixin
    publisher_override_cls: typing.Type[WorkflowPublisherMixin] = WorkflowPublisherMixin
