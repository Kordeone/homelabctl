"""Power Guardian configuration model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PowerGuardianConfig:
    enabled: bool = False

    warning_percent: int = 30
    low_percent: int = 20
    critical_percent: int = 15

    suspend_cycle_seconds: int = 300
    shutdown_rtc_seconds: int = 900

    suspend_on_low: bool = True
    shutdown_on_critical: bool = True

    def validate(self) -> None:
        thresholds = (
            self.warning_percent,
            self.low_percent,
            self.critical_percent,
        )

        if any(
            value < 1 or value > 100
            for value in thresholds
        ):
            raise ValueError(
                "Battery thresholds must be between 1 and 100."
            )

        if not (
            self.warning_percent
            > self.low_percent
            > self.critical_percent
        ):
            raise ValueError(
                "Thresholds must satisfy: "
                "warning > low > critical."
            )

        if self.suspend_cycle_seconds < 60:
            raise ValueError(
                "Suspend cycle must be at least 60 seconds."
            )

        if self.shutdown_rtc_seconds < 60:
            raise ValueError(
                "Shutdown RTC interval must be at least 60 seconds."
            )
