"""Entry point for Celery Canvas complex orchestration examples.

Provides the following exports:
- app: Celery application instance
- FLOWS: Mapping of runnable orchestration flow names to functions
- run_flow_by_name: Run a specific orchestration flow by name
"""

from .celery_app import app
from .flows import FLOWS, run_flow_by_name

__all__ = ["app", "FLOWS", "run_flow_by_name"]


