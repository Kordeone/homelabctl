from homelabctl.apply import sudo


TXID = "a" * 32


def test_firewall_rollback_bridge(
    monkeypatch,
):
    calls = []

    class Result:
        returncode = 0

    def fake_run(
        argv,
        **kwargs,
    ):
        calls.append(
            (argv, kwargs)
        )
        return Result()

    monkeypatch.setattr(
        sudo.subprocess,
        "run",
        fake_run,
    )

    result = (
        sudo.rollback_firewall_transaction(
            TXID
        )
    )

    assert result == 0

    assert calls[0][0] == [
        "sudo",
        (
            "/opt/homelabctl/venv/bin/"
            "homelabctl-apply"
        ),
        "--rollback-firewall",
        TXID,
    ]
