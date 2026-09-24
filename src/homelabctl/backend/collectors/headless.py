"""Headless and sleep-policy collector."""

from __future__ import annotations

import re

from homelabctl.backend.collectors import CollectorResult
from homelabctl.core.actual_state import make_actual_state
from homelabctl.core.models import Status
from homelabctl.system.commands import run_command


POWER_SCHEMA = (
    "org.gnome.settings-daemon.plugins.power"
)


class HeadlessCollector:
    name = "headless"

    def collect(self) -> CollectorResult:
        logind = self._logind_config()

        values: dict[str, object] = {
            "lid_switch": logind.get(
                "HandleLidSwitch"
            ),
            "lid_switch_external_power": logind.get(
                "HandleLidSwitchExternalPower"
            ),
            "lid_switch_docked": logind.get(
                "HandleLidSwitchDocked"
            ),
            "idle_action": logind.get(
                "IdleAction"
            ),
        }

        values.update(
            self._gsettings_for_user(
                "Debian-gdm",
                prefix="gdm",
            )
        )

        status = self._status(values)

        state = make_actual_state(
            "headless",
            status=status,
            summary="Headless, lid and login-screen power policy.",
            values=values,
        )

        return CollectorResult(modules=[state])

    def _logind_config(self) -> dict[str, str]:
        result = run_command(
            [
                "systemd-analyze",
                "cat-config",
                "systemd/logind.conf",
            ],
            timeout=10.0,
        )

        if not result.success:
            return {}

        values: dict[str, str] = {}

        for raw_line in result.stdout.splitlines():
            line = raw_line.strip()

            if (
                not line
                or line.startswith("#")
                or line.startswith("[")
                or "=" not in line
            ):
                continue

            key, value = line.split("=", 1)

            if re.fullmatch(
                r"[A-Za-z][A-Za-z0-9]*",
                key.strip(),
            ):
                values[key.strip()] = value.strip()

        return values

    def _gsettings_for_user(
        self,
        username: str,
        *,
        prefix: str,
    ) -> dict[str, object]:
        keys = (
            "sleep-inactive-ac-type",
            "sleep-inactive-ac-timeout",
            "sleep-inactive-battery-type",
            "sleep-inactive-battery-timeout",
        )

        values: dict[str, object] = {}

        for key in keys:
            result = run_command(
                [
                    "/usr/sbin/runuser",
                    "-u",
                    username,
                    "--",
                    "dbus-run-session",
                    "gsettings",
                    "get",
                    POWER_SCHEMA,
                    key,
                ],
                timeout=10.0,
            )

            normalized = (
                key.replace("-", "_")
            )

            output = (
                result.stdout.strip()
                if result.success
                else None
            )

            if output and (
                output.startswith("'")
                and output.endswith("'")
            ):
                output = output[1:-1]

            if output is not None:
                try:
                    output = int(output)
                except ValueError:
                    pass

            values[f"{prefix}_{normalized}"] = output

        return values

    def _status(
        self,
        values: dict[str, object],
    ) -> Status:
        expected = {
            "lid_switch": "ignore",
            "lid_switch_external_power": "ignore",
            "lid_switch_docked": "ignore",
            "idle_action": "ignore",
            "gdm_sleep_inactive_ac_type": "nothing",
            "gdm_sleep_inactive_battery_type": "nothing",
        }

        for key, expected_value in expected.items():
            if values.get(key) != expected_value:
                return Status.WARNING

        return Status.PASS
