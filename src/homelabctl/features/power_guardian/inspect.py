"""Power Guardian state interpretation."""

from __future__ import annotations

from dataclasses import dataclass

from homelabctl.core.models import (
    ModuleActualState,
    Status,
)
from homelabctl.features.power_guardian.config import (
    PowerGuardianConfig,
)


@dataclass(slots=True)
class PowerGuardianAssessment:
    status: Status
    ac_online: bool | None
    battery_percent: int | None
    level: str
    proposed_action: str


def assess(
    actual: ModuleActualState | None,
    config: PowerGuardianConfig,
) -> PowerGuardianAssessment:
    config.validate()

    if actual is None:
        return PowerGuardianAssessment(
            status=Status.UNKNOWN,
            ac_online=None,
            battery_percent=None,
            level="unknown",
            proposed_action="none",
        )

    ac_online = actual.get(
        "ac_online"
    )

    capacity = actual.get(
        "battery_capacity"
    )

    if not isinstance(capacity, int):
        capacity = None

    if ac_online is True:
        return PowerGuardianAssessment(
            status=Status.PASS,
            ac_online=True,
            battery_percent=capacity,
            level="ac",
            proposed_action="none",
        )

    if capacity is None:
        return PowerGuardianAssessment(
            status=Status.UNKNOWN,
            ac_online=ac_online,
            battery_percent=None,
            level="unknown",
            proposed_action="none",
        )

    if capacity <= config.critical_percent:
        return PowerGuardianAssessment(
            status=Status.WARNING,
            ac_online=False,
            battery_percent=capacity,
            level="critical",
            proposed_action=(
                "shutdown_rtc"
                if config.shutdown_on_critical
                else "none"
            ),
        )

    if capacity <= config.low_percent:
        return PowerGuardianAssessment(
            status=Status.WARNING,
            ac_online=False,
            battery_percent=capacity,
            level="low",
            proposed_action=(
                "suspend_cycle"
                if config.suspend_on_low
                else "none"
            ),
        )

    if capacity <= config.warning_percent:
        return PowerGuardianAssessment(
            status=Status.WARNING,
            ac_online=False,
            battery_percent=capacity,
            level="warning",
            proposed_action="none",
        )

    return PowerGuardianAssessment(
        status=Status.PASS,
        ac_online=False,
        battery_percent=capacity,
        level="battery",
        proposed_action="none",
    )
