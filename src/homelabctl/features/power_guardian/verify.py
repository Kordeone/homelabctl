"""Power Guardian verification."""

from __future__ import annotations

from homelabctl.core.models import (
    Status,
    VerificationCheck,
    VerificationReport,
)
from homelabctl.system.systemd import (
    unit_active_state,
    unit_enabled_state,
    unit_exists,
)


def verify() -> VerificationReport:
    exists = unit_exists(
        "homelab-power-guardian.timer"
    )

    active = (
        unit_active_state(
            "homelab-power-guardian.timer"
        )
        if exists
        else "not-found"
    )

    enabled = (
        unit_enabled_state(
            "homelab-power-guardian.timer"
        )
        if exists
        else "not-found"
    )

    checks = [
        VerificationCheck(
            key="timer_exists",
            expected=True,
            actual=exists,
            passed=exists,
            message=(
                "Power Guardian timer exists."
                if exists
                else "Power Guardian timer is missing."
            ),
        ),
        VerificationCheck(
            key="timer_active",
            expected="active",
            actual=active,
            passed=(active == "active"),
            message=(
                "Power Guardian timer is active."
                if active == "active"
                else "Power Guardian timer is not active."
            ),
        ),
        VerificationCheck(
            key="timer_enabled",
            expected="enabled",
            actual=enabled,
            passed=(enabled == "enabled"),
            message=(
                "Power Guardian timer is enabled."
                if enabled == "enabled"
                else "Power Guardian timer is not enabled."
            ),
        ),
    ]

    return VerificationReport(
        feature="power_guardian",
        status=(
            Status.PASS
            if all(
                check.passed
                for check in checks
            )
            else Status.FAIL
        ),
        checks=checks,
    )
