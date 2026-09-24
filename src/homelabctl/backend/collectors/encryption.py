"""Disk encryption and Clevis inspection."""

from __future__ import annotations

import json
import shutil

from homelabctl.backend.collectors import CollectorResult
from homelabctl.core.actual_state import make_actual_state
from homelabctl.core.models import (
    CapabilityResult,
    CapabilityState,
    Status,
)
from homelabctl.system.commands import run_command


class EncryptionCollector:
    name = "encryption"

    def collect(self) -> CollectorResult:
        devices = self._lsblk()

        luks_devices = [
            item
            for item in self._walk(devices)
            if item.get("fstype") == "crypto_LUKS"
        ]

        values = {
            "luks_present": bool(luks_devices),
            "luks_device_count": len(luks_devices),
            "luks_devices": [
                {
                    "name": item.get("name"),
                    "path": item.get("path"),
                    "uuid": item.get("uuid"),
                }
                for item in luks_devices
            ],
            "cryptsetup_available": (
                shutil.which("cryptsetup") is not None
            ),
            "clevis_available": (
                shutil.which("clevis") is not None
            ),
        }

        state = make_actual_state(
            "encryption",
            status=(
                Status.PASS
                if luks_devices
                else Status.NOT_CONFIGURED
            ),
            summary="Disk encryption state collected.",
            values=values,
        )

        capabilities = [
            CapabilityResult(
                key="encryption.luks",
                name="LUKS encryption",
                state=(
                    CapabilityState.AVAILABLE
                    if luks_devices
                    else CapabilityState.UNAVAILABLE
                ),
                reason=(
                    None
                    if luks_devices
                    else "No LUKS block device was detected."
                ),
            )
        ]

        return CollectorResult(
            modules=[state],
            capabilities=capabilities,
        )

    def _lsblk(self) -> list[dict]:
        result = run_command(
            [
                "lsblk",
                "-J",
                "-o",
                "NAME,PATH,TYPE,FSTYPE,UUID,MOUNTPOINTS",
            ],
            timeout=10.0,
        )

        if not result.success:
            return []

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []

        devices = data.get("blockdevices", [])

        return (
            devices
            if isinstance(devices, list)
            else []
        )

    def _walk(
        self,
        devices: list[dict],
    ):
        for device in devices:
            yield device

            children = device.get("children", [])

            if isinstance(children, list):
                yield from self._walk(children)
