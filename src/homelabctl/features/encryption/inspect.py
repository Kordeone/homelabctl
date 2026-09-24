"""Encryption-state assessment."""

from __future__ import annotations

from dataclasses import dataclass, field

from homelabctl.core.models import (
    ModuleActualState,
    Status,
)
from homelabctl.features.encryption.capabilities import (
    detect_capabilities,
)


@dataclass(slots=True)
class EncryptionAssessment:
    status: Status
    luks_present: bool
    luks_device_count: int
    cryptsetup_available: bool
    clevis_available: bool
    luks_devices: list[dict]
    messages: list[str] = field(
        default_factory=list
    )


def assess(
    actual: ModuleActualState | None,
) -> EncryptionAssessment:
    if actual is None:
        return EncryptionAssessment(
            status=Status.UNKNOWN,
            luks_present=False,
            luks_device_count=0,
            cryptsetup_available=False,
            clevis_available=False,
            luks_devices=[],
            messages=[
                "Encryption state has not been collected."
            ],
        )

    capabilities = detect_capabilities(
        actual
    )

    devices = actual.get(
        "luks_devices",
        [],
    )

    if not isinstance(devices, list):
        devices = []

    messages: list[str] = []

    if capabilities.luks_present:
        messages.append(
            (
                f"{capabilities.luks_device_count} "
                "LUKS device(s) detected."
            )
        )
    else:
        messages.append(
            "No LUKS device was detected."
        )

    if capabilities.cryptsetup_available:
        messages.append(
            "cryptsetup is available."
        )
    else:
        messages.append(
            "cryptsetup is not available."
        )

    if capabilities.clevis_available:
        messages.append(
            "Clevis is available."
        )
    else:
        messages.append(
            "Clevis is not available."
        )

    status = (
        Status.PASS
        if capabilities.luks_present
        and capabilities.cryptsetup_available
        else Status.WARNING
    )

    return EncryptionAssessment(
        status=status,
        luks_present=capabilities.luks_present,
        luks_device_count=(
            capabilities.luks_device_count
        ),
        cryptsetup_available=(
            capabilities.cryptsetup_available
        ),
        clevis_available=(
            capabilities.clevis_available
        ),
        luks_devices=devices,
        messages=messages,
    )
