"""One-shot privileged HomeLabCTL apply runner.

This program is never a daemon.

It accepts only a narrow set of known HomeLabCTL operations.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from homelabctl.apply.backup import (
    BackupRecord,
    backup_file,
    write_manifest,
)
from homelabctl.apply.rollback import (
    restore_transaction_files,
)
from homelabctl.apply.firewall_safety import (
    arm_firewall_rollback,
    cancel_firewall_rollback,
    clear_firewall_rollback_state,
    firewall_safety_lock,
    load_pending_firewall_rollback,
    validate_transaction_id as validate_firewall_transaction_id,
    verify_firewall_for_confirmation,
)

from homelabctl.apply.ssh_safety import (
    arm_ssh_rollback,
    cancel_ssh_rollback,
    clear_ssh_rollback_state,
    load_pending_ssh_rollback,
    ssh_safety_lock,
    validate_transaction_id,
    verify_ssh_for_confirmation,
)
from homelabctl.apply.transaction import (
    ActionType,
    ApplyAction,
    ApplyTransaction,
    transaction_from_dict,
)


SAFE_TARGETS = {
    "ssh": {
        (
            "/etc/ssh/sshd_config.d/"
            "00-homelabctl.conf"
        ),
    },

    "firewall": {
        "/etc/nftables.conf",
    },

    "headless": {
        (
            "/etc/systemd/logind.conf.d/"
            "10-homelab-headless.conf"
        ),
    },

    "graphics": {
        (
            "/etc/modprobe.d/"
            "disable-nouveau.conf"
        ),
    },

    "power_profile": {
        "/usr/local/sbin/homelab-power-mode",
        (
            "/etc/systemd/system/"
            "homelab-power-mode.service"
        ),
        (
            "/etc/udev/rules.d/"
            "80-homelab-power.rules"
        ),
    },

    "power_guardian": {
        (
            "/usr/local/sbin/"
            "homelab-power-guardian"
        ),
        (
            "/etc/homelabctl/"
            "power-guardian.toml"
        ),
        (
            "/etc/systemd/system/"
            "homelab-power-guardian.service"
        ),
        (
            "/etc/systemd/system/"
            "homelab-power-guardian.timer"
        ),
    },
}


SAFE_SYSTEMD_UNITS = {
    "ssh": {
        "ssh.service",
        "sshd.service",
    },

    "firewall": {
        "nftables.service",
    },

    "power_profile": {
        "homelab-power-mode.service",
    },

    "power_guardian": {
        "homelab-power-guardian.service",
        "homelab-power-guardian.timer",
    },
}


ALLOWED_SYSTEMCTL_OPERATIONS = {
    "start",
    "stop",
    "restart",
    "reload",
    "enable",
    "disable",
    "reenable",
    "enable-now",
    "disable-now",
    "daemon-reload",
}


USERNAME_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_-]*[$]?$"
)

SESSION_ID_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$"
)


def require_root() -> None:
    if os.geteuid() != 0:
        raise PermissionError(
            "homelabctl-apply must run as root."
        )


def validate_target(
    feature: str,
    target: str | None,
) -> None:
    if not target:
        raise ValueError(
            "A managed file target is required."
        )

    allowed = SAFE_TARGETS.get(
        feature,
        set(),
    )

    if target not in allowed:
        raise PermissionError(
            f"Target is not allowed for "
            f"feature {feature!r}: {target}"
        )


def validate_run_command(
    feature: str,
    argv: list[str],
) -> None:
    command = tuple(argv)

    if feature == "ssh":
        if command == (
            "/usr/sbin/sshd",
            "-t",
        ):
            return

        if (
            len(argv) == 3
            and argv[0] == "/usr/bin/loginctl"
            and argv[1] == "terminate-session"
            and SESSION_ID_RE.fullmatch(
                argv[2]
            )
        ):
            return

    elif feature == "firewall":
        if command in {
            (
                "/usr/sbin/nft",
                "-c",
                "-f",
                "/etc/nftables.conf",
            ),
            (
                "/usr/sbin/nft",
                "-f",
                "/etc/nftables.conf",
            ),
        }:
            return

    elif feature == "graphics":
        if command == (
            "/usr/sbin/update-initramfs",
            "-u",
        ):
            return

    elif feature == "power_profile":
        if command == (
            "/usr/bin/udevadm",
            "control",
            "--reload-rules",
        ):
            return

    elif feature == "headless":
        if command == (
            "/usr/bin/systemctl",
            "kill",
            "--kill-whom=main",
            "--signal=HUP",
            "systemd-logind.service",
        ):
            return

        validate_gsettings_command(
            argv
        )
        return

    raise PermissionError(
        f"Command is not allowed for "
        f"feature {feature!r}: {argv!r}"
    )


def validate_gsettings_command(
    argv: list[str],
) -> None:
    if len(argv) != 10:
        raise PermissionError(
            "Invalid managed gsettings command."
        )

    if argv[0] != "runuser":
        raise PermissionError(
            "Invalid gsettings command."
        )

    if argv[1] != "-u":
        raise PermissionError(
            "Invalid gsettings command."
        )

    username = argv[2]

    if not USERNAME_RE.fullmatch(
        username
    ):
        raise PermissionError(
            "Invalid target username."
        )

    if argv[3:7] != [
        "--",
        "dbus-run-session",
        "gsettings",
        "set",
    ]:
        raise PermissionError(
            "Invalid gsettings command."
        )

    if (
        argv[7]
        != "org.gnome.settings-daemon.plugins.power"
    ):
        raise PermissionError(
            "Unexpected gsettings schema."
        )

    allowed_keys = {
        "sleep-inactive-ac-type",
        "sleep-inactive-ac-timeout",
        "sleep-inactive-battery-type",
        "sleep-inactive-battery-timeout",
    }

    key = argv[8]
    value = argv[9]

    if key not in allowed_keys:
        raise PermissionError(
            "Unsupported gsettings key."
        )

    if key.endswith("-type"):
        allowed_actions = {
            "blank",
            "suspend",
            "shutdown",
            "hibernate",
            "interactive",
            "nothing",
            "logout",
        }

        if value not in allowed_actions:
            raise PermissionError(
                "Unsupported power action."
            )

    else:
        try:
            timeout = int(value)
        except ValueError as exc:
            raise PermissionError(
                "Invalid timeout."
            ) from exc

        if timeout < 0:
            raise PermissionError(
                "Invalid timeout."
            )


def validate_systemctl(
    feature: str,
    argv: list[str],
) -> None:
    if not argv:
        raise ValueError(
            "systemctl action requires arguments."
        )

    operation = argv[0]

    if operation not in ALLOWED_SYSTEMCTL_OPERATIONS:
        raise PermissionError(
            "Unsupported systemctl operation."
        )

    if operation == "daemon-reload":
        if len(argv) != 1:
            raise PermissionError(
                "daemon-reload takes no unit."
            )

        if feature not in {
            "power_profile",
            "power_guardian",
        }:
            raise PermissionError(
                "daemon-reload not allowed "
                "for this feature."
            )

        return

    if len(argv) != 2:
        raise PermissionError(
            "Expected one systemd unit."
        )

    unit = argv[1]

    allowed_units = SAFE_SYSTEMD_UNITS.get(
        feature,
        set(),
    )

    if unit not in allowed_units:
        raise PermissionError(
            f"Unit is not allowed for "
            f"feature {feature!r}: {unit}"
        )


def validate_transaction(
    transaction: ApplyTransaction,
) -> None:
    if transaction.feature not in SAFE_TARGETS:
        raise PermissionError(
            f"Unsupported managed feature: "
            f"{transaction.feature}"
        )

    for action in transaction.actions:
        if action.action_type in {
            ActionType.WRITE_FILE,
            ActionType.REMOVE_FILE,
        }:
            validate_target(
                transaction.feature,
                action.target,
            )

        elif (
            action.action_type
            == ActionType.RUN_COMMAND
        ):
            validate_run_command(
                transaction.feature,
                action.argv,
            )

        elif (
            action.action_type
            == ActionType.SYSTEMCTL
        ):
            validate_systemctl(
                transaction.feature,
                action.argv,
            )

        else:
            raise PermissionError(
                f"Unsupported action type: "
                f"{action.action_type}"
            )


def write_file(
    action: ApplyAction,
) -> None:
    if not action.target:
        raise ValueError(
            "write_file requires target."
        )

    if action.content is None:
        raise ValueError(
            "write_file requires content."
        )

    target = Path(
        action.target
    )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fd, temporary_name = tempfile.mkstemp(
        prefix=".homelabctl-",
        dir=str(target.parent),
    )

    temporary = Path(
        temporary_name
    )

    try:
        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
        ) as handle:
            handle.write(
                action.content
            )

            handle.flush()

            os.fsync(
                handle.fileno()
            )

        if action.mode is not None:
            temporary.chmod(
                action.mode
            )

        os.replace(
            temporary,
            target,
        )

    finally:
        if temporary.exists():
            temporary.unlink()


def remove_file(
    action: ApplyAction,
) -> None:
    if not action.target:
        raise ValueError(
            "remove_file requires target."
        )

    path = Path(
        action.target
    )

    if path.exists():
        path.unlink()


def _logind_property(
    session_id: str,
    property_name: str,
) -> str:
    result = subprocess.run(
        [
            "/usr/bin/loginctl",
            "show-session",
            session_id,
            "-p",
            property_name,
            "--value",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Unable to inspect logind session "
            f"{session_id!r}."
        )

    value = result.stdout.strip()

    if not value:
        raise RuntimeError(
            f"Missing {property_name} for "
            f"logind session {session_id!r}."
        )

    return value


def validate_disconnect_target(
    session_id: str,
) -> None:
    current_session = _logind_property(
        "self",
        "Id",
    )

    if session_id == current_session:
        raise PermissionError(
            "Refusing to disconnect the current "
            "HomeLabCTL SSH session."
        )

    service = _logind_property(
        session_id,
        "Service",
    )

    if service != "sshd":
        raise PermissionError(
            "Target is not an SSH session."
        )

    remote = _logind_property(
        session_id,
        "Remote",
    ).lower()

    if remote not in {
        "yes",
        "true",
        "1",
    }:
        raise PermissionError(
            "Target is not a remote session."
        )

    state = _logind_property(
        session_id,
        "State",
    ).lower()

    if state != "active":
        raise PermissionError(
            "Target SSH session is not active."
        )


def run_command(
    action: ApplyAction,
) -> None:
    if (
        len(action.argv) == 3
        and action.argv[0]
        == "/usr/bin/loginctl"
        and action.argv[1]
        == "terminate-session"
    ):
        validate_disconnect_target(
            action.argv[2]
        )

    result = subprocess.run(
        action.argv,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code "
            f"{result.returncode}: "
            f"{action.argv!r}"
        )


def run_systemctl(
    action: ApplyAction,
) -> None:
    operation = action.argv[0]

    if operation == "daemon-reload":
        command = [
            "systemctl",
            "daemon-reload",
        ]

    elif operation == "enable-now":
        command = [
            "systemctl",
            "enable",
            "--now",
            action.argv[1],
        ]

    elif operation == "disable-now":
        command = [
            "systemctl",
            "disable",
            "--now",
            action.argv[1],
        ]

    else:
        command = [
            "systemctl",
            operation,
            action.argv[1],
        ]

    subprocess.run(
        command,
        check=True,
    )


def execute_action(
    action: ApplyAction,
) -> None:
    if (
        action.action_type
        == ActionType.WRITE_FILE
    ):
        write_file(action)
        return

    if (
        action.action_type
        == ActionType.REMOVE_FILE
    ):
        remove_file(action)
        return

    if (
        action.action_type
        == ActionType.RUN_COMMAND
    ):
        run_command(action)
        return

    if (
        action.action_type
        == ActionType.SYSTEMCTL
    ):
        run_systemctl(action)
        return

    raise ValueError(
        f"Unsupported action type: "
        f"{action.action_type}"
    )


def _is_ssh_config_transaction(
    transaction: ApplyTransaction,
) -> bool:
    if transaction.feature != "ssh":
        return False

    managed_target = (
        "/etc/ssh/sshd_config.d/"
        "00-homelabctl.conf"
    )

    return any(
        (
            action.action_type
            in {
                ActionType.WRITE_FILE,
                ActionType.REMOVE_FILE,
            }
            and action.target
            == managed_target
        )
        for action in transaction.actions
    )


def _backup_transaction_files(
    transaction: ApplyTransaction,
) -> list[BackupRecord]:
    records: list[BackupRecord] = []

    for action in transaction.actions:
        if (
            action.backup
            and action.target
            and action.action_type
            in {
                ActionType.WRITE_FILE,
                ActionType.REMOVE_FILE,
            }
        ):
            records.append(
                backup_file(
                    Path(action.target),
                    transaction_id=(
                        transaction.id
                    ),
                )
            )

    return records


def _reload_restored_ssh() -> None:
    subprocess.run(
        [
            "/usr/sbin/sshd",
            "-t",
        ],
        check=True,
    )

    subprocess.run(
        [
            "/usr/bin/systemctl",
            "reload",
            "ssh.service",
        ],
        check=True,
    )


def execute_safe_ssh_transaction(
    transaction: ApplyTransaction,
) -> None:
    with ssh_safety_lock():
        pending = (
            load_pending_ssh_rollback()
        )

        if pending is not None:
            raise RuntimeError(
                "Another SSH apply is awaiting "
                "connectivity confirmation."
            )

        records = (
            _backup_transaction_files(
                transaction
            )
        )

        # The manifest MUST exist before the timer
        # is armed or any managed file is changed.
        write_manifest(
            transaction.id,
            records,
        )

        armed = False

        try:
            arm_ssh_rollback(
                transaction.id
            )

            armed = True

            for action in transaction.actions:
                execute_action(
                    action
                )

        except Exception:
            # Immediate recovery while this root
            # process is still alive.
            restore_transaction_files(
                transaction.id
            )

            # Ensure the restored configuration is
            # valid and active before disarming the
            # independent timer.
            _reload_restored_ssh()

            if armed:
                cancel_ssh_rollback(
                    transaction.id
                )

            raise

        # Success intentionally leaves the rollback
        # timer armed. A separate connectivity
        # confirmation must cancel it.


def rollback_pending_ssh(
    transaction_id: str,
) -> None:
    validate_transaction_id(
        transaction_id
    )

    with ssh_safety_lock():
        pending = (
            load_pending_ssh_rollback()
        )

        if pending is None:
            raise RuntimeError(
                "No SSH rollback is pending."
            )

        if (
            pending["transaction_id"]
            != transaction_id
        ):
            raise PermissionError(
                "SSH rollback transaction mismatch."
            )

        restore_transaction_files(
            transaction_id
        )

        _reload_restored_ssh()

        clear_ssh_rollback_state(
            transaction_id
        )


def confirm_pending_ssh(
    transaction_id: str,
) -> None:
    validate_transaction_id(
        transaction_id
    )

    with ssh_safety_lock():
        pending = (
            load_pending_ssh_rollback()
        )

        if pending is None:
            raise RuntimeError(
                "No SSH rollback is pending."
            )

        if (
            pending["transaction_id"]
            != transaction_id
        ):
            raise PermissionError(
                "SSH rollback transaction mismatch."
            )

        verify_ssh_for_confirmation()

        cancel_ssh_rollback(
            transaction_id
        )


def _is_firewall_config_transaction(
    transaction: ApplyTransaction,
) -> bool:
    if transaction.feature != "firewall":
        return False

    managed_target = "/etc/nftables.conf"

    return any(
        (
            action.action_type
            in {
                ActionType.WRITE_FILE,
                ActionType.REMOVE_FILE,
            }
            and action.target
            == managed_target
        )
        for action in transaction.actions
    )


def _reload_restored_firewall() -> None:
    subprocess.run(
        [
            "/usr/sbin/nft",
            "-c",
            "-f",
            "/etc/nftables.conf",
        ],
        check=True,
    )

    subprocess.run(
        [
            "/usr/sbin/nft",
            "-f",
            "/etc/nftables.conf",
        ],
        check=True,
    )


def execute_safe_firewall_transaction(
    transaction: ApplyTransaction,
) -> None:
    with firewall_safety_lock():
        pending = (
            load_pending_firewall_rollback()
        )

        if pending is not None:
            raise RuntimeError(
                "Another firewall apply is "
                "awaiting connectivity "
                "confirmation."
            )

        records = (
            _backup_transaction_files(
                transaction
            )
        )

        # Manifest must exist before the timer
        # is armed or nftables is changed.
        write_manifest(
            transaction.id,
            records,
        )

        armed = False

        try:
            arm_firewall_rollback(
                transaction.id
            )

            armed = True

            for action in transaction.actions:
                execute_action(
                    action
                )

        except Exception:
            # Restore the previous config first.
            restore_transaction_files(
                transaction.id
            )

            # Then validate and activate the
            # restored ruleset before disarming
            # the independent rollback timer.
            _reload_restored_firewall()

            if armed:
                cancel_firewall_rollback(
                    transaction.id
                )

            raise

        # Success intentionally leaves the
        # rollback timer armed until a separate
        # connectivity confirmation.


def rollback_pending_firewall(
    transaction_id: str,
) -> None:
    validate_firewall_transaction_id(
        transaction_id
    )

    with firewall_safety_lock():
        pending = (
            load_pending_firewall_rollback()
        )

        if pending is None:
            raise RuntimeError(
                "No firewall rollback is pending."
            )

        if (
            pending["transaction_id"]
            != transaction_id
        ):
            raise PermissionError(
                "Firewall rollback transaction "
                "mismatch."
            )

        restore_transaction_files(
            transaction_id
        )

        _reload_restored_firewall()

        clear_firewall_rollback_state(
            transaction_id
        )


def confirm_pending_firewall(
    transaction_id: str,
) -> None:
    validate_firewall_transaction_id(
        transaction_id
    )

    with firewall_safety_lock():
        pending = (
            load_pending_firewall_rollback()
        )

        if pending is None:
            raise RuntimeError(
                "No firewall rollback is pending."
            )

        if (
            pending["transaction_id"]
            != transaction_id
        ):
            raise PermissionError(
                "Firewall rollback transaction "
                "mismatch."
            )

        verify_firewall_for_confirmation()

        cancel_firewall_rollback(
            transaction_id
        )


def execute_transaction(
    transaction: ApplyTransaction,
) -> None:
    validate_transaction(
        transaction
    )

    if _is_ssh_config_transaction(
        transaction
    ):
        execute_safe_ssh_transaction(
            transaction
        )
        return

    if _is_firewall_config_transaction(
        transaction
    ):
        execute_safe_firewall_transaction(
            transaction
        )
        return

    records: list[
        BackupRecord
    ] = []

    try:
        for action in transaction.actions:
            if (
                action.backup
                and action.target
                and action.action_type
                in {
                    ActionType.WRITE_FILE,
                    ActionType.REMOVE_FILE,
                }
            ):
                records.append(
                    backup_file(
                        Path(
                            action.target
                        ),
                        transaction_id=(
                            transaction.id
                        ),
                    )
                )

            execute_action(
                action
            )

        write_manifest(
            transaction.id,
            records,
        )

    except Exception:
        if records:
            write_manifest(
                transaction.id,
                records,
            )

            restore_transaction_files(
                transaction.id
            )

        raise


def main() -> int:
    require_root()

    try:
        if len(sys.argv) > 1:
            if (
                len(sys.argv) == 3
                and sys.argv[1]
                == "--rollback-ssh"
            ):
                transaction_id = (
                    sys.argv[2]
                )

                rollback_pending_ssh(
                    transaction_id
                )

                print(
                    "SSH rollback completed for "
                    f"{transaction_id}."
                )

                return 0

            if (
                len(sys.argv) == 3
                and sys.argv[1]
                == "--confirm-ssh"
            ):
                transaction_id = (
                    sys.argv[2]
                )

                confirm_pending_ssh(
                    transaction_id
                )

                print(
                    "SSH connectivity confirmed for "
                    f"{transaction_id}."
                )

                return 0

            if (
                len(sys.argv) == 3
                and sys.argv[1]
                == "--rollback-firewall"
            ):
                transaction_id = (
                    sys.argv[2]
                )

                rollback_pending_firewall(
                    transaction_id
                )

                print(
                    "Firewall rollback completed "
                    f"for {transaction_id}."
                )

                return 0

            if (
                len(sys.argv) == 3
                and sys.argv[1]
                == "--confirm-firewall"
            ):
                transaction_id = (
                    sys.argv[2]
                )

                confirm_pending_firewall(
                    transaction_id
                )

                print(
                    "Firewall connectivity "
                    "confirmed for "
                    f"{transaction_id}."
                )

                return 0

            print(
                "Unsupported privileged operation.",
                file=sys.stderr,
            )

            return 2

        raw = sys.stdin.read()

        if not raw:
            print(
                "No transaction supplied.",
                file=sys.stderr,
            )
            return 2

        data = json.loads(raw)

        transaction = (
            transaction_from_dict(
                data
            )
        )

        execute_transaction(
            transaction
        )

    except Exception as exc:
        print(
            f"Apply failed: {exc}",
            file=sys.stderr,
        )
        return 1

    print(
        f"Transaction "
        f"{transaction.id} "
        f"completed successfully."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
