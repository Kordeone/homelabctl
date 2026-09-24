"""Network state collector."""

from __future__ import annotations

import json

from homelabctl.backend.collectors import CollectorResult
from homelabctl.core.actual_state import make_actual_state
from homelabctl.core.models import Status
from homelabctl.system.commands import run_command


class NetworkCollector:
    name = "network"

    def collect(self) -> CollectorResult:
        links = self._json_command(
            ["ip", "-j", "link", "show"]
        )

        addresses = self._json_command(
            ["ip", "-j", "address", "show"]
        )

        routes = self._json_command(
            ["ip", "-j", "route", "show"]
        )

        interfaces = []

        for link in links:
            interfaces.append(
                {
                    "name": link.get("ifname"),
                    "state": link.get("operstate"),
                    "mtu": link.get("mtu"),
                    "mac": link.get("address"),
                }
            )

        default_routes = [
            route
            for route in routes
            if route.get("dst") == "default"
        ]

        state = make_actual_state(
            "network",
            status=Status.PASS,
            summary="Network interface and routing state collected.",
            values={
                "interfaces": interfaces,
                "addresses": addresses,
                "default_routes": default_routes,
            },
        )

        return CollectorResult(modules=[state])

    def _json_command(
        self,
        command: list[str],
    ) -> list[dict]:
        result = run_command(
            command,
            timeout=10.0,
        )

        if not result.success:
            return []

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []

        return data if isinstance(data, list) else []
