from homelabctl.core.models import (
    ChangeKind,
    RiskLevel,
)
from homelabctl.core.planner import (
    build_plan,
    make_step,
)


def test_plan_detects_root_requirement():
    step = make_step(
        step_id="test",
        description="Test step",
        kind=ChangeKind.MODIFY_FILE,
        requires_root=True,
    )

    plan = build_plan(
        feature="test",
        title="Test Plan",
        summary="Test",
        risk=RiskLevel.LOW,
        steps=[step],
    )

    assert plan.requires_root is True
    assert plan.empty is False


def test_empty_plan():
    plan = build_plan(
        feature="test",
        title="Empty",
        summary="Nothing",
        risk=RiskLevel.LOW,
        steps=[],
    )

    assert plan.empty is True
