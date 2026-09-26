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
from homelabctl.features.firewall.schema import (
    FirewallSettings,
)


def verify(
    actual: ModuleActualState | None,
    settings: FirewallSettings | None = None,
) -> VerificationReport:
    return verify_module(
        desired_state(
            settings
        ),
        actual,
    )
