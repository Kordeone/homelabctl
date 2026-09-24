"""Verification of the selected security baseline."""

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
            feature="security",
            status=Status.ERROR,
            checks=[
                VerificationCheck(
                    key="security_state",
                    expected="available",
                    actual=None,
                    passed=False,
                    message=(
                        "Security state has not "
                        "been collected."
                    ),
                )
            ],
        )

    secure_boot = actual.get(
        "secure_boot"
    )

    lockdown = actual.get(
        "kernel_lockdown"
    )

    tpm_present = actual.get(
        "tpm_present"
    )

    checks = [
        VerificationCheck(
            key="secure_boot",
            expected=True,
            actual=secure_boot,
            passed=(
                secure_boot is True
            ),
            message=(
                "Secure Boot enabled."
                if secure_boot is True
                else "Secure Boot is not enabled or could not be verified."
            ),
        ),
        VerificationCheck(
            key="kernel_lockdown",
            expected=(
                "integrity or confidentiality"
            ),
            actual=lockdown,
            passed=(
                lockdown
                in {
                    "integrity",
                    "confidentiality",
                }
            ),
            message=(
                "Kernel lockdown is active."
                if lockdown
                in {
                    "integrity",
                    "confidentiality",
                }
                else (
                    "Kernel lockdown is not active "
                    "or could not be verified."
                )
            ),
        ),
        VerificationCheck(
            key="tpm_present",
            expected=True,
            actual=tpm_present,
            passed=(
                tpm_present is True
            ),
            message=(
                "TPM detected."
                if tpm_present is True
                else "TPM was not detected."
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
        feature="security",
        status=status,
        checks=checks,
    )
