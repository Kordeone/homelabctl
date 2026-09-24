"""Interpret headless state reported by homelabd."""

from __future__ import annotations

from homelabctl.core.drift import compare_module_state
from homelabctl.core.models import (
    DesiredSetting,
    ModuleActualState,
    ModuleDesiredState,
    StateValue,
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
            "desktop_user": DesiredSetting(
                key="desktop_user",
                value=settings.desktop_user,
            ),
            "user_sleep_inactive_ac_type": DesiredSetting(
                key="user_sleep_inactive_ac_type",
                value=settings.user_ac_action,
            ),
            "user_sleep_inactive_battery_type":
                DesiredSetting(
                    key=(
                        "user_sleep_inactive_"
                        "battery_type"
                    ),
                    value=settings.user_battery_action,
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


def actual_for_settings(
    actual: ModuleActualState | None,
    settings: HeadlessSettings,
) -> ModuleActualState | None:
    """Project the selected desktop user into flat compare keys."""

    if actual is None:
        return None

    values = dict(
        actual.values
    )

    desktop_users = actual.get(
        "desktop_users",
        {},
    )

    selected: dict[str, object] | None = None

    if isinstance(
        desktop_users,
        dict,
    ):
        candidate = desktop_users.get(
            settings.desktop_user
        )

        if isinstance(
            candidate,
            dict,
        ):
            selected = candidate

    selected_user = (
        settings.desktop_user
        if selected is not None
        else None
    )

    values["desktop_user"] = StateValue(
        key="desktop_user",
        value=selected_user,
        source="desktop_users",
    )

    values[
        "user_sleep_inactive_ac_type"
    ] = StateValue(
        key="user_sleep_inactive_ac_type",
        value=(
            selected.get(
                "sleep_inactive_ac_type"
            )
            if selected is not None
            else None
        ),
        source=(
            f"desktop_users.{settings.desktop_user}"
        ),
    )

    values[
        "user_sleep_inactive_battery_type"
    ] = StateValue(
        key="user_sleep_inactive_battery_type",
        value=(
            selected.get(
                "sleep_inactive_battery_type"
            )
            if selected is not None
            else None
        ),
        source=(
            f"desktop_users.{settings.desktop_user}"
        ),
    )

    return ModuleActualState(
        module=actual.module,
        collected_at=actual.collected_at,
        status=actual.status,
        summary=actual.summary,
        values=values,
    )


def evaluate(
    actual: ModuleActualState | None,
    settings: HeadlessSettings,
) -> Status:
    return compare_module_state(
        desired_state(settings),
        actual_for_settings(
            actual,
            settings,
        ),
    ).status
