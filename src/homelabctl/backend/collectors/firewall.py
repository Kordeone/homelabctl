"""nftables firewall collector."""

from __future__ import annotations

import re
import shutil

from homelabctl.backend.collectors import CollectorResult
from homelabctl.core.actual_state import make_actual_state
from homelabctl.core.models import Status
from homelabctl.system.commands import run_command
from homelabctl.system.systemd import (
    unit_active_state,
    unit_enabled_state,
    unit_exists,
)


_MANAGEMENT_SSH_RE = re.compile(
    r'iifname\s+"(?P<interface>[A-Za-z0-9_.:-]+)"'
    r"\s+ip\s+saddr\s+"
    r"(?P<cidr>[0-9.]+/[0-9]+)"
    r"\s+tcp\s+dport\s+"
    r"(?P<port>[0-9]+)"
    r"\s+ct\s+state\s+new\s+accept"
)


def _parse_managed_policy(
    ruleset: str,
) -> dict[str, object]:
    match = _MANAGEMENT_SSH_RE.search(
        ruleset
    )

    management_interface: str | None = None
    management_ipv4_cidr: str | None = None
    ssh_port: int | None = None

    if match is not None:
        management_interface = match.group(
            "interface"
        )
        management_ipv4_cidr = match.group(
            "cidr"
        )
        ssh_port = int(
            match.group(
                "port"
            )
        )

    allow_dhcp_client: bool | None = None

    if management_interface is not None:
        dhcp_pattern = re.compile(
            r'iifname\s+"'
            + re.escape(
                management_interface
            )
            + r'"\s+udp\s+sport\s+67'
            r"\s+udp\s+dport\s+68"
            r"\s+accept"
        )

        allow_dhcp_client = bool(
            dhcp_pattern.search(
                ruleset
            )
        )

    return {
        "management_interface": (
            management_interface
        ),
        "management_ipv4_cidr": (
            management_ipv4_cidr
        ),
        "ssh_port": ssh_port,
        "allow_dhcp_client": (
            allow_dhcp_client
        ),
        "allow_ipv4_icmp": (
            "meta l4proto icmp accept"
            in ruleset
        ),
        "allow_ipv6_icmp": (
            "meta l4proto ipv6-icmp accept"
            in ruleset
        ),
    }


class FirewallCollector:
    name = "firewall"

    def collect(self) -> CollectorResult:
        nft_available = (
            shutil.which("nft")
            is not None
        )

        service_exists = unit_exists(
            "nftables.service"
        )

        ruleset = ""

        if nft_available:
            result = run_command(
                [
                    "nft",
                    "list",
                    "ruleset",
                ],
                timeout=10.0,
            )

            if result.success:
                ruleset = result.stdout

        policy = _parse_managed_policy(
            ruleset
        )

        values = {
            "nft_available": (
                nft_available
            ),
            "service_exists": (
                service_exists
            ),
            "service_active": (
                unit_active_state(
                    "nftables.service"
                )
                if service_exists
                else "not-found"
            ),
            "service_enabled": (
                unit_enabled_state(
                    "nftables.service"
                )
                if service_exists
                else "not-found"
            ),
            "ruleset_present": bool(
                ruleset.strip()
            ),
            "inet_filter_table": (
                "table inet filter"
                in ruleset
            ),
            "input_policy_drop": (
                "hook input" in ruleset
                and "policy drop"
                in ruleset
            ),
            "forward_policy_drop": (
                "hook forward" in ruleset
                and "policy drop"
                in ruleset
            ),
            **policy,
        }

        policy_readable = all(
            values[key] is not None
            for key in (
                "management_interface",
                "management_ipv4_cidr",
                "ssh_port",
                "allow_dhcp_client",
            )
        )

        status = (
            Status.PASS
            if (
                nft_available
                and bool(
                    ruleset.strip()
                )
                and policy_readable
            )
            else Status.WARNING
        )

        state = make_actual_state(
            "firewall",
            status=status,
            summary=(
                "nftables firewall state collected."
            ),
            values=values,
        )

        return CollectorResult(
            modules=[
                state
            ]
        )
