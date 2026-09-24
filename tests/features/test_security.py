from homelabctl.core.models import (
    ModuleActualState,
    StateValue,
    Status,
)
from homelabctl.features.security.inspect import (
    assess,
)


def test_security_assessment_pass():
    actual = ModuleActualState(
        module="security",
        collected_at="test",
        values={
            "secure_boot": StateValue(
                key="secure_boot",
                value=True,
            ),
            "kernel_lockdown": StateValue(
                key="kernel_lockdown",
                value="integrity",
            ),
            "tpm_present": StateValue(
                key="tpm_present",
                value=True,
            ),
        },
    )

    result = assess(actual)

    assert result.status == Status.PASS
    assert result.secure_boot is True
    assert result.tpm_present is True
