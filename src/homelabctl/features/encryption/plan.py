"""Encryption configuration planning.

Initial HomeLabCTL support treats TPM/Clevis enrollment as a sensitive
operation. The application can inspect and explain it, but automatic
enrollment is intentionally not enabled yet.
"""

from __future__ import annotations

from homelabctl.core.models import (
    ChangeKind,
    ModuleActualState,
    RiskLevel,
)
from homelabctl.core.planner import (
    build_plan,
    make_step,
)
from homelabctl.features.encryption.capabilities import (
    detect_capabilities,
)


def build_tpm_enrollment_plan(
    *,
    actual: ModuleActualState | None,
    luks_device: str,
):
    if not luks_device.strip():
        raise ValueError(
            "LUKS device cannot be empty."
        )

    capabilities = detect_capabilities(
        actual
    )

    warnings: list[str] = [
        (
            "TPM enrollment changes LUKS metadata "
            "and must retain an existing recovery "
            "passphrase."
        ),
        (
            "A verified LUKS header backup should "
            "exist before enrollment."
        ),
    ]

    if not capabilities.luks_present:
        warnings.append(
            "No LUKS device is currently detected."
        )

    if not capabilities.cryptsetup_available:
        warnings.append(
            "cryptsetup is not available."
        )

    if not capabilities.clevis_available:
        warnings.append(
            "Clevis is not available."
        )

    return build_plan(
        feature="encryption",
        title="TPM-backed LUKS enrollment",
        summary=(
            "Prepare TPM-backed automatic unlock "
            "for the selected LUKS device."
        ),
        risk=RiskLevel.CRITICAL,
        steps=[
            make_step(
                step_id="verify-luks-device",
                description=(
                    "Verify the selected block device "
                    "is a valid LUKS container."
                ),
                kind=ChangeKind.RUN_COMMAND,
                target=luks_device,
                requires_root=True,
                reversible=True,
                command_preview=(
                    f"cryptsetup luksDump {luks_device}"
                ),
            ),
            make_step(
                step_id="backup-luks-header",
                description=(
                    "Create a verified backup of the "
                    "LUKS header before enrollment."
                ),
                kind=ChangeKind.MANUAL_ACTION,
                target=luks_device,
                requires_root=True,
                reversible=True,
            ),
            make_step(
                step_id="enroll-tpm",
                description=(
                    "Enroll a TPM-backed unlock method."
                ),
                kind=ChangeKind.MANUAL_ACTION,
                target=luks_device,
                requires_root=True,
                reversible=False,
            ),
        ],
        warnings=warnings,
        requires_reboot=True,
    )
