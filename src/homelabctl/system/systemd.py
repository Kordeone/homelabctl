"""Read-only systemd inspection helpers."""

from __future__ import annotations

from homelabctl.system.commands import CommandResult, run_command


def _systemctl(*args: str) -> CommandResult:
    return run_command(
        ["systemctl", *args],
        timeout=10.0,
    )


def unit_active_state(unit: str) -> str:
    result = _systemctl("is-active", unit)

    if result.stdout:
        return result.stdout

    return "unknown"


def unit_enabled_state(unit: str) -> str:
    result = _systemctl("is-enabled", unit)

    if result.stdout:
        return result.stdout

    return "unknown"


def unit_exists(unit: str) -> bool:
    result = _systemctl(
        "show",
        unit,
        "--property=LoadState",
        "--value",
    )

    return result.success and result.stdout not in {
        "",
        "not-found",
    }


def unit_property(
    unit: str,
    property_name: str,
) -> str | None:
    result = _systemctl(
        "show",
        unit,
        f"--property={property_name}",
        "--value",
    )

    if not result.success:
        return None

    return result.stdout or None


def unit_properties(
    unit: str,
    *property_names: str,
) -> dict[str, str]:
    if not property_names:
        return {}

    command = [
        "systemctl",
        "show",
        unit,
        "--no-pager",
    ]

    for name in property_names:
        command.append(f"--property={name}")

    result = run_command(command)

    if not result.success:
        return {}

    values: dict[str, str] = {}

    for line in result.stdout.splitlines():
        key, separator, value = line.partition("=")

        if separator:
            values[key] = value

    return values
