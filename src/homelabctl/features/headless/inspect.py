"""Interpret headless state reported by homelabd."""

from __future__ import annotations

from homelabctl.core.drift import compare_module_state
from homelabctl.core.models import (
    DesiredSetting,
    ModuleActualState,
    ModuleDesiredState,
    Status,
)
from homelabctl.features.headless.schema import (
    HeadlessSettings,
)


def desired_state(
    settings: HeadlessSettings,
) -> ModuleDesiredState:
    settings.validate()

    return ModuleDesiredState(
        module="headless",
        settings={
            "lid_switch": DesiredSetting(
                key="lid_switch",
                value=settings.handle_lid_switch,
            ),
            "lid_switch_external_power": DesiredSetting(
                key="lid_switch_external_power",
                value=(
                    settings.handle_lid_switch_external_power
                ),
            ),
            "lid_switch_docked": DesiredSetting(
                key="lid_switch_docked",
                value=settings.handle_lid_switch_docked,
            ),
            "idle_action": DesiredSetting(
                key="idle_action",
                value=settings.idle_action,
            ),
            "gdm_sleep_inactive_ac_type": DesiredSetting(
                key="gdm_sleep_inactive_ac_type",
                value=settings.gdm_ac_action,
            ),
            "gdm_sleep_inactive_ac_timeout": DesiredSetting(
                key="gdm_sleep_inactive_ac_timeout",
                value=settings.gdm_ac_timeout,
            ),
            "gdm_sleep_inactive_battery_type":
                DesiredSetting(
                    key=(
                        "gdm_sleep_inactive_"
                        "battery_type"
                    ),
                    value=settings.gdm_battery_action,
                ),
            "gdm_sleep_inactive_battery_timeout":
                DesiredSetting(
                    key=(
                        "gdm_sleep_inactive_"
                        "battery_timeout"
                    ),
                    value=settings.gdm_battery_timeout,
                ),
        },
    )


def evaluate(
    actual: ModuleActualState | None,
    settings: HeadlessSettings,
) -> Status:
    return compare_module_state(
        desired_state(settings),
        actual,
    ).status
