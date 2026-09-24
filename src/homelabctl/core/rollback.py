"""Rollback metadata helpers."""

from __future__ import annotations

from homelabctl.core.models import (
    ChangePlan,
    RollbackAction,
    RollbackPlan,
)


def build_rollback_plan(
    plan: ChangePlan,
    actions: list[RollbackAction],
) -> RollbackPlan:
    """Create rollback metadata for a change plan."""

    irreversible = [
        step
        for step in plan.steps
        if not step.reversible
    ]

    if irreversible:
        names = ", ".join(step.id for step in irreversible)

        return RollbackPlan(
            source_plan_id=plan.id,
            available=False,
            actions=actions,
            reason_unavailable=(
                "One or more plan steps are marked irreversible: "
                f"{names}"
            ),
        )

    return RollbackPlan(
        source_plan_id=plan.id,
        available=True,
        actions=actions,
    )


def unavailable_rollback(
    plan: ChangePlan,
    reason: str,
) -> RollbackPlan:
    return RollbackPlan(
        source_plan_id=plan.id,
        available=False,
        reason_unavailable=reason,
    )
