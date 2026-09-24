"""Headless-mode feature configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

from homelabctl.system.runtime_defaults import current_user


@dataclass(slots=True)
class HeadlessSettings:
    desktop_user: str = field(
        default_factory=current_user
    )

    handle_lid_switch: str = "ignore"
    handle_lid_switch_external_power: str = "ignore"
    handle_lid_switch_docked: str = "ignore"
    idle_action: str = "ignore"

    user_ac_action: str = "nothing"
    user_battery_action: str = "nothing"

    gdm_ac_action: str = "nothing"
    gdm_battery_action: str = "nothing"
    gdm_ac_timeout: int = 0
    gdm_battery_timeout: int = 0

    def validate(self) -> None:
        if not self.desktop_user.strip():
            raise ValueError(
                "desktop_user cannot be empty."
            )

        for name, value in (
            (
                "handle_lid_switch",
                self.handle_lid_switch,
            ),
            (
                "handle_lid_switch_external_power",
                self.handle_lid_switch_external_power,
            ),
            (
                "handle_lid_switch_docked",
                self.handle_lid_switch_docked,
            ),
            (
                "idle_action",
                self.idle_action,
            ),
        ):
            if value != "ignore":
                raise ValueError(
                    f"{name} must currently be 'ignore'."
                )

        for name, value in (
            (
                "user_ac_action",
                self.user_ac_action,
            ),
            (
                "user_battery_action",
                self.user_battery_action,
            ),
            (
                "gdm_ac_action",
                self.gdm_ac_action,
            ),
            (
                "gdm_battery_action",
                self.gdm_battery_action,
            ),
        ):
            if value != "nothing":
                raise ValueError(
                    f"{name} must currently be 'nothing'."
                )

        if self.gdm_ac_timeout < 0:
            raise ValueError(
                "gdm_ac_timeout cannot be negative."
            )

        if self.gdm_battery_timeout < 0:
            raise ValueError(
                "gdm_battery_timeout cannot be negative."
            )
