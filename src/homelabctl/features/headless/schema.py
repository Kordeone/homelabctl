"""Headless-mode feature configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

from homelabctl.system.runtime_defaults import current_user


SYSTEM_EVENT_ACTIONS = frozenset(
    {
        "ignore",
        "poweroff",
        "reboot",
        "suspend",
        "hibernate",
        "hybrid-sleep",
        "suspend-then-hibernate",
        "sleep",
        "lock",
    }
)

IDLE_ACTIONS = frozenset(
    {
        "ignore",
        "poweroff",
        "suspend",
        "hibernate",
        "hybrid-sleep",
        "suspend-then-hibernate",
        "sleep",
        "lock",
    }
)

DESKTOP_POWER_ACTIONS = frozenset(
    {
        "blank",
        "suspend",
        "shutdown",
        "hibernate",
        "interactive",
        "nothing",
        "logout",
    }
)


@dataclass(slots=True)
class HeadlessSettings:
    desktop_user: str = field(
        default_factory=current_user
    )

    # systemd-logind
    handle_lid_switch: str = "ignore"
    handle_lid_switch_external_power: str = "ignore"
    handle_lid_switch_docked: str = "ignore"

    handle_power_key: str = "poweroff"
    handle_power_key_long_press: str = "ignore"

    idle_action: str = "ignore"
    idle_action_sec: int = 1800

    # Desktop session
    user_ac_action: str = "nothing"
    user_ac_timeout: int = 900

    user_battery_action: str = "nothing"
    user_battery_timeout: int = 900

    # GDM login screen
    gdm_ac_action: str = "nothing"
    gdm_ac_timeout: int = 0

    gdm_battery_action: str = "nothing"
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
                "handle_power_key",
                self.handle_power_key,
            ),
            (
                "handle_power_key_long_press",
                self.handle_power_key_long_press,
            ),
        ):
            if value not in SYSTEM_EVENT_ACTIONS:
                raise ValueError(
                    f"Unsupported {name}: {value}"
                )

        if self.idle_action not in IDLE_ACTIONS:
            raise ValueError(
                f"Unsupported idle_action: "
                f"{self.idle_action}"
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
            if value not in DESKTOP_POWER_ACTIONS:
                raise ValueError(
                    f"Unsupported {name}: {value}"
                )

        for name, value in (
            (
                "idle_action_sec",
                self.idle_action_sec,
            ),
            (
                "user_ac_timeout",
                self.user_ac_timeout,
            ),
            (
                "user_battery_timeout",
                self.user_battery_timeout,
            ),
            (
                "gdm_ac_timeout",
                self.gdm_ac_timeout,
            ),
            (
                "gdm_battery_timeout",
                self.gdm_battery_timeout,
            ),
        ):
            if value < 0:
                raise ValueError(
                    f"{name} cannot be negative."
                )
