"""Foreground nftables apply transaction."""

from __future__ import annotations

from homelabctl.apply.transaction import (
    ActionType,
    ApplyAction,
    ApplyTransaction,
    new_transaction,
)
from homelabctl.features.firewall.plan import (
    NFTABLES_CONFIG,
    render_config,
)
from homelabctl.features.firewall.schema import (
    FirewallSettings,
)


def build_apply_transaction(
    settings: FirewallSettings,
) -> ApplyTransaction:
    settings.validate()

    return new_transaction(
        feature="firewall",
        actions=[
            ApplyAction(
                action_type=ActionType.WRITE_FILE,
                description=(
                    "Write managed nftables configuration."
                ),
                target=NFTABLES_CONFIG,
                content=render_config(settings),
                mode=0o755,
                backup=True,
            ),
            ApplyAction(
                action_type=ActionType.RUN_COMMAND,
                description=(
                    "Validate nftables configuration."
                ),
                argv=[
                    "/usr/sbin/nft",
                    "-c",
                    "-f",
                    NFTABLES_CONFIG,
                ],
                backup=False,
            ),
            ApplyAction(
                action_type=ActionType.RUN_COMMAND,
                description=(
                    "Apply nftables configuration."
                ),
                argv=[
                    "/usr/sbin/nft",
                    "-f",
                    NFTABLES_CONFIG,
                ],
                backup=False,
            ),
            ApplyAction(
                action_type=ActionType.SYSTEMCTL,
                description=(
                    "Enable nftables service."
                ),
                argv=[
                    "enable",
                    "nftables.service",
                ],
                backup=False,
            ),
        ],
    )
