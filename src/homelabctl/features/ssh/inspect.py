"""Interpret SSH state reported by homelabd."""

from __future__ import annotations

from homelabctl.core.drift import compare_module_state
from homelabctl.core.models import (
    ModuleActualState,
    ModuleDesiredState,
    Status,
)
from homelabctl.features.ssh.schema import SSHSettings


def desired_state(
    settings: SSHSettings,
) -> ModuleDesiredState:
    settings.validate()

    state = ModuleDesiredState(
        module="ssh"
    )

    state.settings = {
        "port": _setting(
            "port",
            settings.port,
        ),
        "permit_root_login": _setting(
            "permit_root_login",
            settings.permit_root_login,
        ),
        "password_authentication": _setting(
            "password_authentication",
            settings.password_authentication,
        ),
        "pubkey_authentication": _setting(
            "pubkey_authentication",
            settings.pubkey_authentication,
        ),
        "kbd_interactive_authentication": _setting(
            "kbd_interactive_authentication",
            settings.kbd_interactive_authentication,
        ),
        "allow_users": _setting(
            "allow_users",
            list(settings.allow_users),
        ),
        "allow_groups": _setting(
            "allow_groups",
            list(settings.allow_groups),
        ),
        "max_auth_tries": _setting(
            "max_auth_tries",
            settings.max_auth_tries,
        ),
        "client_alive_interval": _setting(
            "client_alive_interval",
            settings.client_alive_interval,
        ),
        "client_alive_count_max": _setting(
            "client_alive_count_max",
            settings.client_alive_count_max,
        ),
        "x11_forwarding": _setting(
            "x11_forwarding",
            settings.x11_forwarding,
        ),
        "allow_tcp_forwarding": _setting(
            "allow_tcp_forwarding",
            settings.allow_tcp_forwarding,
        ),
    }

    return state


def evaluate(
    actual: ModuleActualState | None,
    settings: SSHSettings,
) -> Status:
    report = compare_module_state(
        desired_state(settings),
        actual,
    )

    return report.status


def _setting(
    key: str,
    value: object,
):
    from homelabctl.core.models import DesiredSetting

    return DesiredSetting(
        key=key,
        value=value,
    )
