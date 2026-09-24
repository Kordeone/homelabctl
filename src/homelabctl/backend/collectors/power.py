"""Power, battery and sleep capability collector."""

from __future__ import annotations

import shutil
from pathlib import Path

from homelabctl.backend.collectors import CollectorResult
from homelabctl.core.actual_state import make_actual_state
from homelabctl.core.models import (
    CapabilityResult,
    CapabilityState,
    Status,
)
from homelabctl.system.commands import run_command
from homelabctl.system.files import (
    read_first_line,
    read_int,
)


class PowerCollector:
    name = "power"

    def collect(self) -> CollectorResult:
        battery = self._battery()
        ac = self._ac_adapter()
        profile = self._power_profile()
        sleep_modes = self._sleep_modes()

        values = {
            **battery,
            **ac,
            "power_profile": profile,
            **sleep_modes,
            "can_hibernate": self._login1_capability(
                "CanHibernate"
            ),
            "can_suspend": self._login1_capability(
                "CanSuspend"
            ),
            "can_suspend_then_hibernate":
                self._login1_capability(
                    "CanSuspendThenHibernate"
                ),
        }

        state = make_actual_state(
            "power",
            status=Status.PASS,
            summary="Power and sleep state collected.",
            values=values,
        )

        capabilities = [
            CapabilityResult(
                key="power.deep_suspend",
                name="Deep suspend",
                state=(
                    CapabilityState.AVAILABLE
                    if values.get("deep_sleep_available")
                    else CapabilityState.UNAVAILABLE
                ),
            ),
            CapabilityResult(
                key="power.hibernate",
                name="Hibernate",
                state=self._capability_state(
                    values.get("can_hibernate")
                ),
                reason=(
                    None
                    if values.get("can_hibernate") == "yes"
                    else (
                        "systemd-logind reports "
                        f"{values.get('can_hibernate')!r}."
                    )
                ),
            ),
        ]

        return CollectorResult(
            modules=[state],
            capabilities=capabilities,
        )

    def _battery(self) -> dict[str, object]:
        base = Path("/sys/class/power_supply")

        for path in base.glob("BAT*"):
            return {
                "battery_name": path.name,
                "battery_capacity": read_int(
                    path / "capacity"
                ),
                "battery_status": read_first_line(
                    path / "status"
                ),
            }

        return {
            "battery_name": None,
            "battery_capacity": None,
            "battery_status": None,
        }

    def _ac_adapter(self) -> dict[str, object]:
        base = Path("/sys/class/power_supply")

        for path in base.iterdir():
            supply_type = read_first_line(
                path / "type"
            )

            if supply_type in {
                "Mains",
                "USB",
                "USB_C",
            }:
                online = read_int(
                    path / "online"
                )

                return {
                    "ac_name": path.name,
                    "ac_online": (
                        bool(online)
                        if online is not None
                        else None
                    ),
                }

        return {
            "ac_name": None,
            "ac_online": None,
        }

    def _power_profile(self) -> str | None:
        executable = shutil.which(
            "powerprofilesctl"
        )

        if not executable:
            return None

        result = run_command(
            [executable, "get"]
        )

        return (
            result.stdout.strip()
            if result.success
            else None
        )

    def _sleep_modes(self) -> dict[str, object]:
        content = read_first_line(
            "/sys/power/mem_sleep"
        )

        if not content:
            return {
                "mem_sleep": None,
                "active_mem_sleep": None,
                "deep_sleep_available": False,
            }

        active = None

        for token in content.split():
            if token.startswith("[") and token.endswith("]"):
                active = token[1:-1]

        return {
            "mem_sleep": content,
            "active_mem_sleep": active,
            "deep_sleep_available": (
                "deep" in content.split()
                or "[deep]" in content
            ),
        }

    def _login1_capability(
        self,
        method: str,
    ) -> str | None:
        result = run_command(
            [
                "busctl",
                "call",
                "org.freedesktop.login1",
                "/org/freedesktop/login1",
                "org.freedesktop.login1.Manager",
                method,
            ],
            timeout=5.0,
        )

        if not result.success:
            return None

        output = result.stdout.strip()

        if '"' in output:
            parts = output.split('"')

            if len(parts) >= 2:
                return parts[1]

        return output or None

    def _capability_state(
        self,
        value: object,
    ) -> CapabilityState:
        if value == "yes":
            return CapabilityState.AVAILABLE

        if value in {
            "no",
            "na",
            "challenge",
        }:
            return CapabilityState.UNAVAILABLE

        return CapabilityState.UNKNOWN
