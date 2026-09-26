"""Temporary sudo invocation for privileged apply operations."""

from __future__ import annotations

import json
import subprocess

from homelabctl.apply.transaction import (
    ApplyTransaction,
    transaction_to_dict,
)


def validate_sudo() -> bool:
    result = subprocess.run(
        ["sudo", "-v"],
        check=False,
    )

    return result.returncode == 0


def run_privileged_transaction(
    transaction: ApplyTransaction,
) -> int:
    """
    Execute the one-shot privileged apply helper.

    The transaction is sent over stdin rather than placed in a temporary
    user-writable file.
    """

    payload = json.dumps(
        transaction_to_dict(transaction)
    )

    result = subprocess.run(
        [
            "sudo",
            (
                "/opt/homelabctl/venv/bin/"
                "homelabctl-apply"
            ),
        ],
        input=payload,
        text=True,
        check=False,
    )

    return result.returncode



def confirm_ssh_transaction(
    transaction_id: str,
) -> int:
    """Confirm connectivity after a safe SSH apply."""

    result = subprocess.run(
        [
            "sudo",
            (
                "/opt/homelabctl/venv/bin/"
                "homelabctl-apply"
            ),
            "--confirm-ssh",
            transaction_id,
        ],
        text=True,
        check=False,
    )

    return result.returncode


def confirm_firewall_transaction(
    transaction_id: str,
) -> int:
    """Confirm connectivity after a safe firewall apply."""

    result = subprocess.run(
        [
            "sudo",
            (
                "/opt/homelabctl/venv/bin/"
                "homelabctl-apply"
            ),
            "--confirm-firewall",
            transaction_id,
        ],
        text=True,
        check=False,
    )

    return result.returncode



def rollback_firewall_transaction(
    transaction_id: str,
) -> int:
    """Immediately roll back a pending firewall apply."""

    result = subprocess.run(
        [
            "sudo",
            (
                "/opt/homelabctl/venv/bin/"
                "homelabctl-apply"
            ),
            "--rollback-firewall",
            transaction_id,
        ],
        text=True,
        check=False,
    )

    return result.returncode
