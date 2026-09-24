"""Interpret firewall state reported by homelabd."""

from __future__ import annotations

from homelabctl.core.drift import compare_module_state
from homelabctl.core.models import (
    DesiredSetting,
    ModuleActualState,
    ModuleDesiredState,
    Status,
)


def desired_state() -> ModuleDesiredState:
    return ModuleDesiredState(
        module="firewall",
        settings={
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
        },
    )


def evaluate(
    actual: ModuleActualState | None,
) -> Status:
    return compare_module_state(
        desired_state(),
        actual,
    ).status
