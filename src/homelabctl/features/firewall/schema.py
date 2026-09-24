"""Firewall feature configuration schema."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass, field

from homelabctl.system.runtime_defaults import (
    default_management_interface,
    default_management_ipv4_cidr,
)


_INTERFACE_RE = re.compile(
    r"^[A-Za-z0-9_.:-]+$"
)


@dataclass(slots=True)
class FirewallSettings:
    management_interface: str = field(
        default_factory=(
            default_management_interface
        )
    )

    management_ipv4_cidr: str = field(
        default_factory=(
            default_management_ipv4_cidr
        )
    )

    ssh_port: int = 22

    allow_dhcp_client: bool = True
    allow_ipv4_icmp: bool = True
    allow_ipv6_icmp: bool = True

    def validate(self) -> None:
        if not _INTERFACE_RE.fullmatch(
            self.management_interface
        ):
            raise ValueError(
                "Invalid management interface."
            )

        network = ipaddress.ip_network(
            self.management_ipv4_cidr,
            strict=False,
        )

        if network.version != 4:
            raise ValueError(
                "Management CIDR must be IPv4."
            )

        if not 1 <= self.ssh_port <= 65535:
            raise ValueError(
                "SSH port must be between 1 and 65535."
            )
