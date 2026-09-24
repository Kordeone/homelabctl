"""Power Guardian installation planning."""

from __future__ import annotations

from homelabctl.core.models import (
    ChangeKind,
    RiskLevel,
)
from homelabctl.core.planner import (
    build_plan,
    make_step,
)
from homelabctl.features.power_guardian.config import (
    PowerGuardianConfig,
)
from homelabctl.template_engine import render_template


SCRIPT_PATH = (
    "/usr/local/sbin/homelab-power-guardian"
)

CONFIG_PATH = (
    "/etc/homelabctl/power-guardian.toml"
)

SERVICE_PATH = (
    "/etc/systemd/system/"
    "homelab-power-guardian.service"
)

TIMER_PATH = (
    "/etc/systemd/system/"
    "homelab-power-guardian.timer"
)


def render_config(
    config: PowerGuardianConfig,
) -> str:
    config.validate()

    return render_template(
        "power/power-guardian.toml.j2",
        enabled=config.enabled,
        warning_percent=(
            config.warning_percent
        ),
        low_percent=(
            config.low_percent
        ),
        critical_percent=(
            config.critical_percent
        ),
        suspend_cycle_seconds=(
            config.suspend_cycle_seconds
        ),
        shutdown_rtc_seconds=(
            config.shutdown_rtc_seconds
        ),
        suspend_on_low=(
            config.suspend_on_low
        ),
        shutdown_on_critical=(
            config.shutdown_on_critical
        ),
    )


def render_service() -> str:
    return render_template(
        "systemd/"
        "homelab-power-guardian.service.j2"
    )


def render_timer() -> str:
    return render_template(
        "systemd/"
        "homelab-power-guardian.timer.j2"
    )


def build_power_guardian_plan(
    config: PowerGuardianConfig,
):
    config.validate()

    return build_plan(
        feature="power_guardian",
        title="Install Power Guardian",
        summary=(
            "Install the optional independent "
            "battery outage guardian."
        ),
        risk=RiskLevel.HIGH,
        steps=[
            make_step(
                step_id="install-guardian-runtime",
                description=(
                    "Install Power Guardian runtime."
                ),
                kind=ChangeKind.CREATE_FILE,
                target=SCRIPT_PATH,
                requires_root=True,
                reversible=True,
            ),
            make_step(
                step_id="install-guardian-config",
                description=(
                    "Install selected guardian policy."
                ),
                kind=ChangeKind.CREATE_FILE,
                target=CONFIG_PATH,
                after=render_config(config),
                requires_root=True,
                reversible=True,
            ),
            make_step(
                step_id="install-guardian-service",
                description=(
                    "Install Power Guardian service."
                ),
                kind=ChangeKind.CREATE_FILE,
                target=SERVICE_PATH,
                after=render_service(),
                requires_root=True,
                reversible=True,
            ),
            make_step(
                step_id="install-guardian-timer",
                description=(
                    "Install Power Guardian timer."
                ),
                kind=ChangeKind.CREATE_FILE,
                target=TIMER_PATH,
                after=render_timer(),
                requires_root=True,
                reversible=True,
            ),
        ],
        warnings=[
            (
                "When enabled, Power Guardian "
                "may suspend or power off the host."
            ),
            (
                "RTC wake capability must be "
                "verified before unattended use."
            ),
        ],
    )
