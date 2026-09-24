"""Headless post-change verification."""

from __future__ import annotations

from homelabctl.core.models import (
    ModuleActualState,
    VerificationReport,
)
from homelabctl.core.verifier import verify_module
from homelabctl.features.headless.inspect import (
    desired_state,
)
from homelabctl.features.headless.schema import (
    HeadlessSettings,
)


def verify(
    actual: ModuleActualState | None,
    settings: HeadlessSettings,
) -> VerificationReport:
    return verify_module(
        desired_state(settings),
        actual,
    )
