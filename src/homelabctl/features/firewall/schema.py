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


def _trusted_ipv4_network(
    value: str,
):
    network = ipaddress.ip_network(
        value,
        strict=False,
    )

    if network.version != 4:
        raise ValueError(
            "Trusted networks must be IPv4."
        )

    if str(network) != value:
        raise ValueError(
            "Trusted networks must use canonical "
            "network form."
        )

    return network


def _validate_ports(
    ports: tuple[int, ...],
    *,
    label: str,
) -> None:
    seen: set[int] = set()

    for port in ports:
        if (
            not isinstance(port, int)
            or isinstance(port, bool)
            or not 1 <= port <= 65535
        ):
            raise ValueError(
                f"{label} ports must be between "
                "1 and 65535."
            )

        if port in seen:
            raise ValueError(
                f"{label} ports must not contain "
                "duplicates."
            )

        seen.add(port)


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

    trusted_ipv4_cidrs: tuple[str, ...] = ()

    allowed_tcp_ports: tuple[int, ...] = ()
    allowed_udp_ports: tuple[int, ...] = ()

    def validate(self) -> None:
        if not _INTERFACE_RE.fullmatch(
            self.management_interface
        ):
            raise ValueError(
                "Invalid management interface."
            )

        management_network = ipaddress.ip_network(
            self.management_ipv4_cidr,
            strict=False,
        )

        if management_network.version != 4:
            raise ValueError(
                "Management CIDR must be IPv4."
            )

        if not 1 <= self.ssh_port <= 65535:
            raise ValueError(
                "SSH port must be between 1 and 65535."
            )

        trusted_networks = []

        for value in self.trusted_ipv4_cidrs:
            network = _trusted_ipv4_network(
                value
            )

            if network.overlaps(
                management_network
            ):
                raise ValueError(
                    "Trusted networks must not overlap "
                    "the management network."
                )

            for existing in trusted_networks:
                if network.overlaps(existing):
                    raise ValueError(
                        "Trusted networks must not "
                        "overlap each other."
                    )

            trusted_networks.append(
                network
            )

        _validate_ports(
            self.allowed_tcp_ports,
            label="TCP",
        )

        _validate_ports(
            self.allowed_udp_ports,
            label="UDP",
        )
