"""Read-only recent-change watcher for HomeLab managed files."""

from __future__ import annotations

import hashlib
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

from homelabctl.backend.collectors import CollectorResult
from homelabctl.core.actual_state import make_actual_state
from homelabctl.core.models import Status


WATCHED_PATHS = (
    # SSH
    "/etc/ssh/sshd_config",
    (
        "/etc/ssh/sshd_config.d/"
        "00-homelabctl.conf"
    ),

    # Firewall
    "/etc/nftables.conf",

    # Headless
    "/etc/systemd/logind.conf",
    (
        "/etc/systemd/logind.conf.d/"
        "10-homelab-headless.conf"
    ),

    # Power profile
    "/usr/local/sbin/homelab-power-mode",
    (
        "/etc/systemd/system/"
        "homelab-power-mode.service"
    ),
    (
        "/etc/udev/rules.d/"
        "80-homelab-power.rules"
    ),

    # Power guardian
    (
        "/usr/local/sbin/"
        "homelab-power-guardian"
    ),
    (
        "/etc/homelabctl/"
        "power-guardian.toml"
    ),
    (
        "/etc/systemd/system/"
        "homelab-power-guardian.service"
    ),
    (
        "/etc/systemd/system/"
        "homelab-power-guardian.timer"
    ),
)


def _now() -> str:
    return (
        datetime.now()
        .astimezone()
        .isoformat(
            timespec="seconds"
        )
    )


def _signature(
    path: Path,
) -> dict[str, Any]:
    try:
        stat = path.stat()

    except OSError:
        return {
            "exists": False,
        }

    result: dict[str, Any] = {
        "exists": True,
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
    }

    if (
        path.is_file()
        and stat.st_size <= 2_000_000
    ):
        try:
            digest = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()

            result["sha256"] = digest

        except OSError:
            pass

    return result


class FileWatchCollector:
    name = "file_watch"

    def __init__(
        self,
    ) -> None:
        self._baseline: dict[
            str,
            dict[str, Any],
        ] = {}

        self._events: deque[
            dict[str, str]
        ] = deque(
            maxlen=40
        )

        self._initialized = False

    def collect(
        self,
    ) -> CollectorResult:
        current = {
            raw: _signature(
                Path(raw)
            )
            for raw in WATCHED_PATHS
        }

        if not self._initialized:
            self._baseline = current
            self._initialized = True

        else:
            for raw in WATCHED_PATHS:
                before = (
                    self._baseline.get(
                        raw,
                        {
                            "exists": False,
                        },
                    )
                )

                after = current[
                    raw
                ]

                event: str | None = None

                if (
                    not before.get(
                        "exists"
                    )
                    and after.get(
                        "exists"
                    )
                ):
                    event = "created"

                elif (
                    before.get(
                        "exists"
                    )
                    and not after.get(
                        "exists"
                    )
                ):
                    event = "deleted"

                elif (
                    before.get(
                        "exists"
                    )
                    and after.get(
                        "exists"
                    )
                    and before != after
                ):
                    event = "modified"

                if event:
                    self._events.appendleft(
                        {
                            "time": _now(),
                            "path": raw,
                            "event": event,
                        }
                    )

            self._baseline = current

        existing_count = sum(
            1
            for value in current.values()
            if value.get(
                "exists"
            )
        )

        state = make_actual_state(
            "file_watch",
            status=Status.PASS,
            summary=(
                "HomeLab managed-file watcher active."
            ),
            values={
                "watched_count": (
                    len(WATCHED_PATHS)
                ),
                "existing_count": (
                    existing_count
                ),
                "changed_files": (
                    list(self._events)
                ),
            },
        )

        return CollectorResult(
            modules=[state]
        )
