"""Security-state assessment."""

from __future__ import annotations

from dataclasses import dataclass, field

from homelabctl.core.models import (
    ModuleActualState,
    Status,
)
from homelabctl.features.security.capabilities import (
    SecurityCapabilities,
    detect_capabilities,
)


@dataclass(slots=True)
class SecurityAssessment:
    status: Status

    secure_boot: bool | None
    kernel_lockdown: str | None
    tpm_present: bool

    messages: list[str] = field(
        default_factory=list
    )


def assess(
    actual: ModuleActualState | None,
) -> SecurityAssessment:
    capabilities = detect_capabilities(
        actual
    )

    messages: list[str] = []

    if actual is None:
        return SecurityAssessment(
            status=Status.UNKNOWN,
            secure_boot=None,
            kernel_lockdown=None,
            tpm_present=False,
            messages=[
                (
                    "Security state has not "
                    "been collected."
                )
            ],
        )

    if (
        capabilities.secure_boot_known
        and capabilities.secure_boot_enabled
    ):
        messages.append(
            "Secure Boot is enabled."
        )

    elif (
        capabilities.secure_boot_known
        and not capabilities.secure_boot_enabled
    ):
        messages.append(
            "Secure Boot is disabled."
        )

    else:
        messages.append(
            "Secure Boot state is unknown."
        )

    if capabilities.lockdown_active:
        messages.append(
            (
                "Kernel lockdown is active "
                f"in {capabilities.kernel_lockdown_mode} "
                "mode."
            )
        )

    elif capabilities.kernel_lockdown_known:
        messages.append(
            (
                "Kernel lockdown mode is "
                f"{capabilities.kernel_lockdown_mode}."
            )
        )

    else:
        messages.append(
            "Kernel lockdown state is unknown."
        )

    if capabilities.tpm_present:
        messages.append(
            "TPM device is available."
        )
    else:
        messages.append(
            "TPM device was not detected."
        )

    status = _overall_status(
        capabilities
    )

    return SecurityAssessment(
        status=status,
        secure_boot=(
            capabilities.secure_boot_enabled
        ),
        kernel_lockdown=(
            capabilities.kernel_lockdown_mode
        ),
        tpm_present=(
            capabilities.tpm_present
        ),
        messages=messages,
    )


def _overall_status(
    capabilities: SecurityCapabilities,
) -> Status:
    if not capabilities.secure_boot_known:
        return Status.WARNING

    if not capabilities.secure_boot_enabled:
        return Status.WARNING

    if not capabilities.kernel_lockdown_known:
        return Status.WARNING

    if not capabilities.tpm_present:
        return Status.WARNING

    return Status.PASS
