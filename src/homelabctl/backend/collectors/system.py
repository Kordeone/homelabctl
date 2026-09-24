"""Basic host/system state collector."""

from __future__ import annotations

import os
import platform
import shutil
import socket
import sys
from pathlib import Path

from homelabctl.backend.collectors import CollectorResult
from homelabctl.core.actual_state import make_actual_state
from homelabctl.core.models import Status


def _read_os_release() -> dict[str, str]:
    path = Path("/etc/os-release")

    result: dict[str, str] = {}

    try:
        content = path.read_text(
            encoding="utf-8"
        )
    except OSError:
        return result

    for line in content.splitlines():
        if "=" not in line:
            continue

        key, value = line.split(
            "=",
            1,
        )

        result[key] = (
            value.strip().strip('"')
        )

    return result


def _uptime_seconds() -> float | None:
    try:
        content = Path(
            "/proc/uptime"
        ).read_text().strip()

        return float(
            content.split()[0]
        )

    except (
        OSError,
        ValueError,
        IndexError,
    ):
        return None


def _memory() -> dict[str, int | float | None]:
    values: dict[str, int] = {}

    try:
        content = Path(
            "/proc/meminfo"
        ).read_text(
            encoding="utf-8"
        )

    except OSError:
        return {
            "total": None,
            "available": None,
            "used": None,
            "percent": None,
        }

    for line in content.splitlines():
        if ":" not in line:
            continue

        key, raw = line.split(
            ":",
            1,
        )

        fields = raw.strip().split()

        if not fields:
            continue

        try:
            value = int(
                fields[0]
            )
        except ValueError:
            continue

        # /proc/meminfo is normally KiB.
        values[key] = value * 1024

    total = values.get(
        "MemTotal"
    )

    available = values.get(
        "MemAvailable"
    )

    if total is None:
        used = None
        percent = None
    else:
        used = (
            total - available
            if available is not None
            else None
        )

        percent = (
            round(
                used / total * 100,
                1,
            )
            if (
                used is not None
                and total
            )
            else None
        )

    return {
        "total": total,
        "available": available,
        "used": used,
        "percent": percent,
    }


class SystemCollector:
    name = "system"

    def collect(
        self,
    ) -> CollectorResult:
        os_release = (
            _read_os_release()
        )

        memory = _memory()

        try:
            load_1, load_5, load_15 = (
                os.getloadavg()
            )
        except OSError:
            load_1 = load_5 = load_15 = None

        try:
            disk = shutil.disk_usage(
                "/"
            )

            root_total = disk.total
            root_used = disk.used
            root_free = disk.free

            root_percent = round(
                root_used
                / root_total
                * 100,
                1,
            )

        except OSError:
            root_total = None
            root_used = None
            root_free = None
            root_percent = None

        state = make_actual_state(
            "system",
            status=Status.PASS,
            summary=(
                "Basic system information collected."
            ),
            values={
                "hostname": (
                    socket.gethostname()
                ),
                "kernel": (
                    platform.release()
                ),
                "architecture": (
                    platform.machine()
                ),
                "python_version": (
                    platform.python_version()
                ),
                "os_name": (
                    os_release.get(
                        "PRETTY_NAME"
                    )
                    or platform.platform()
                ),
                "os_id": (
                    os_release.get(
                        "ID"
                    )
                ),
                "os_version": (
                    os_release.get(
                        "VERSION_ID"
                    )
                ),
                "uptime_seconds": (
                    _uptime_seconds()
                ),
                "load_1": load_1,
                "load_5": load_5,
                "load_15": load_15,
                "memory_total_bytes": (
                    memory["total"]
                ),
                "memory_available_bytes": (
                    memory["available"]
                ),
                "memory_used_bytes": (
                    memory["used"]
                ),
                "memory_used_percent": (
                    memory["percent"]
                ),
                "root_total_bytes": (
                    root_total
                ),
                "root_used_bytes": (
                    root_used
                ),
                "root_free_bytes": (
                    root_free
                ),
                "root_used_percent": (
                    root_percent
                ),
                "effective_uid": (
                    os.geteuid()
                ),
            },
        )

        return CollectorResult(
            modules=[state]
        )
