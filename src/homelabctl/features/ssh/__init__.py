"""SSH management feature."""

from homelabctl.features.ssh.apply import (
    build_apply_transaction,
)
from homelabctl.features.ssh.inspect import (
    desired_state,
    evaluate,
)
from homelabctl.features.ssh.plan import (
    SSH_DROP_IN,
    build_ssh_plan,
    render_config,
)
from homelabctl.features.ssh.schema import (
    SSHSettings,
)
from homelabctl.features.ssh.session_actions import (
    build_disconnect_session_transaction,
    validate_session_id,
)
from homelabctl.features.ssh.verify import verify

__all__ = [
    "SSHSettings",
    "build_disconnect_session_transaction",
    "validate_session_id",
    "SSH_DROP_IN",
    "build_apply_transaction",
    "build_ssh_plan",
    "desired_state",
    "evaluate",
    "render_config",
    "verify",
]
