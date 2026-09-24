"""Secure Boot, kernel lockdown and TPM collector."""

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
from homelabctl.system.files import read_text


class SecurityCollector:
    name = "security"

    def collect(self) -> CollectorResult:
        secure_boot = self._secure_boot()
        lockdown = self._lockdown()
        tpm_present = (
            Path("/dev/tpm0").exists()
            or Path("/dev/tpmrm0").exists()
        )

        values = {
            "secure_boot": secure_boot,
            "kernel_lockdown": lockdown,
            "tpm_present": tpm_present,
            "tpm0_present": Path(
                "/dev/tpm0"
            ).exists(),
            "tpmrm0_present": Path(
                "/dev/tpmrm0"
            ).exists(),
        }

        state = make_actual_state(
            "security",
            status=Status.PASS,
            summary="Platform security capabilities collected.",
            values=values,
        )

        capabilities = [
            CapabilityResult(
                key="security.tpm",
                name="TPM",
                state=(
                    CapabilityState.AVAILABLE
                    if tpm_present
                    else CapabilityState.UNAVAILABLE
                ),
                reason=(
                    None
                    if tpm_present
                    else "No TPM character device was found."
                ),
            ),
            CapabilityResult(
                key="security.secure_boot",
                name="Secure Boot",
                state=(
                    CapabilityState.AVAILABLE
                    if secure_boot is True
                    else CapabilityState.UNAVAILABLE
                    if secure_boot is False
                    else CapabilityState.UNKNOWN
                ),
                reason=(
                    None
                    if secure_boot is not None
                    else "Secure Boot state could not be determined."
                ),
            ),
        ]

        return CollectorResult(
            modules=[state],
            capabilities=capabilities,
        )

    def _secure_boot(self) -> bool | None:
        executable = shutil.which("mokutil")

        if not executable:
            return None

        result = run_command(
            [executable, "--sb-state"],
            timeout=5.0,
        )

        text = (
            result.stdout + "\n" + result.stderr
        ).lower()

        if "secureboot enabled" in text:
            return True

        if "secureboot disabled" in text:
            return False

        return None

    def _lockdown(self) -> str | None:
        content = read_text(
            "/sys/kernel/security/lockdown"
        )

        if not content:
            return None

        for token in content.strip().split():
            if token.startswith("[") and token.endswith("]"):
                return token[1:-1]

        return content.strip()
