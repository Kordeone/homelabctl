import pytest

from homelabctl.apply.runner import (
    validate_gsettings_command,
)


def command(
    value: str,
    *,
    key: str = "sleep-inactive-ac-type",
):
    return [
        "runuser",
        "-u",
        "operator",
        "--",
        "dbus-run-session",
        "gsettings",
        "set",
        "org.gnome.settings-daemon.plugins.power",
        key,
        value,
    ]


@pytest.mark.parametrize(
    "value",
    [
        "blank",
        "suspend",
        "shutdown",
        "hibernate",
        "interactive",
        "nothing",
        "logout",
    ],
)
def test_headless_runner_accepts_schema_actions(
    value,
):
    validate_gsettings_command(
        command(
            value
        )
    )


def test_headless_runner_rejects_unknown_action():
    with pytest.raises(
        PermissionError
    ):
        validate_gsettings_command(
            command(
                "factory-reset"
            )
        )


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "1",
        "900",
        "86400",
    ],
)
def test_headless_runner_accepts_nonnegative_timeout(
    value,
):
    validate_gsettings_command(
        command(
            value,
            key="sleep-inactive-ac-timeout",
        )
    )


def test_headless_runner_rejects_negative_timeout():
    with pytest.raises(
        PermissionError
    ):
        validate_gsettings_command(
            command(
                "-1",
                key="sleep-inactive-ac-timeout",
            )
        )


def test_headless_runner_accepts_exact_logind_hup():
    from homelabctl.apply.runner import (
        validate_run_command,
    )

    validate_run_command(
        "headless",
        [
            "/usr/bin/systemctl",
            "kill",
            "--kill-whom=main",
            "--signal=HUP",
            "systemd-logind.service",
        ],
    )


def test_headless_runner_rejects_other_logind_signal():
    from homelabctl.apply.runner import (
        validate_run_command,
    )

    with pytest.raises(
        PermissionError
    ):
        validate_run_command(
            "headless",
            [
                "/usr/bin/systemctl",
                "kill",
                "--kill-whom=main",
                "--signal=TERM",
                "systemd-logind.service",
            ],
        )
