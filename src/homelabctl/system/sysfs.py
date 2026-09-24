"""Linux sysfs inspection helpers."""

from __future__ import annotations

from pathlib import Path

from homelabctl.system.files import (
    list_directory,
    read_first_line,
    read_int,
)


SYSFS_ROOT = Path("/sys")


def sysfs_path(relative_path: str) -> Path:
    return SYSFS_ROOT / relative_path.lstrip("/")


def read_value(
    relative_path: str,
    *,
    default: str | None = None,
) -> str | None:
    return read_first_line(
        sysfs_path(relative_path),
        default=default,
    )


def read_integer(
    relative_path: str,
    *,
    default: int | None = None,
) -> int | None:
    return read_int(
        sysfs_path(relative_path),
        default=default,
    )


def power_supplies() -> list[Path]:
    return list_directory(
        SYSFS_ROOT / "class/power_supply"
    )


def network_interfaces() -> list[Path]:
    return list_directory(
        SYSFS_ROOT / "class/net"
    )
