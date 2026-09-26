"""nftables firewall collector."""

from __future__ import annotations

import ipaddress
import re
import shutil

from homelabctl.apply.firewall_safety import (
    FIREWALL_ROLLBACK_TIMEOUT_SECONDS,
    load_pending_firewall_rollback,
)
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


def _named_set_elements(
    ruleset: str,
    set_name: str,
) -> list[str] | None:
    set_match = re.search(
        (
            r"\bset\s+"
            + re.escape(set_name)
            + r"\s*\{"
            + r"(?P<body>.*?)"
            + r"^\s*\}"
        ),
        ruleset,
        flags=(
            re.MULTILINE
            | re.DOTALL
        ),
    )

    if set_match is None:
        return None

    body = set_match.group(
        "body"
    )

    elements_match = re.search(
        (
            r"\belements\s*=\s*\{"
            r"(?P<elements>[^}]*)"
            r"\}"
        ),
        body,
        flags=re.DOTALL,
    )

    if elements_match is None:
        return []

    return [
        item.strip()
        for item in (
            elements_match
            .group("elements")
            .split(",")
        )
        if item.strip()
    ]


def _parse_trusted_ipv4(
    ruleset: str,
    management_ipv4_cidr: str | None,
) -> list[str] | None:
    elements = _named_set_elements(
        ruleset,
        "homelabctl_trusted_ipv4",
    )

    # Legacy managed configs did not have
    # advanced-policy sets.
    if elements is None:
        return []

    if management_ipv4_cidr is None:
        return None

    try:
        management = ipaddress.ip_network(
            management_ipv4_cidr,
            strict=False,
        )

        networks = [
            ipaddress.ip_network(
                value,
                strict=False,
            )
            for value in elements
        ]
    except ValueError:
        return None

    if any(
        network.version != 4
        for network in networks
    ):
        return None

    if management not in networks:
        return None

    extras = [
        network
        for network in networks
        if network != management
    ]

    extras.sort(
        key=lambda network: (
            int(network.network_address),
            network.prefixlen,
        )
    )

    return [
        str(network)
        for network in extras
    ]


def _parse_allowed_ports(
    ruleset: str,
    *,
    management_interface: str | None,
    protocol: str,
    set_name: str,
) -> list[int] | None:
    elements = _named_set_elements(
        ruleset,
        set_name,
    )

    # Legacy config / disabled advanced rule.
    if elements is None:
        return []

    try:
        ports = [
            int(value)
            for value in elements
        ]
    except ValueError:
        return None

    if any(
        port < 1 or port > 65535
        for port in ports
    ):
        return None

    if len(set(ports)) != len(ports):
        return None

    if not ports:
        return []

    if management_interface is None:
        return None

    rule_pattern = re.compile(
        (
            r'iifname\s+"'
            + re.escape(
                management_interface
            )
            + r'"\s+ip\s+saddr\s+'
            r"@homelabctl_trusted_ipv4"
            r"\s+"
            + re.escape(protocol)
            + r"\s+dport\s+@"
            + re.escape(set_name)
            + r"\s+ct\s+state\s+new\s+accept"
        )
    )

    if rule_pattern.search(
        ruleset
    ) is None:
        return None

    return sorted(
        ports
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

    trusted_ipv4_cidrs = (
        _parse_trusted_ipv4(
            ruleset,
            management_ipv4_cidr,
        )
    )

    allowed_tcp_ports = (
        _parse_allowed_ports(
            ruleset,
            management_interface=(
                management_interface
            ),
            protocol="tcp",
            set_name=(
                "homelabctl_allowed_tcp_ports"
            ),
        )
    )

    allowed_udp_ports = (
        _parse_allowed_ports(
            ruleset,
            management_interface=(
                management_interface
            ),
            protocol="udp",
            set_name=(
                "homelabctl_allowed_udp_ports"
            ),
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
        "trusted_ipv4_cidrs": (
            trusted_ipv4_cidrs
        ),
        "allowed_tcp_ports": (
            allowed_tcp_ports
        ),
        "allowed_udp_ports": (
            allowed_udp_ports
        ),
    }


def _firewall_rollback_safety_state(
) -> dict[str, object]:
    """Return minimal read-only rollback state for the frontend."""

    try:
        pending = (
            load_pending_firewall_rollback()
        )

    except (
        OSError,
        RuntimeError,
        ValueError,
    ):
        return {
            "firewall_rollback_state_readable": False,
            "firewall_rollback_pending": None,
            "firewall_rollback_transaction_id": None,
            "firewall_rollback_timeout_seconds": (
                FIREWALL_ROLLBACK_TIMEOUT_SECONDS
            ),
        }

    if pending is None:
        return {
            "firewall_rollback_state_readable": True,
            "firewall_rollback_pending": False,
            "firewall_rollback_transaction_id": None,
            "firewall_rollback_timeout_seconds": (
                FIREWALL_ROLLBACK_TIMEOUT_SECONDS
            ),
        }

    transaction_id = pending.get(
        "transaction_id"
    )

    if not isinstance(
        transaction_id,
        str,
    ):
        return {
            "firewall_rollback_state_readable": False,
            "firewall_rollback_pending": None,
            "firewall_rollback_transaction_id": None,
            "firewall_rollback_timeout_seconds": (
                FIREWALL_ROLLBACK_TIMEOUT_SECONDS
            ),
        }

    return {
        "firewall_rollback_state_readable": True,
        "firewall_rollback_pending": True,
        "firewall_rollback_transaction_id": (
            transaction_id
        ),
        "firewall_rollback_timeout_seconds": (
            FIREWALL_ROLLBACK_TIMEOUT_SECONDS
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

        rollback_safety = (
            _firewall_rollback_safety_state()
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
            **rollback_safety,
        }

        policy_readable = all(
            values[key] is not None
            for key in (
                "management_interface",
                "management_ipv4_cidr",
                "ssh_port",
                "allow_dhcp_client",
                "trusted_ipv4_cidrs",
                "allowed_tcp_ports",
                "allowed_udp_ports",
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
                and values[
                    "firewall_rollback_state_readable"
                ]
                and not values[
                    "firewall_rollback_pending"
                ]
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
