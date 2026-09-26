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


def desired_state(
    settings: FirewallSettings | None = None,
) -> ModuleDesiredState:
    desired = {
        "service_active": DesiredSetting(
            key="service_active",
            value="active",
        ),
        "service_enabled": DesiredSetting(
            key="service_enabled",
            value="enabled",
        ),
        "ruleset_present": DesiredSetting(
            key="ruleset_present",
            value=True,
        ),
        "inet_filter_table": DesiredSetting(
            key="inet_filter_table",
            value=True,
        ),
        "input_policy_drop": DesiredSetting(
            key="input_policy_drop",
            value=True,
        ),
        "forward_policy_drop": DesiredSetting(
            key="forward_policy_drop",
            value=True,
        ),
    }

    if settings is not None:
        settings.validate()

        desired.update(
            {
                "management_interface":
                    DesiredSetting(
                        key=(
                            "management_interface"
                        ),
                        value=(
                            settings
                            .management_interface
                        ),
                    ),
                "management_ipv4_cidr":
                    DesiredSetting(
                        key=(
                            "management_ipv4_cidr"
                        ),
                        value=(
                            settings
                            .management_ipv4_cidr
                        ),
                    ),
                "ssh_port":
                    DesiredSetting(
                        key="ssh_port",
                        value=settings.ssh_port,
                    ),
                "allow_dhcp_client":
                    DesiredSetting(
                        key=(
                            "allow_dhcp_client"
                        ),
                        value=(
                            settings
                            .allow_dhcp_client
                        ),
                    ),
                "allow_ipv4_icmp":
                    DesiredSetting(
                        key=(
                            "allow_ipv4_icmp"
                        ),
                        value=(
                            settings
                            .allow_ipv4_icmp
                        ),
                    ),
                "allow_ipv6_icmp":
                    DesiredSetting(
                        key=(
                            "allow_ipv6_icmp"
                        ),
                        value=(
                            settings
                            .allow_ipv6_icmp
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
