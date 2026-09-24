"""SSH post-change verification."""

from __future__ import annotations

from homelabctl.core.models import (
    ModuleActualState,
    VerificationReport,
)
from homelabctl.core.verifier import verify_module
from homelabctl.features.ssh.inspect import desired_state
from homelabctl.features.ssh.schema import SSHSettings


def verify(
    actual: ModuleActualState | None,
    settings: SSHSettings,
) -> VerificationReport:
    return verify_module(
        desired_state(settings),
        actual,
    )
