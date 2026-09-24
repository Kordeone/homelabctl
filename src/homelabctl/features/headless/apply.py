"""Foreground apply transaction for headless mode."""

from __future__ import annotations

from homelabctl.apply.transaction import (
    ActionType,
    ApplyAction,
    ApplyTransaction,
    new_transaction,
)
from homelabctl.features.headless.plan import (
    LOGIND_DROP_IN,
    render_logind_config,
)
from homelabctl.features.headless.schema import (
    HeadlessSettings,
)


POWER_SCHEMA = (
    "org.gnome.settings-daemon.plugins.power"
)


def _gsettings_action(
    *,
    user: str,
    key: str,
    value: str,
    description: str,
) -> ApplyAction:
    return ApplyAction(
        action_type=ActionType.RUN_COMMAND,
        description=description,
        argv=[
            "runuser",
            "-u",
            user,
            "--",
            "dbus-run-session",
            "gsettings",
            "set",
            POWER_SCHEMA,
            key,
            value,
        ],
        backup=False,
    )


def build_apply_transaction(
    settings: HeadlessSettings,
) -> ApplyTransaction:
    settings.validate()

    actions = [
        ApplyAction(
            action_type=ActionType.WRITE_FILE,
            description=(
                "Write systemd-logind headless "
                "configuration."
            ),
            target=LOGIND_DROP_IN,
            content=render_logind_config(
                settings
            ),
            mode=0o644,
            backup=True,
        ),

        _gsettings_action(
            user=settings.desktop_user,
            key="sleep-inactive-ac-type",
            value=settings.user_ac_action,
            description=(
                "Disable AC idle suspend for "
                "the desktop user."
            ),
        ),

        _gsettings_action(
            user=settings.desktop_user,
            key="sleep-inactive-battery-type",
            value=settings.user_battery_action,
            description=(
                "Disable battery idle suspend for "
                "the desktop user."
            ),
        ),

        _gsettings_action(
            user="Debian-gdm",
            key="sleep-inactive-ac-type",
            value=settings.gdm_ac_action,
            description=(
                "Disable GDM AC idle suspend."
            ),
        ),

        _gsettings_action(
            user="Debian-gdm",
            key="sleep-inactive-ac-timeout",
            value=str(settings.gdm_ac_timeout),
            description=(
                "Set GDM AC idle timeout."
            ),
        ),

        _gsettings_action(
            user="Debian-gdm",
            key="sleep-inactive-battery-type",
            value=settings.gdm_battery_action,
            description=(
                "Disable GDM battery idle suspend."
            ),
        ),

        _gsettings_action(
            user="Debian-gdm",
            key="sleep-inactive-battery-timeout",
            value=str(
                settings.gdm_battery_timeout
            ),
            description=(
                "Set GDM battery idle timeout."
            ),
        ),
    ]

    return new_transaction(
        feature="headless",
        actions=actions,
    )
