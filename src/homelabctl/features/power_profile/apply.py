"""Foreground install/update transaction for power profiles."""

from __future__ import annotations

from homelabctl.apply.transaction import (
    ActionType,
    ApplyAction,
    ApplyTransaction,
    new_transaction,
)
from homelabctl.features.power_profile.inspect import (
    PowerProfilePolicy,
)
from homelabctl.features.power_profile.plan import (
    SCRIPT_PATH,
    SERVICE_PATH,
    UDEV_RULE_PATH,
    render_runtime_script,
    render_service,
    render_udev_rule,
)


def build_apply_transaction(
    policy: PowerProfilePolicy,
) -> ApplyTransaction:
    policy.validate()

    return new_transaction(
        feature="power_profile",
        actions=[
            ApplyAction(
                action_type=ActionType.WRITE_FILE,
                description=(
                    "Install power-profile runtime."
                ),
                target=SCRIPT_PATH,
                content=render_runtime_script(
                    policy
                ),
                mode=0o755,
                backup=True,
            ),
            ApplyAction(
                action_type=ActionType.WRITE_FILE,
                description=(
                    "Install power-profile service."
                ),
                target=SERVICE_PATH,
                content=render_service(),
                mode=0o644,
                backup=True,
            ),
            ApplyAction(
                action_type=ActionType.WRITE_FILE,
                description=(
                    "Install power-profile udev rule."
                ),
                target=UDEV_RULE_PATH,
                content=render_udev_rule(),
                mode=0o644,
                backup=True,
            ),
            ApplyAction(
                action_type=ActionType.SYSTEMCTL,
                description="Reload systemd.",
                argv=[
                    "daemon-reload",
                ],
                backup=False,
            ),
            ApplyAction(
                action_type=ActionType.RUN_COMMAND,
                description="Reload udev rules.",
                argv=[
                    "/usr/bin/udevadm",
                    "control",
                    "--reload-rules",
                ],
                backup=False,
            ),
            ApplyAction(
                action_type=ActionType.SYSTEMCTL,
                description=(
                    "Re-enable power-profile service "
                    "with canonical boot target."
                ),
                argv=[
                    "reenable",
                    "homelab-power-mode.service",
                ],
                backup=False,
            ),
            ApplyAction(
                action_type=ActionType.SYSTEMCTL,
                description=(
                    "Apply the correct profile now."
                ),
                argv=[
                    "start",
                    "homelab-power-mode.service",
                ],
                backup=False,
            ),
        ],
    )
