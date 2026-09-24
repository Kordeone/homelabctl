import pytest

from homelabctl.core.models import (
    ModuleActualState,
    StateValue,
    Status,
)
from homelabctl.features.power_guardian.config import (
    PowerGuardianConfig,
)
from homelabctl.features.power_guardian.inspect import (
    assess as assess_guardian,
)
from homelabctl.features.power_profile.inspect import (
    PowerProfilePolicy,
    assess as assess_profile,
)


def test_power_profile_on_ac():
    actual = ModuleActualState(
        module="power",
        collected_at="test",
        values={
            "ac_online": StateValue(
                key="ac_online",
                value=True,
            ),
            "power_profile": StateValue(
                key="power_profile",
                value="balanced",
            ),
        },
    )

    result = assess_profile(
        actual,
        PowerProfilePolicy(),
    )

    assert result.status == Status.PASS
    assert result.expected_profile == "balanced"


def test_guardian_critical_battery():
    actual = ModuleActualState(
        module="power",
        collected_at="test",
        values={
            "ac_online": StateValue(
                key="ac_online",
                value=False,
            ),
            "battery_capacity": StateValue(
                key="battery_capacity",
                value=10,
            ),
        },
    )

    result = assess_guardian(
        actual,
        PowerGuardianConfig(),
    )

    assert result.level == "critical"
    assert result.proposed_action == "shutdown_rtc"


def test_invalid_guardian_thresholds():
    config = PowerGuardianConfig(
        warning_percent=20,
        low_percent=30,
        critical_percent=10,
    )

    with pytest.raises(ValueError):
        config.validate()
