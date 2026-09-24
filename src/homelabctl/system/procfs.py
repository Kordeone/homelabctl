"""Linux procfs inspection helpers."""

from __future__ import annotations

from pathlib import Path

from homelabctl.system.files import read_text


PROCFS_ROOT = Path("/proc")


def proc_path(relative_path: str) -> Path:
    return PROCFS_ROOT / relative_path.lstrip("/")


def read_proc(
    relative_path: str,
    *,
    default: str | None = None,
) -> str | None:
    return read_text(
        proc_path(relative_path),
        default=default,
    )


def uptime_seconds() -> float | None:
    content = read_proc("uptime")

    if not content:
        return None

    try:
        return float(content.split()[0])
    except (ValueError, IndexError):
        return None


def kernel_command_line() -> str | None:
    content = read_proc("cmdline")

    if content is None:
        return None

    return content.strip()
