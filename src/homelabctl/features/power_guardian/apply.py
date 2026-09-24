"""Foreground Power Guardian installation transaction."""

from __future__ import annotations

from pathlib import Path

from homelabctl.apply.transaction import (
    ActionType,
    ApplyAction,
    ApplyTransaction,
    new_transaction,
)
from homelabctl.features.power_guardian.config import (
    PowerGuardianConfig,
)
from homelabctl.features.power_guardian.plan import (
    CONFIG_PATH,
    SCRIPT_PATH,
    SERVICE_PATH,
    TIMER_PATH,
    render_config,
    render_service,
    render_timer,
)


def runtime_source() -> str:
    path = (
        Path(__file__).parent
        / "runtime"
        / "guardian.py"
    )

    return path.read_text(
        encoding="utf-8"
    )


def build_apply_transaction(
    config: PowerGuardianConfig,
) -> ApplyTransaction:
    config.validate()

    return new_transaction(
        feature="power_guardian",
        actions=[
            ApplyAction(
                action_type=ActionType.WRITE_FILE,
                description=(
                    "Install Power Guardian runtime."
                ),
                target=SCRIPT_PATH,
                content=runtime_source(),
                mode=0o755,
                backup=True,
            ),
            ApplyAction(
                action_type=ActionType.WRITE_FILE,
                description=(
                    "Install Power Guardian configuration."
                ),
                target=CONFIG_PATH,
                content=render_config(config),
                mode=0o644,
                backup=True,
            ),
            ApplyAction(
                action_type=ActionType.WRITE_FILE,
                description=(
                    "Install Power Guardian service."
                ),
                target=SERVICE_PATH,
                content=render_service(),
                mode=0o644,
                backup=True,
            ),
            ApplyAction(
                action_type=ActionType.WRITE_FILE,
                description=(
                    "Install Power Guardian timer."
                ),
                target=TIMER_PATH,
                content=render_timer(),
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
                action_type=ActionType.SYSTEMCTL,
                description=(
                    "Enable and start Power Guardian timer."
                ),
                argv=[
                    "enable-now",
                    "homelab-power-guardian.timer",
                ],
                backup=False,
            ),
        ],
    )
