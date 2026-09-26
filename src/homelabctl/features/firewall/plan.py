"""Build nftables firewall plans."""

from __future__ import annotations

from homelabctl.core.models import (
    ChangeKind,
    ModuleActualState,
    RiskLevel,
)
from homelabctl.core.planner import (
    build_plan,
    make_step,
)
from homelabctl.features.firewall.schema import (
    FirewallSettings,
)
from homelabctl.template_engine import render_template


NFTABLES_CONFIG = "/etc/nftables.conf"


def render_config(
    settings: FirewallSettings,
) -> str:
    settings.validate()

    return render_template(
        "nftables/nftables.conf.j2",
        management_interface=(
            settings.management_interface
        ),
        management_ipv4_cidr=(
            settings.management_ipv4_cidr
        ),
        ssh_port=settings.ssh_port,
        allow_dhcp_client=(
            settings.allow_dhcp_client
        ),
        allow_ipv4_icmp=(
            settings.allow_ipv4_icmp
        ),
        allow_ipv6_icmp=(
            settings.allow_ipv6_icmp
        ),
        trusted_ipv4_cidrs=(
            settings.trusted_ipv4_cidrs
        ),
        allowed_tcp_ports=(
            settings.allowed_tcp_ports
        ),
        allowed_udp_ports=(
            settings.allowed_udp_ports
        ),
    )


def build_firewall_plan(
    *,
    actual: ModuleActualState | None,
    settings: FirewallSettings,
):
    settings.validate()

    return build_plan(
        feature="firewall",
        title="Apply nftables firewall",
        summary=(
            "Install and apply the selected "
            "nftables host firewall."
        ),
        risk=RiskLevel.HIGH,
        steps=[
            make_step(
                step_id="write-nftables-config",
                description=(
                    "Write managed nftables configuration."
                ),
                kind=ChangeKind.MODIFY_FILE,
                target=NFTABLES_CONFIG,
                after=render_config(settings),
                requires_root=True,
                reversible=True,
            ),
            make_step(
                step_id="validate-nftables",
                description=(
                    "Validate nftables syntax."
                ),
                kind=ChangeKind.RUN_COMMAND,
                target=NFTABLES_CONFIG,
                requires_root=True,
                reversible=True,
                command_preview=(
                    "nft -c -f /etc/nftables.conf"
                ),
            ),
            make_step(
                step_id="apply-nftables",
                description=(
                    "Apply the validated ruleset."
                ),
                kind=ChangeKind.RUN_COMMAND,
                target=NFTABLES_CONFIG,
                requires_root=True,
                reversible=True,
                command_preview=(
                    "nft -f /etc/nftables.conf"
                ),
            ),
            make_step(
                step_id="enable-nftables",
                description=(
                    "Enable nftables at boot."
                ),
                kind=ChangeKind.ENABLE_SERVICE,
                target="nftables.service",
                requires_root=True,
                reversible=True,
            ),
        ],
        warnings=[
            (
                "Incorrect firewall rules can "
                "interrupt SSH access."
            )
        ],
    )
