"""Graphics configuration planning."""

from __future__ import annotations

from homelabctl.core.models import (
    ChangeKind,
    RiskLevel,
)
from homelabctl.core.planner import (
    build_plan,
    make_step,
)
from homelabctl.template_engine import render_template


NOUVEAU_CONFIG = (
    "/etc/modprobe.d/disable-nouveau.conf"
)


def render_nouveau_blacklist() -> str:
    return render_template(
        "modprobe/disable-nouveau.conf.j2"
    )


def build_disable_nouveau_plan():
    return build_plan(
        feature="graphics",
        title="Disable Nouveau",
        summary=(
            "Blacklist Nouveau and rebuild "
            "the initramfs."
        ),
        risk=RiskLevel.MEDIUM,
        steps=[
            make_step(
                step_id="write-nouveau-blacklist",
                description=(
                    "Write Nouveau blacklist."
                ),
                kind=ChangeKind.MODIFY_FILE,
                target=NOUVEAU_CONFIG,
                after=(
                    render_nouveau_blacklist()
                ),
                requires_root=True,
                reversible=True,
            ),
            make_step(
                step_id="rebuild-initramfs",
                description=(
                    "Rebuild initramfs."
                ),
                kind=ChangeKind.RUN_COMMAND,
                requires_root=True,
                reversible=True,
                command_preview=(
                    "update-initramfs -u"
                ),
            ),
        ],
        warnings=[
            (
                "A reboot is required before "
                "the driver change is fully active."
            )
        ],
        requires_reboot=True,
    )
