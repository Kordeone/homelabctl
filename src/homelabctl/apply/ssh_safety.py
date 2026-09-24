"""Timed rollback safety for high-risk SSH changes."""

from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SSH_ROLLBACK_TIMEOUT_SECONDS = 90

SSH_SAFETY_ROOT = Path(
    "/run/homelabctl-apply"
)

SSH_ROLLBACK_STATE = (
    SSH_SAFETY_ROOT / "ssh-rollback.json"
)

SSH_ROLLBACK_LOCK = (
    SSH_SAFETY_ROOT / "ssh-rollback.lock"
)

APPLY_HELPER = (
    "/opt/homelabctl/venv/bin/"
    "homelabctl-apply"
)

TRANSACTION_ID_RE = re.compile(
    r"^[0-9a-f]{32}$"
)


def validate_transaction_id(
    transaction_id: str,
) -> str:
    if not TRANSACTION_ID_RE.fullmatch(
        transaction_id
    ):
        raise ValueError(
            "Invalid SSH rollback transaction ID."
        )

    return transaction_id


def rollback_unit_name(
    transaction_id: str,
) -> str:
    validate_transaction_id(
        transaction_id
    )

    return (
        "homelabctl-ssh-rollback-"
        f"{transaction_id}"
    )


def _ensure_root_directory() -> None:
    SSH_SAFETY_ROOT.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )

    os.chmod(
        SSH_SAFETY_ROOT,
        0o700,
    )


@contextmanager
def ssh_safety_lock() -> Iterator[None]:
    _ensure_root_directory()

    with SSH_ROLLBACK_LOCK.open(
        "a+",
        encoding="utf-8",
    ) as handle:
        os.chmod(
            SSH_ROLLBACK_LOCK,
            0o600,
        )

        fcntl.flock(
            handle.fileno(),
            fcntl.LOCK_EX,
        )

        try:
            yield
        finally:
            fcntl.flock(
                handle.fileno(),
                fcntl.LOCK_UN,
            )


def load_pending_ssh_rollback(
) -> dict[str, object] | None:
    if not SSH_ROLLBACK_STATE.exists():
        return None

    data = json.loads(
        SSH_ROLLBACK_STATE.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(data, dict):
        raise RuntimeError(
            "Invalid SSH rollback state."
        )

    transaction_id = data.get(
        "transaction_id"
    )

    unit = data.get(
        "unit"
    )

    if not isinstance(
        transaction_id,
        str,
    ):
        raise RuntimeError(
            "SSH rollback state has no transaction ID."
        )

    validate_transaction_id(
        transaction_id
    )

    expected_unit = rollback_unit_name(
        transaction_id
    )

    if unit != expected_unit:
        raise RuntimeError(
            "SSH rollback state has an invalid unit."
        )

    return data


def _write_pending_state(
    transaction_id: str,
    unit: str,
) -> None:
    _ensure_root_directory()

    temporary = (
        SSH_SAFETY_ROOT
        / "ssh-rollback.json.tmp"
    )

    temporary.write_text(
        json.dumps(
            {
                "transaction_id": (
                    transaction_id
                ),
                "unit": unit,
                "timeout_seconds": (
                    SSH_ROLLBACK_TIMEOUT_SECONDS
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    os.chmod(
        temporary,
        0o600,
    )

    os.replace(
        temporary,
        SSH_ROLLBACK_STATE,
    )


def arm_ssh_rollback(
    transaction_id: str,
) -> str:
    validate_transaction_id(
        transaction_id
    )

    pending = load_pending_ssh_rollback()

    if pending is not None:
        raise RuntimeError(
            "Another SSH rollback is already pending."
        )

    unit = rollback_unit_name(
        transaction_id
    )

    subprocess.run(
        [
            "/usr/bin/systemd-run",
            "--quiet",
            f"--unit={unit}",
            (
                "--on-active="
                f"{SSH_ROLLBACK_TIMEOUT_SECONDS}s"
            ),
            "--timer-property=AccuracySec=1s",
            "--property=Type=oneshot",
            APPLY_HELPER,
            "--rollback-ssh",
            transaction_id,
        ],
        check=True,
    )

    try:
        _write_pending_state(
            transaction_id,
            unit,
        )
    except Exception:
        subprocess.run(
            [
                "/usr/bin/systemctl",
                "stop",
                f"{unit}.timer",
            ],
            check=False,
        )

        raise

    return unit


def cancel_ssh_rollback(
    transaction_id: str,
) -> None:
    validate_transaction_id(
        transaction_id
    )

    pending = load_pending_ssh_rollback()

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

    unit = str(
        pending["unit"]
    )

    subprocess.run(
        [
            "/usr/bin/systemctl",
            "stop",
            f"{unit}.timer",
        ],
        check=True,
    )

    SSH_ROLLBACK_STATE.unlink(
        missing_ok=True
    )


def clear_ssh_rollback_state(
    transaction_id: str,
) -> None:
    validate_transaction_id(
        transaction_id
    )

    pending = load_pending_ssh_rollback()

    if pending is None:
        return

    if (
        pending["transaction_id"]
        != transaction_id
    ):
        raise PermissionError(
            "SSH rollback transaction mismatch."
        )

    SSH_ROLLBACK_STATE.unlink(
        missing_ok=True
    )


def verify_ssh_for_confirmation() -> None:
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
            "is-active",
            "--quiet",
            "ssh.service",
        ],
        check=True,
    )
