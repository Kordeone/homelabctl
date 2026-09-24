"""Automatic power-profile feature planning."""

from __future__ import annotations

from homelabctl.core.models import (
    ChangeKind,
    RiskLevel,
)
from homelabctl.core.planner import (
    build_plan,
    make_step,
)
from homelabctl.features.power_profile.inspect import (
    PowerProfilePolicy,
)
from homelabctl.template_engine import render_template


SCRIPT_PATH = (
    "/usr/local/sbin/homelab-power-mode"
)

SERVICE_PATH = (
    "/etc/systemd/system/"
    "homelab-power-mode.service"
)

UDEV_RULE_PATH = (
    "/etc/udev/rules.d/"
    "80-homelab-power.rules"
)


def render_runtime_script(
    policy: PowerProfilePolicy,
) -> str:
    policy.validate()

    return render_template(
        "power/power-mode.py.j2",
        ac_profile=policy.ac_profile,
        battery_profile=(
            policy.battery_profile
        ),
    )


def render_service() -> str:
    return render_template(
        "systemd/homelab-power-mode.service.j2"
    )


def render_udev_rule() -> str:
    return render_template(
        "udev/80-homelab-power.rules.j2"
    )


def build_power_profile_plan(
    policy: PowerProfilePolicy,
):
    policy.validate()

    return build_plan(
        feature="power_profile",
        title="Automatic power profiles",
        summary=(
            "Install an optional independent "
            "AC/battery power-profile service."
        ),
        risk=RiskLevel.LOW,
        steps=[
            make_step(
                step_id="install-power-script",
                description=(
                    "Install power-profile runtime."
                ),
                kind=ChangeKind.CREATE_FILE,
                target=SCRIPT_PATH,
                after=render_runtime_script(
                    policy
                ),
                requires_root=True,
                reversible=True,
            ),
            make_step(
                step_id="install-power-service",
                description=(
                    "Install power-profile service."
                ),
                kind=ChangeKind.CREATE_FILE,
                target=SERVICE_PATH,
                after=render_service(),
                requires_root=True,
                reversible=True,
            ),
            make_step(
                step_id="install-power-udev",
                description=(
                    "Install AC-state udev rule."
                ),
                kind=ChangeKind.CREATE_FILE,
                target=UDEV_RULE_PATH,
                after=render_udev_rule(),
                requires_root=True,
                reversible=True,
            ),
        ],
    )
