from pathlib import Path

import pytest

from homelabctl.apply import ssh_safety


TXID = "a" * 32


def configure_paths(
    monkeypatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "runtime"

    monkeypatch.setattr(
        ssh_safety,
        "SSH_SAFETY_ROOT",
        root,
    )

    monkeypatch.setattr(
        ssh_safety,
        "SSH_ROLLBACK_STATE",
        root / "ssh-rollback.json",
    )

    monkeypatch.setattr(
        ssh_safety,
        "SSH_ROLLBACK_LOCK",
        root / "ssh-rollback.lock",
    )


def test_transaction_id_validation():
    assert (
        ssh_safety.validate_transaction_id(
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
            ssh_safety.validate_transaction_id(
                value
            )


def test_rollback_unit_name():
    assert (
        ssh_safety.rollback_unit_name(
            TXID
        )
        == (
            "homelabctl-ssh-rollback-"
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
        ssh_safety.subprocess,
        "run",
        fake_run,
    )

    unit = ssh_safety.arm_ssh_rollback(
        TXID
    )

    assert unit.endswith(TXID)

    pending = (
        ssh_safety.load_pending_ssh_rollback()
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
        "--on-active=90s"
        in command
    )

    assert command[-2:] == [
        "--rollback-ssh",
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
        ssh_safety.subprocess,
        "run",
        lambda *args, **kwargs: None,
    )

    ssh_safety.arm_ssh_rollback(
        TXID
    )

    with pytest.raises(RuntimeError):
        ssh_safety.arm_ssh_rollback(
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
        ssh_safety.subprocess,
        "run",
        lambda *args, **kwargs: None,
    )

    ssh_safety.arm_ssh_rollback(
        TXID
    )

    with pytest.raises(
        PermissionError
    ):
        ssh_safety.cancel_ssh_rollback(
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
        ssh_safety.subprocess,
        "run",
        fake_run,
    )

    ssh_safety.arm_ssh_rollback(
        TXID
    )

    ssh_safety.cancel_ssh_rollback(
        TXID
    )

    assert not (
        ssh_safety.SSH_ROLLBACK_STATE.exists()
    )

    assert calls[-1] == [
        "/usr/bin/systemctl",
        "stop",
        (
            "homelabctl-ssh-rollback-"
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
        ssh_safety.subprocess,
        "run",
        fake_run,
    )

    ssh_safety.verify_ssh_for_confirmation()

    assert calls[0][0] == [
        "/usr/sbin/sshd",
        "-t",
    ]

    assert calls[1][0] == [
        "/usr/bin/systemctl",
        "is-active",
        "--quiet",
        "ssh.service",
    ]

    assert all(
        kwargs["check"] is True
        for _, kwargs in calls
    )
