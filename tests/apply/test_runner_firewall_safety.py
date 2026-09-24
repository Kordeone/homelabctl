from contextlib import nullcontext

import pytest

from homelabctl.apply import runner
from homelabctl.apply.transaction import (
    ActionType,
    ApplyAction,
    new_transaction,
)


TXID = "a" * 32


def make_transaction():
    transaction = new_transaction(
        feature="firewall",
        actions=[
            ApplyAction(
                action_type=(
                    ActionType.WRITE_FILE
                ),
                description="write",
                target="/etc/nftables.conf",
                content="flush ruleset\n",
                backup=True,
            ),
            ApplyAction(
                action_type=(
                    ActionType.RUN_COMMAND
                ),
                description="validate",
                argv=[
                    "/usr/sbin/nft",
                    "-c",
                    "-f",
                    "/etc/nftables.conf",
                ],
                backup=False,
            ),
            ApplyAction(
                action_type=(
                    ActionType.RUN_COMMAND
                ),
                description="apply",
                argv=[
                    "/usr/sbin/nft",
                    "-f",
                    "/etc/nftables.conf",
                ],
                backup=False,
            ),
        ],
    )

    transaction.id = TXID

    return transaction


def test_safe_firewall_manifest_precedes_timer(
    monkeypatch,
):
    transaction = make_transaction()
    events = []

    monkeypatch.setattr(
        runner,
        "firewall_safety_lock",
        lambda: nullcontext(),
    )

    monkeypatch.setattr(
        runner,
        "load_pending_firewall_rollback",
        lambda: None,
    )

    monkeypatch.setattr(
        runner,
        "_backup_transaction_files",
        lambda transaction: (
            events.append("backup")
            or []
        ),
    )

    monkeypatch.setattr(
        runner,
        "write_manifest",
        lambda *args, **kwargs: (
            events.append("manifest")
        ),
    )

    monkeypatch.setattr(
        runner,
        "arm_firewall_rollback",
        lambda transaction_id: (
            events.append("arm")
        ),
    )

    monkeypatch.setattr(
        runner,
        "execute_action",
        lambda action: (
            events.append("execute")
        ),
    )

    runner.execute_safe_firewall_transaction(
        transaction
    )

    assert events == [
        "backup",
        "manifest",
        "arm",
        "execute",
        "execute",
        "execute",
    ]


def test_safe_firewall_success_keeps_timer_armed(
    monkeypatch,
):
    transaction = make_transaction()
    cancelled = []

    monkeypatch.setattr(
        runner,
        "firewall_safety_lock",
        lambda: nullcontext(),
    )

    monkeypatch.setattr(
        runner,
        "load_pending_firewall_rollback",
        lambda: None,
    )

    monkeypatch.setattr(
        runner,
        "_backup_transaction_files",
        lambda transaction: [],
    )

    monkeypatch.setattr(
        runner,
        "write_manifest",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        runner,
        "arm_firewall_rollback",
        lambda transaction_id: None,
    )

    monkeypatch.setattr(
        runner,
        "execute_action",
        lambda action: None,
    )

    monkeypatch.setattr(
        runner,
        "cancel_firewall_rollback",
        lambda transaction_id: (
            cancelled.append(
                transaction_id
            )
        ),
    )

    runner.execute_safe_firewall_transaction(
        transaction
    )

    assert cancelled == []


def test_safe_firewall_failure_restores_before_cancel(
    monkeypatch,
):
    transaction = make_transaction()
    events = []

    monkeypatch.setattr(
        runner,
        "firewall_safety_lock",
        lambda: nullcontext(),
    )

    monkeypatch.setattr(
        runner,
        "load_pending_firewall_rollback",
        lambda: None,
    )

    monkeypatch.setattr(
        runner,
        "_backup_transaction_files",
        lambda transaction: [],
    )

    monkeypatch.setattr(
        runner,
        "write_manifest",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        runner,
        "arm_firewall_rollback",
        lambda transaction_id: (
            events.append("arm")
        ),
    )

    def fail_action(action):
        events.append("execute")
        raise RuntimeError("boom")

    monkeypatch.setattr(
        runner,
        "execute_action",
        fail_action,
    )

    monkeypatch.setattr(
        runner,
        "restore_transaction_files",
        lambda transaction_id: (
            events.append("restore")
        ),
    )

    monkeypatch.setattr(
        runner,
        "_reload_restored_firewall",
        lambda: events.append(
            "reload"
        ),
    )

    monkeypatch.setattr(
        runner,
        "cancel_firewall_rollback",
        lambda transaction_id: (
            events.append("cancel")
        ),
    )

    with pytest.raises(RuntimeError):
        runner.execute_safe_firewall_transaction(
            transaction
        )

    assert events == [
        "arm",
        "execute",
        "restore",
        "reload",
        "cancel",
    ]


def test_second_safe_firewall_apply_is_blocked(
    monkeypatch,
):
    transaction = make_transaction()

    monkeypatch.setattr(
        runner,
        "firewall_safety_lock",
        lambda: nullcontext(),
    )

    monkeypatch.setattr(
        runner,
        "load_pending_firewall_rollback",
        lambda: {
            "transaction_id": (
                "b" * 32
            )
        },
    )

    with pytest.raises(RuntimeError):
        runner.execute_safe_firewall_transaction(
            transaction
        )


def test_confirm_pending_firewall(
    monkeypatch,
):
    events = []

    monkeypatch.setattr(
        runner,
        "firewall_safety_lock",
        lambda: nullcontext(),
    )

    monkeypatch.setattr(
        runner,
        "load_pending_firewall_rollback",
        lambda: {
            "transaction_id": TXID
        },
    )

    monkeypatch.setattr(
        runner,
        "verify_firewall_for_confirmation",
        lambda: events.append(
            "verify"
        ),
    )

    monkeypatch.setattr(
        runner,
        "cancel_firewall_rollback",
        lambda transaction_id: (
            events.append("cancel")
        ),
    )

    runner.confirm_pending_firewall(
        TXID
    )

    assert events == [
        "verify",
        "cancel",
    ]


def test_timed_firewall_rollback_restores_and_reloads(
    monkeypatch,
):
    events = []

    monkeypatch.setattr(
        runner,
        "firewall_safety_lock",
        lambda: nullcontext(),
    )

    monkeypatch.setattr(
        runner,
        "load_pending_firewall_rollback",
        lambda: {
            "transaction_id": TXID
        },
    )

    monkeypatch.setattr(
        runner,
        "restore_transaction_files",
        lambda transaction_id: (
            events.append("restore")
        ),
    )

    monkeypatch.setattr(
        runner,
        "_reload_restored_firewall",
        lambda: events.append(
            "reload"
        ),
    )

    monkeypatch.setattr(
        runner,
        "clear_firewall_rollback_state",
        lambda transaction_id: (
            events.append("clear")
        ),
    )

    runner.rollback_pending_firewall(
        TXID
    )

    assert events == [
        "restore",
        "reload",
        "clear",
    ]


def test_firewall_transaction_routes_to_safe_path(
    monkeypatch,
):
    transaction = make_transaction()
    events = []

    monkeypatch.setattr(
        runner,
        "execute_safe_firewall_transaction",
        lambda transaction: (
            events.append("safe")
        ),
    )

    runner.execute_transaction(
        transaction
    )

    assert events == ["safe"]
