"""Change-plan construction and validation."""

from __future__ import annotations

from uuid import uuid4

from homelabctl.core.errors import PlanningError
from homelabctl.core.models import (
    ChangeKind,
    ChangePlan,
    PlanStep,
    RiskLevel,
)


def new_plan_id() -> str:
    return uuid4().hex


def build_plan(
    *,
    feature: str,
    title: str,
    summary: str,
    risk: RiskLevel,
    steps: list[PlanStep],
    warnings: list[str] | None = None,
    requires_reboot: bool = False,
) -> ChangePlan:
    if not feature.strip():
        raise PlanningError("Plan feature name cannot be empty.")

    if not title.strip():
        raise PlanningError("Plan title cannot be empty.")

    step_ids = [step.id for step in steps]

    if len(step_ids) != len(set(step_ids)):
        raise PlanningError("Plan step IDs must be unique.")

    requires_root = any(step.requires_root for step in steps)

    return ChangePlan(
        id=new_plan_id(),
        feature=feature,
        title=title,
        summary=summary,
        risk=risk,
        steps=steps,
        warnings=list(warnings or []),
        requires_root=requires_root,
        requires_reboot=requires_reboot,
    )


def make_step(
    *,
    step_id: str,
    description: str,
    kind: ChangeKind,
    target: str | None = None,
    before: object = None,
    after: object = None,
    requires_root: bool = False,
    reversible: bool = True,
    command_preview: str | None = None,
) -> PlanStep:
    if not step_id.strip():
        raise PlanningError("Plan step ID cannot be empty.")

    if not description.strip():
        raise PlanningError("Plan step description cannot be empty.")

    return PlanStep(
        id=step_id,
        description=description,
        kind=kind,
        target=target,
        before=before,
        after=after,
        requires_root=requires_root,
        reversible=reversible,
        command_preview=command_preview,
    )
