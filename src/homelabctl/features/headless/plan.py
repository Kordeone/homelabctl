"""Build headless configuration plans."""

from __future__ import annotations

from homelabctl.core.models import (
    ChangeKind,
    ModuleActualState,
    RiskLevel,
)
from homelabctl.core.planner import (
    build_plan,
    make_step,
)
from homelabctl.features.headless.schema import (
    HeadlessSettings,
)
from homelabctl.template_engine import render_template


LOGIND_DROP_IN = (
    "/etc/systemd/logind.conf.d/"
    "10-homelab-headless.conf"
)


def render_logind_config(
    settings: HeadlessSettings,
) -> str:
    settings.validate()

    return render_template(
        "logind/10-homelab-headless.conf.j2",
        handle_lid_switch=(
            settings.handle_lid_switch
        ),
        handle_lid_switch_external_power=(
            settings.handle_lid_switch_external_power
        ),
        handle_lid_switch_docked=(
            settings.handle_lid_switch_docked
        ),
        idle_action=(
            settings.idle_action
        ),
    )


def build_headless_plan(
    *,
    actual: ModuleActualState | None,
    settings: HeadlessSettings,
):
    settings.validate()

    return build_plan(
        feature="headless",
        title="Configure headless operation",
        summary=(
            "Configure lid and idle behavior "
            "for unattended server operation."
        ),
        risk=RiskLevel.MEDIUM,
        steps=[
            make_step(
                step_id="write-logind-headless",
                description=(
                    "Write systemd-logind "
                    "headless policy."
                ),
                kind=ChangeKind.MODIFY_FILE,
                target=LOGIND_DROP_IN,
                after=render_logind_config(
                    settings
                ),
                requires_root=True,
                reversible=True,
            ),
            make_step(
                step_id="configure-user-power",
                description=(
                    "Disable desktop-user "
                    "idle suspend."
                ),
                kind=ChangeKind.RUN_COMMAND,
                requires_root=True,
                reversible=True,
            ),
            make_step(
                step_id="configure-gdm-power",
                description=(
                    "Disable GDM login-screen "
                    "idle suspend."
                ),
                kind=ChangeKind.RUN_COMMAND,
                requires_root=True,
                reversible=True,
            ),
        ],
        warnings=[
            (
                "The laptop will remain awake "
                "when the lid is closed."
            )
        ],
        requires_reboot=True,
    )
