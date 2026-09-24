"""Security capability interpretation."""

from __future__ import annotations

from dataclasses import dataclass

from homelabctl.core.models import ModuleActualState


@dataclass(slots=True)
class SecurityCapabilities:
    secure_boot_known: bool
    secure_boot_enabled: bool | None

    kernel_lockdown_known: bool
    kernel_lockdown_mode: str | None

    tpm_present: bool

    @property
    def lockdown_active(self) -> bool:
        return self.kernel_lockdown_mode in {
            "integrity",
            "confidentiality",
        }


def detect_capabilities(
    actual: ModuleActualState | None,
) -> SecurityCapabilities:
    if actual is None:
        return SecurityCapabilities(
            secure_boot_known=False,
            secure_boot_enabled=None,
            kernel_lockdown_known=False,
            kernel_lockdown_mode=None,
            tpm_present=False,
        )

    secure_boot = actual.get(
        "secure_boot"
    )

    lockdown = actual.get(
        "kernel_lockdown"
    )

    tpm_present = bool(
        actual.get(
            "tpm_present",
            False,
        )
    )

    return SecurityCapabilities(
        secure_boot_known=(
            isinstance(
                secure_boot,
                bool,
            )
        ),
        secure_boot_enabled=(
            secure_boot
            if isinstance(
                secure_boot,
                bool,
            )
            else None
        ),
        kernel_lockdown_known=(
            isinstance(
                lockdown,
                str,
            )
            and bool(lockdown)
        ),
        kernel_lockdown_mode=(
            lockdown
            if isinstance(
                lockdown,
                str,
            )
            else None
        ),
        tpm_present=tpm_present,
    )
