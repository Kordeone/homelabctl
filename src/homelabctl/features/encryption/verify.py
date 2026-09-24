"""Encryption verification."""

from __future__ import annotations

from homelabctl.core.models import (
    ModuleActualState,
    Status,
    VerificationCheck,
    VerificationReport,
)


def verify_luks(
    actual: ModuleActualState | None,
) -> VerificationReport:
    if actual is None:
        return VerificationReport(
            feature="encryption",
            status=Status.ERROR,
            checks=[
                VerificationCheck(
                    key="encryption_state",
                    expected="available",
                    actual=None,
                    passed=False,
                    message=(
                        "Encryption state has not "
                        "been collected."
                    ),
                )
            ],
        )

    luks_present = actual.get(
        "luks_present",
        False,
    )

    cryptsetup_available = actual.get(
        "cryptsetup_available",
        False,
    )

    checks = [
        VerificationCheck(
            key="luks_present",
            expected=True,
            actual=luks_present,
            passed=(luks_present is True),
            message=(
                "LUKS encryption detected."
                if luks_present is True
                else "LUKS encryption was not detected."
            ),
        ),
        VerificationCheck(
            key="cryptsetup_available",
            expected=True,
            actual=cryptsetup_available,
            passed=(
                cryptsetup_available is True
            ),
            message=(
                "cryptsetup is available."
                if cryptsetup_available is True
                else "cryptsetup is unavailable."
            ),
        ),
    ]

    status = (
        Status.PASS
        if all(
            check.passed
            for check in checks
        )
        else Status.WARNING
    )

    return VerificationReport(
        feature="encryption",
        status=status,
        checks=checks,
    )
