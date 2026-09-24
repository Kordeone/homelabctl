"""Create foreground privileged SSH apply transactions."""

from __future__ import annotations

from homelabctl.apply.transaction import (
    ActionType,
    ApplyAction,
    ApplyTransaction,
    new_transaction,
)
from homelabctl.features.ssh.constants import (
    MANAGED_SSH_PATH,
)
from homelabctl.features.ssh.plan import (
    render_config,
)
from homelabctl.features.ssh.schema import SSHSettings


def build_apply_transaction(
    settings: SSHSettings,
) -> ApplyTransaction:
    settings.validate()

    return new_transaction(
        feature="ssh",
        actions=[
            ApplyAction(
                action_type=ActionType.WRITE_FILE,
                description=(
                    "Write managed SSH hardening "
                    "configuration."
                ),
                target=MANAGED_SSH_PATH,
                content=render_config(settings),
                mode=0o644,
                backup=True,
            ),
            ApplyAction(
                action_type=ActionType.RUN_COMMAND,
                description=(
                    "Validate OpenSSH configuration."
                ),
                argv=[
                    "/usr/sbin/sshd",
                    "-t",
                ],
                backup=False,
            ),
            ApplyAction(
                action_type=ActionType.SYSTEMCTL,
                description=(
                    "Reload OpenSSH service."
                ),
                argv=[
                    "reload",
                    "ssh.service",
                ],
                backup=False,
            ),
        ],
    )
