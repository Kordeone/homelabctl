"""Build SSH configuration change plans."""

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
from homelabctl.features.ssh.constants import (
    MANAGED_SSH_PATH,
)
from homelabctl.features.ssh.schema import SSHSettings
from homelabctl.template_engine import render_template


# Compatibility export used by existing callers.
# The canonical source of truth is constants.py.
SSH_DROP_IN = MANAGED_SSH_PATH


def render_config(
    settings: SSHSettings,
) -> str:
    settings.validate()

    return render_template(
        "ssh/00-homelabctl.conf.j2",
        port=settings.port,
        permit_root_login=(
            settings.permit_root_login
        ),
        pubkey_authentication=(
            settings.pubkey_authentication
        ),
        password_authentication=(
            settings.password_authentication
        ),
        kbd_interactive_authentication=(
            settings.kbd_interactive_authentication
        ),
        allow_users=settings.allow_users,
        allow_groups=settings.allow_groups,
        max_auth_tries=settings.max_auth_tries,
        client_alive_interval=(
            settings.client_alive_interval
        ),
        client_alive_count_max=(
            settings.client_alive_count_max
        ),
        x11_forwarding=(
            settings.x11_forwarding
        ),
        allow_tcp_forwarding=(
            settings.allow_tcp_forwarding
        ),
    )


def build_ssh_plan(
    *,
    actual: ModuleActualState | None,
    settings: SSHSettings,
):
    settings.validate()

    return build_plan(
        feature="ssh",
        title="Apply SSH configuration",
        summary=(
            "Apply the selected OpenSSH settings "
            "using the HomeLabCTL-managed drop-in."
        ),
        risk=RiskLevel.HIGH,
        steps=[
            make_step(
                step_id="write-ssh-config",
                description=(
                    "Write HomeLabCTL-managed "
                    "OpenSSH configuration."
                ),
                kind=ChangeKind.MODIFY_FILE,
                target=MANAGED_SSH_PATH,
                after=render_config(settings),
                requires_root=True,
                reversible=True,
            ),
            make_step(
                step_id="validate-sshd",
                description=(
                    "Validate OpenSSH configuration."
                ),
                kind=ChangeKind.RUN_COMMAND,
                target="sshd",
                requires_root=True,
                reversible=True,
                command_preview=(
                    "/usr/sbin/sshd -t"
                ),
            ),
            make_step(
                step_id="reload-ssh",
                description=(
                    "Reload OpenSSH service."
                ),
                kind=ChangeKind.RESTART_SERVICE,
                target="ssh.service",
                requires_root=True,
                reversible=True,
                command_preview=(
                    "systemctl reload ssh.service"
                ),
            ),
        ],
        warnings=[
            (
                "Incorrect SSH configuration can "
                "interrupt remote access."
            ),
            (
                "Public-key authentication should "
                "be verified before password login "
                "is disabled."
            ),
            (
                "Legacy SSH drop-ins are detected "
                "separately and are not automatically "
                "removed by this plan."
            ),
        ],
    )
