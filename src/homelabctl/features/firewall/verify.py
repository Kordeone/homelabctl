"""Firewall post-change verification."""

from __future__ import annotations

from homelabctl.core.models import (
    ModuleActualState,
    VerificationReport,
)
from homelabctl.core.verifier import verify_module
from homelabctl.features.firewall.inspect import (
    desired_state,
)


def verify(
    actual: ModuleActualState | None,
) -> VerificationReport:
    return verify_module(
        desired_state(),
        actual,
    )
