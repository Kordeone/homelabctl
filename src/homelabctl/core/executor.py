"""Execution interfaces.

The persistent backend must never use this module to mutate the system.

Actual privileged changes will be implemented later under
``homelabctl.apply`` and invoked only by an explicit foreground user action.
"""

from __future__ import annotations

from typing import Protocol

from homelabctl.core.models import ChangePlan, ExecutionResult


class PlanExecutor(Protocol):
    """Interface implemented by foreground apply executors."""

    def execute(self, plan: ChangePlan) -> ExecutionResult:
        ...


class DryRunExecutor:
    """Executor that performs no mutation.

    Useful for plan previews, tests, and development.
    """

    def execute(self, plan: ChangePlan) -> ExecutionResult:
        return ExecutionResult(
            plan_id=plan.id,
            success=True,
            message="Dry run only; no system changes were performed.",
            completed_steps=[],
        )
