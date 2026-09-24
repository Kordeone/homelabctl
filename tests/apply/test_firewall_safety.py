from pathlib import Path

import pytest

from homelabctl.apply import (
    firewall_safety,
)


TXID = "a" * 32


def configure_paths(
    monkeypatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "runtime"

    monkeypatch.setattr(
        firewall_safety,
        "FIREWALL_SAFETY_ROOT",
        root,
    )

    monkeypatch.setattr(
        firewall_safety,
        "FIREWALL_ROLLBACK_STATE",
        root / "firewall-rollback.json",
    )

    monkeypatch.setattr(
        firewall_safety,
        "FIREWALL_ROLLBACK_LOCK",
        root / "firewall-rollback.lock",
    )


def test_transaction_id_validation():
    assert (
        firewall_safety.validate_transaction_id(
            TXID
        )
        == TXID
    )

    for value in (
        "",
        "abc",
        "../" + TXID,
        "A" * 32,
        "g" * 32,
        "a" * 31,
        "a" * 33,
    ):
        with pytest.raises(ValueError):
            firewall_safety.validate_transaction_id(
                value
            )


def test_rollback_unit_name():
    assert (
        firewall_safety.rollback_unit_name(
            TXID
        )
        == (
            "homelabctl-firewall-rollback-"
            + TXID
        )
    )


def test_arm_writes_state_and_timer(
    monkeypatch,
    tmp_path,
):
    configure_paths(
        monkeypatch,
        tmp_path,
    )

    calls = []

    def fake_run(argv, **kwargs):
        calls.append(
            (argv, kwargs)
        )

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(
        firewall_safety.subprocess,
        "run",
        fake_run,
    )

    unit = (
        firewall_safety.arm_firewall_rollback(
            TXID
        )
    )

    assert unit.endswith(TXID)

    pending = (
        firewall_safety
        .load_pending_firewall_rollback()
    )

    assert pending is not None
    assert (
        pending["transaction_id"]
        == TXID
    )

    command = calls[0][0]

    assert command[0] == (
        "/usr/bin/systemd-run"
    )

    assert (
        "--on-active=120s"
        in command
    )

    assert command[-2:] == [
        "--rollback-firewall",
        TXID,
    ]


def test_second_pending_apply_is_rejected(
    monkeypatch,
    tmp_path,
):
    configure_paths(
        monkeypatch,
        tmp_path,
    )

    monkeypatch.setattr(
        firewall_safety.subprocess,
        "run",
        lambda *args, **kwargs: None,
    )

    firewall_safety.arm_firewall_rollback(
        TXID
    )

    with pytest.raises(RuntimeError):
        firewall_safety.arm_firewall_rollback(
            "b" * 32
        )


def test_cancel_requires_matching_transaction(
    monkeypatch,
    tmp_path,
):
    configure_paths(
        monkeypatch,
        tmp_path,
    )

    monkeypatch.setattr(
        firewall_safety.subprocess,
        "run",
        lambda *args, **kwargs: None,
    )

    firewall_safety.arm_firewall_rollback(
        TXID
    )

    with pytest.raises(
        PermissionError
    ):
        firewall_safety.cancel_firewall_rollback(
            "b" * 32
        )


def test_cancel_stops_timer_and_removes_state(
    monkeypatch,
    tmp_path,
):
    configure_paths(
        monkeypatch,
        tmp_path,
    )

    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(
        firewall_safety.subprocess,
        "run",
        fake_run,
    )

    firewall_safety.arm_firewall_rollback(
        TXID
    )

    firewall_safety.cancel_firewall_rollback(
        TXID
    )

    assert not (
        firewall_safety
        .FIREWALL_ROLLBACK_STATE
        .exists()
    )

    assert calls[-1] == [
        "/usr/bin/systemctl",
        "stop",
        (
            "homelabctl-firewall-rollback-"
            f"{TXID}.timer"
        ),
    ]


def test_confirmation_verification(
    monkeypatch,
):
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(
            (argv, kwargs)
        )

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(
        firewall_safety.subprocess,
        "run",
        fake_run,
    )

    firewall_safety \
        .verify_firewall_for_confirmation()

    assert calls[0][0] == [
        "/usr/sbin/nft",
        "-c",
        "-f",
        "/etc/nftables.conf",
    ]

    assert calls[1][0] == [
        "/usr/bin/systemctl",
        "is-active",
        "--quiet",
        "nftables.service",
    ]

    assert all(
        kwargs["check"] is True
        for _, kwargs in calls
    )
