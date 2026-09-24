from homelabctl.core.models import (
    DesiredSetting,
    ModuleActualState,
    ModuleDesiredState,
    StateValue,
    Status,
)
from homelabctl.core.verifier import verify_module


def test_verification_passes():
    desired = ModuleDesiredState(
        module="test",
        settings={
            "enabled": DesiredSetting(
                key="enabled",
                value=True,
            )
        },
    )

    actual = ModuleActualState(
        module="test",
        collected_at="test",
        values={
            "enabled": StateValue(
                key="enabled",
                value=True,
            )
        },
    )

    result = verify_module(
        desired,
        actual,
    )

    assert result.status == Status.PASS
    assert result.passed is True


def test_verification_fails():
    desired = ModuleDesiredState(
        module="test",
        settings={
            "enabled": DesiredSetting(
                key="enabled",
                value=True,
            )
        },
    )

    actual = ModuleActualState(
        module="test",
        collected_at="test",
        values={
            "enabled": StateValue(
                key="enabled",
                value=False,
            )
        },
    )

    result = verify_module(
        desired,
        actual,
    )

    assert result.status == Status.FAIL
