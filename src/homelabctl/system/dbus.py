"""Helpers for read-only D-Bus and GSettings inspection."""

from __future__ import annotations

from homelabctl.system.commands import CommandResult, run_command


def gsettings_get(
    schema: str,
    key: str,
    *,
    user: str | None = None,
) -> CommandResult:
    command = [
        "gsettings",
        "get",
        schema,
        key,
    ]

    if user is None:
        return run_command(command)

    return run_command(
        [
            "sudo",
            "-n",
            "-u",
            user,
            "-H",
            "dbus-run-session",
            *command,
        ],
        timeout=10.0,
    )


def parse_gsettings_string(value: str) -> str:
    value = value.strip()

    if len(value) >= 2:
        if value[0] == value[-1] and value[0] in {"'", '"'}:
            return value[1:-1]

    return value
