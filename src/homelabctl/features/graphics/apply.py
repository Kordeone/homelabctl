"""Foreground graphics apply transaction."""

from __future__ import annotations

from homelabctl.apply.transaction import (
    ActionType,
    ApplyAction,
    ApplyTransaction,
    new_transaction,
)
from homelabctl.features.graphics.plan import (
    NOUVEAU_CONFIG,
    render_nouveau_blacklist,
)


def build_disable_nouveau_transaction(
) -> ApplyTransaction:
    return new_transaction(
        feature="graphics",
        actions=[
            ApplyAction(
                action_type=ActionType.WRITE_FILE,
                description=(
                    "Write Nouveau blacklist."
                ),
                target=NOUVEAU_CONFIG,
                content=render_nouveau_blacklist(),
                mode=0o644,
                backup=True,
            ),
            ApplyAction(
                action_type=ActionType.RUN_COMMAND,
                description=(
                    "Rebuild initramfs."
                ),
                argv=[
                    "/usr/sbin/update-initramfs",
                    "-u",
                ],
                backup=False,
            ),
        ],
    )
