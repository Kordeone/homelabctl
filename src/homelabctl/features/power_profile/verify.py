"""Automatic power-profile verification."""

from __future__ import annotations

from homelabctl.core.models import (
    ModuleActualState,
    Status,
    VerificationCheck,
    VerificationReport,
)
from homelabctl.features.power_profile.inspect import (
    PowerProfilePolicy,
)


def verify(
    actual: ModuleActualState | None,
    policy: PowerProfilePolicy,
) -> VerificationReport:
    policy.validate()

    if actual is None:
        return VerificationReport(
            feature="power_profile",
            status=Status.ERROR,
            checks=[
                VerificationCheck(
                    key="power_state",
                    expected="available",
                    actual=None,
                    passed=False,
                    message=(
                        "Power state has not "
                        "been collected."
                    ),
                )
            ],
        )

    ac_online = actual.get(
        "ac_online"
    )

    current = actual.get(
        "power_profile"
    )

    if ac_online is True:
        expected = policy.ac_profile
    elif ac_online is False:
        expected = policy.battery_profile
    else:
        expected = None

    passed = (
        expected is not None
        and current == expected
    )

    return VerificationReport(
        feature="power_profile",
        status=(
            Status.PASS
            if passed
            else Status.FAIL
        ),
        checks=[
            VerificationCheck(
                key="power_profile",
                expected=expected,
                actual=current,
                passed=passed,
                message=(
                    "Power profile matches "
                    "current AC state."
                    if passed
                    else (
                        "Power profile does not "
                        "match current AC state."
                    )
                ),
            )
        ],
    )
