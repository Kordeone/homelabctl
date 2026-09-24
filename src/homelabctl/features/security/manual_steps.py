"""Manual security operations that HomeLabCTL cannot safely automate."""

from __future__ import annotations

from dataclasses import dataclass

from homelabctl.core.models import ModuleActualState
from homelabctl.features.security.capabilities import (
    detect_capabilities,
)


@dataclass(slots=True)
class ManualStep:
    key: str
    title: str
    description: str
    required: bool
    completed: bool | None = None


def get_manual_steps(
    actual: ModuleActualState | None,
) -> list[ManualStep]:
    capabilities = detect_capabilities(
        actual
    )

    steps: list[ManualStep] = []

    if (
        not capabilities.secure_boot_known
        or not capabilities.secure_boot_enabled
    ):
        steps.append(
            ManualStep(
                key="enable-secure-boot",
                title="Enable Secure Boot",
                description=(
                    "Open the machine UEFI/BIOS "
                    "configuration and enable Secure Boot. "
                    "HomeLabCTL will verify the result "
                    "after the next boot."
                ),
                required=True,
                completed=(
                    capabilities.secure_boot_enabled
                    if capabilities.secure_boot_known
                    else None
                ),
            )
        )

    if not capabilities.tpm_present:
        steps.append(
            ManualStep(
                key="check-tpm",
                title="Check TPM configuration",
                description=(
                    "Inspect UEFI/BIOS security settings "
                    "and confirm that the TPM is enabled. "
                    "HomeLabCTL cannot change firmware "
                    "settings automatically."
                ),
                required=False,
                completed=False,
            )
        )

    return steps
