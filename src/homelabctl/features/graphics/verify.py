"""Graphics configuration verification."""

from __future__ import annotations

from homelabctl.core.models import (
    ModuleActualState,
    Status,
    VerificationCheck,
    VerificationReport,
)


def verify(
    actual: ModuleActualState | None,
) -> VerificationReport:
    if actual is None:
        return VerificationReport(
            feature="graphics",
            status=Status.ERROR,
            checks=[
                VerificationCheck(
                    key="graphics_state",
                    expected="available",
                    actual=None,
                    passed=False,
                    message=(
                        "Graphics state has not "
                        "been collected."
                    ),
                )
            ],
        )

    nouveau_loaded = actual.get(
        "nouveau_loaded"
    )

    nouveau_blacklisted = actual.get(
        "nouveau_blacklisted"
    )

    checks = [
        VerificationCheck(
            key="nouveau_blacklisted",
            expected=True,
            actual=nouveau_blacklisted,
            passed=(
                nouveau_blacklisted is True
            ),
            message=(
                "Nouveau is blacklisted."
                if nouveau_blacklisted is True
                else "Nouveau blacklist not detected."
            ),
        ),
        VerificationCheck(
            key="nouveau_loaded",
            expected=False,
            actual=nouveau_loaded,
            passed=(
                nouveau_loaded is False
            ),
            message=(
                "Nouveau is not loaded."
                if nouveau_loaded is False
                else (
                    "Nouveau is currently loaded; "
                    "a reboot may be required."
                )
            ),
        ),
    ]

    return VerificationReport(
        feature="graphics",
        status=(
            Status.PASS
            if all(
                check.passed
                for check in checks
            )
            else Status.WARNING
        ),
        checks=checks,
    )
