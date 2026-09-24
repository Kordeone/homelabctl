"""Automatic AC/battery power-profile state."""

from __future__ import annotations

from dataclasses import dataclass

from homelabctl.core.models import (
    ModuleActualState,
    Status,
)


@dataclass(slots=True)
class PowerProfilePolicy:
    ac_profile: str = "balanced"
    battery_profile: str = "power-saver"

    def validate(self) -> None:
        allowed = {
            "power-saver",
            "balanced",
            "performance",
        }

        if self.ac_profile not in allowed:
            raise ValueError(
                f"Invalid AC profile: {self.ac_profile}"
            )

        if self.battery_profile not in allowed:
            raise ValueError(
                f"Invalid battery profile: "
                f"{self.battery_profile}"
            )


@dataclass(slots=True)
class PowerProfileAssessment:
    status: Status
    current_profile: str | None
    ac_online: bool | None
    expected_profile: str | None


def assess(
    actual: ModuleActualState | None,
    policy: PowerProfilePolicy,
) -> PowerProfileAssessment:
    policy.validate()

    if actual is None:
        return PowerProfileAssessment(
            status=Status.UNKNOWN,
            current_profile=None,
            ac_online=None,
            expected_profile=None,
        )

    current = actual.get(
        "power_profile"
    )

    ac_online = actual.get(
        "ac_online"
    )

    if ac_online is True:
        expected = policy.ac_profile
    elif ac_online is False:
        expected = policy.battery_profile
    else:
        expected = None

    if expected is None:
        status = Status.UNKNOWN
    elif current == expected:
        status = Status.PASS
    else:
        status = Status.DRIFT

    return PowerProfileAssessment(
        status=status,
        current_profile=current,
        ac_online=ac_online,
        expected_profile=expected,
    )
