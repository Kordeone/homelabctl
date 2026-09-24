from homelabctl.core.drift import compare_module_state
from homelabctl.core.models import (
    DesiredSetting,
    ModuleActualState,
    ModuleDesiredState,
    StateValue,
    Status,
)


def test_matching_state_passes():
    desired = ModuleDesiredState(
        module="ssh",
        settings={
            "permit_root_login": DesiredSetting(
                key="permit_root_login",
                value="no",
            )
        },
    )

    actual = ModuleActualState(
        module="ssh",
        collected_at="test",
        values={
            "permit_root_login": StateValue(
                key="permit_root_login",
                value="no",
            )
        },
    )

    report = compare_module_state(
        desired,
        actual,
    )

    assert report.status == Status.PASS
    assert report.drift_count == 0


def test_different_state_reports_drift():
    desired = ModuleDesiredState(
        module="ssh",
        settings={
            "permit_root_login": DesiredSetting(
                key="permit_root_login",
                value="no",
            )
        },
    )

    actual = ModuleActualState(
        module="ssh",
        collected_at="test",
        values={
            "permit_root_login": StateValue(
                key="permit_root_login",
                value="yes",
            )
        },
    )

    report = compare_module_state(
        desired,
        actual,
    )

    assert report.status == Status.DRIFT
    assert report.drift_count == 1
