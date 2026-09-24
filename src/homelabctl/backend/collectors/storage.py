"""Storage-device collector."""

from __future__ import annotations

import json

from homelabctl.backend.collectors import CollectorResult
from homelabctl.core.actual_state import make_actual_state
from homelabctl.core.models import Status
from homelabctl.system.commands import run_command


class StorageCollector:
    name = "storage"

    def collect(self) -> CollectorResult:
        result = run_command(
            [
                "lsblk",
                "-J",
                "-b",
                "-o",
                (
                    "NAME,PATH,TYPE,SIZE,FSTYPE,"
                    "UUID,MOUNTPOINTS,MODEL,SERIAL"
                ),
            ],
            timeout=10.0,
        )

        devices: list[dict] = []

        if result.success:
            try:
                parsed = json.loads(result.stdout)
                raw_devices = parsed.get(
                    "blockdevices",
                    [],
                )

                if isinstance(raw_devices, list):
                    devices = raw_devices
            except json.JSONDecodeError:
                pass

        state = make_actual_state(
            "storage",
            status=(
                Status.PASS
                if devices
                else Status.WARNING
            ),
            summary="Block-device inventory collected.",
            values={
                "devices": devices,
                "device_count": len(devices),
            },
        )

        return CollectorResult(modules=[state])
