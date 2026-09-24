"""Headless server configuration feature."""

from homelabctl.features.headless.apply import (
    build_apply_transaction,
)
from homelabctl.features.headless.inspect import (
    desired_state,
    evaluate,
)
from homelabctl.features.headless.plan import (
    LOGIND_DROP_IN,
    build_headless_plan,
    render_logind_config,
)
from homelabctl.features.headless.schema import (
    HeadlessSettings,
)
from homelabctl.features.headless.verify import verify

__all__ = [
    "HeadlessSettings",
    "LOGIND_DROP_IN",
    "build_apply_transaction",
    "build_headless_plan",
    "desired_state",
    "evaluate",
    "render_logind_config",
    "verify",
]
