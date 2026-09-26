"""Interpret firewall state reported by homelabd."""

from __future__ import annotations

from homelabctl.core.drift import compare_module_state
from homelabctl.core.models import (
    DesiredSetting,
    ModuleActualState,
    ModuleDesiredState,
    Status,
)
from homelabctl.features.firewall.schema import (
    FirewallSettings,
)


def _setting(
    key: str,
    value: object,
) -> DesiredSetting:
    return DesiredSetting(
        key=key,
        value=value,
    )


def desired_state(
    settings: FirewallSettings | None = None,
) -> ModuleDesiredState:
    desired = {
        "service_active": _setting(
            "service_active",
            "active",
        ),
        "service_enabled": _setting(
            "service_enabled",
            "enabled",
        ),
        "ruleset_present": _setting(
            "ruleset_present",
            True,
        ),
        "inet_filter_table": _setting(
            "inet_filter_table",
            True,
        ),
        "input_policy_drop": _setting(
            "input_policy_drop",
            True,
        ),
        "forward_policy_drop": _setting(
            "forward_policy_drop",
            True,
        ),
    }

    if settings is not None:
        settings.validate()

        desired.update(
            {
                "management_interface":
                    _setting(
                        "management_interface",
                        settings
                        .management_interface,
                    ),
                "management_ipv4_cidr":
                    _setting(
                        "management_ipv4_cidr",
                        settings
                        .management_ipv4_cidr,
                    ),
                "ssh_port":
                    _setting(
                        "ssh_port",
                        settings.ssh_port,
                    ),
                "allow_dhcp_client":
                    _setting(
                        "allow_dhcp_client",
                        settings
                        .allow_dhcp_client,
                    ),
                "allow_ipv4_icmp":
                    _setting(
                        "allow_ipv4_icmp",
                        settings
                        .allow_ipv4_icmp,
                    ),
                "allow_ipv6_icmp":
                    _setting(
                        "allow_ipv6_icmp",
                        settings
                        .allow_ipv6_icmp,
                    ),
                "trusted_ipv4_cidrs":
                    _setting(
                        "trusted_ipv4_cidrs",
                        sorted(
                            settings
                            .trusted_ipv4_cidrs
                        ),
                    ),
                "allowed_tcp_ports":
                    _setting(
                        "allowed_tcp_ports",
                        sorted(
                            settings
                            .allowed_tcp_ports
                        ),
                    ),
                "allowed_udp_ports":
                    _setting(
                        "allowed_udp_ports",
                        sorted(
                            settings
                            .allowed_udp_ports
                        ),
                    ),
            }
        )

    return ModuleDesiredState(
        module="firewall",
        settings=desired,
    )


def evaluate(
    actual: ModuleActualState | None,
    settings: FirewallSettings | None = None,
) -> Status:
    return compare_module_state(
        desired_state(
            settings
        ),
        actual,
    ).status
