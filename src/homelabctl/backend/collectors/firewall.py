"""nftables firewall collector."""

from __future__ import annotations

import shutil

from homelabctl.backend.collectors import CollectorResult
from homelabctl.core.actual_state import make_actual_state
from homelabctl.core.models import Status
from homelabctl.system.commands import run_command
from homelabctl.system.systemd import (
    unit_active_state,
    unit_enabled_state,
    unit_exists,
)


class FirewallCollector:
    name = "firewall"

    def collect(self) -> CollectorResult:
        nft_available = shutil.which("nft") is not None
        service_exists = unit_exists("nftables.service")

        ruleset = ""

        if nft_available:
            result = run_command(
                ["nft", "list", "ruleset"],
                timeout=10.0,
            )

            if result.success:
                ruleset = result.stdout

        values = {
            "nft_available": nft_available,
            "service_exists": service_exists,
            "service_active": (
                unit_active_state("nftables.service")
                if service_exists
                else "not-found"
            ),
            "service_enabled": (
                unit_enabled_state("nftables.service")
                if service_exists
                else "not-found"
            ),
            "ruleset_present": bool(ruleset.strip()),
            "inet_filter_table": (
                "table inet filter" in ruleset
            ),
            "input_policy_drop": (
                "hook input" in ruleset
                and "policy drop" in ruleset
            ),
            "forward_policy_drop": (
                "hook forward" in ruleset
                and "policy drop" in ruleset
            ),
        }

        status = (
            Status.PASS
            if nft_available and bool(ruleset.strip())
            else Status.WARNING
        )

        state = make_actual_state(
            "firewall",
            status=status,
            summary="nftables firewall state collected.",
            values=values,
        )

        return CollectorResult(modules=[state])
