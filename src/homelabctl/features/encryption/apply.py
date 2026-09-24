"""Sensitive encryption apply operations.

Automatic TPM/LUKS enrollment is intentionally disabled in the initial
implementation. Encryption changes require a dedicated reviewed workflow
before they may be executed automatically.
"""

from __future__ import annotations

from homelabctl.apply.transaction import (
    ApplyTransaction,
)


def build_tpm_enrollment_transaction(
    *,
    luks_device: str,
) -> ApplyTransaction:
    raise RuntimeError(
        "Automatic TPM/LUKS enrollment is not "
        "enabled in this version of HomeLabCTL. "
        "Use the guided manual workflow instead."
    )
