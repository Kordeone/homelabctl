from homelabctl.core.models import (
    ChangeKind,
    RiskLevel,
    RollbackAction,
)
from homelabctl.core.planner import (
    build_plan,
    make_step,
)
from homelabctl.core.rollback import (
    build_rollback_plan,
)


def test_reversible_plan_has_rollback():
    plan = build_plan(
        feature="test",
        title="Test",
        summary="Test",
        risk=RiskLevel.LOW,
        steps=[
            make_step(
                step_id="file",
                description="Change file",
                kind=ChangeKind.MODIFY_FILE,
                reversible=True,
            )
        ],
    )

    rollback = build_rollback_plan(
        plan,
        [
            RollbackAction(
                description="Restore file"
            )
        ],
    )

    assert rollback.available is True


def test_irreversible_step_disables_full_rollback():
    plan = build_plan(
        feature="test",
        title="Test",
        summary="Test",
        risk=RiskLevel.HIGH,
        steps=[
            make_step(
                step_id="danger",
                description="Danger",
                kind=ChangeKind.OTHER,
                reversible=False,
            )
        ],
    )

    rollback = build_rollback_plan(
        plan,
        [],
    )

    assert rollback.available is False
