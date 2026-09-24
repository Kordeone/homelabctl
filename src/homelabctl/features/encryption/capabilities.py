"""Encryption capability interpretation."""

from __future__ import annotations

from dataclasses import dataclass

from homelabctl.core.models import ModuleActualState


@dataclass(slots=True)
class EncryptionCapabilities:
    luks_present: bool
    luks_device_count: int
    cryptsetup_available: bool
    clevis_available: bool

    @property
    def can_manage_luks(self) -> bool:
        return (
            self.luks_present
            and self.cryptsetup_available
        )

    @property
    def can_use_clevis(self) -> bool:
        return (
            self.can_manage_luks
            and self.clevis_available
        )


def detect_capabilities(
    actual: ModuleActualState | None,
) -> EncryptionCapabilities:
    if actual is None:
        return EncryptionCapabilities(
            luks_present=False,
            luks_device_count=0,
            cryptsetup_available=False,
            clevis_available=False,
        )

    return EncryptionCapabilities(
        luks_present=bool(
            actual.get(
                "luks_present",
                False,
            )
        ),
        luks_device_count=int(
            actual.get(
                "luks_device_count",
                0,
            )
            or 0
        ),
        cryptsetup_available=bool(
            actual.get(
                "cryptsetup_available",
                False,
            )
        ),
        clevis_available=bool(
            actual.get(
                "clevis_available",
                False,
            )
        ),
    )
