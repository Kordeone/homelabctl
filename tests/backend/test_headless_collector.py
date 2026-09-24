from types import SimpleNamespace

from homelabctl.backend.collectors.headless import (
    HeadlessCollector,
)


def test_desktop_usernames_filters_system_accounts(
    monkeypatch,
):
    entries = [
        SimpleNamespace(
            pw_uid=0,
            pw_name="root",
            pw_shell="/bin/bash",
        ),
        SimpleNamespace(
            pw_uid=1000,
            pw_name="operator",
            pw_shell="/bin/bash",
        ),
        SimpleNamespace(
            pw_uid=1001,
            pw_name="service-user",
            pw_shell="/usr/sbin/nologin",
        ),
        SimpleNamespace(
            pw_uid=65534,
            pw_name="nobody",
            pw_shell="/usr/sbin/nologin",
        ),
    ]

    monkeypatch.setattr(
        "homelabctl.backend.collectors.headless.pwd.getpwall",
        lambda: entries,
    )

    collector = HeadlessCollector()

    assert collector._desktop_usernames() == [
        "operator"
    ]


def test_collect_keeps_desktop_users_separate(
    monkeypatch,
):
    collector = HeadlessCollector()

    monkeypatch.setattr(
        collector,
        "_desktop_usernames",
        lambda: [
            "operator",
            "second-user",
        ],
    )

    monkeypatch.setattr(
        collector,
        "_logind_config",
        lambda: {
            "HandleLidSwitch": "ignore",
            "HandleLidSwitchExternalPower": "ignore",
            "HandleLidSwitchDocked": "ignore",
            "IdleAction": "ignore",
        },
    )

    def fake_gsettings(
        username: str,
        *,
        prefix: str,
    ):
        if prefix == "gdm":
            return {
                "gdm_sleep_inactive_ac_type":
                    "nothing",
                "gdm_sleep_inactive_ac_timeout":
                    0,
                "gdm_sleep_inactive_battery_type":
                    "nothing",
                "gdm_sleep_inactive_battery_timeout":
                    0,
            }

        return {
            "sleep_inactive_ac_type": "nothing",
            "sleep_inactive_ac_timeout": 0,
            "sleep_inactive_battery_type": "nothing",
            "sleep_inactive_battery_timeout": 0,
        }

    monkeypatch.setattr(
        collector,
        "_gsettings_for_user",
        fake_gsettings,
    )

    result = collector.collect()

    state = result.modules[0]

    desktop_users = state.get(
        "desktop_users"
    )

    assert sorted(
        desktop_users
    ) == [
        "operator",
        "second-user",
    ]

    assert (
        desktop_users["operator"][
            "sleep_inactive_ac_type"
        ]
        == "nothing"
    )


def test_gsettings_read_does_not_switch_uid(
    monkeypatch,
):
    collector = HeadlessCollector()

    monkeypatch.setattr(
        "homelabctl.backend.collectors.headless.pwd.getpwnam",
        lambda username: SimpleNamespace(
            pw_dir="/home/operator",
            pw_uid=1000,
        ),
    )

    commands = []

    def fake_run_command(
        argv,
        *,
        timeout,
    ):
        commands.append(
            list(argv)
        )

        if argv[-1].endswith(
            "-timeout"
        ):
            output = "900\n"
        else:
            output = "'nothing'\n"

        return SimpleNamespace(
            success=True,
            stdout=output,
        )

    monkeypatch.setattr(
        "homelabctl.backend.collectors.headless.run_command",
        fake_run_command,
    )

    values = collector._gsettings_for_user(
        "operator",
        prefix="",
    )

    assert (
        values["sleep_inactive_ac_type"]
        == "nothing"
    )

    assert (
        values["sleep_inactive_ac_timeout"]
        == 900
    )

    assert len(commands) == 4

    for command in commands:
        assert "/usr/sbin/runuser" not in command
        assert "dbus-run-session" not in command

        assert command[0] == "/usr/bin/env"

        assert (
            "HOME=/home/operator"
            in command
        )

        assert (
            "XDG_CONFIG_HOME=/home/operator/.config"
            in command
        )

        assert any(
            item.startswith(
                "XDG_CACHE_HOME="
            )
            for item in command
        )

        assert (
            "/usr/bin/gsettings"
            in command
        )


def test_logind_duration_conversion():
    collector = HeadlessCollector()

    assert collector._duration_seconds(
        "30min",
        default=1,
    ) == 1800

    assert collector._duration_seconds(
        "2h",
        default=1,
    ) == 7200

    assert collector._duration_seconds(
        "45s",
        default=1,
    ) == 45

    assert collector._duration_seconds(
        None,
        default=1800,
    ) == 1800


def test_status_accepts_noncanonical_but_readable_policy():
    from homelabctl.core.models import Status

    collector = HeadlessCollector()

    values = {
        "lid_switch": "suspend",
        "lid_switch_external_power": "ignore",
        "lid_switch_docked": "lock",
        "power_key": "lock",
        "power_key_long_press": "poweroff",
        "idle_action": "suspend",
        "idle_action_sec": 600,
        "gdm_sleep_inactive_ac_type": "suspend",
        "gdm_sleep_inactive_ac_timeout": 900,
        "gdm_sleep_inactive_battery_type": "nothing",
        "gdm_sleep_inactive_battery_timeout": 0,
        "desktop_users": {
            "operator": {
                "sleep_inactive_ac_type": "nothing",
                "sleep_inactive_ac_timeout": 900,
                "sleep_inactive_battery_type": "hibernate",
                "sleep_inactive_battery_timeout": 600,
            },
        },
    }

    assert collector._status(
        values
    ) == Status.PASS


def test_status_warns_when_extended_state_is_unreadable():
    from homelabctl.core.models import Status

    collector = HeadlessCollector()

    values = {
        "lid_switch": "ignore",
        "lid_switch_external_power": "ignore",
        "lid_switch_docked": "ignore",
        "power_key": None,
        "power_key_long_press": "ignore",
        "idle_action": "ignore",
        "idle_action_sec": 1800,
        "gdm_sleep_inactive_ac_type": "nothing",
        "gdm_sleep_inactive_ac_timeout": 0,
        "gdm_sleep_inactive_battery_type": "nothing",
        "gdm_sleep_inactive_battery_timeout": 0,
        "desktop_users": {
            "operator": {
                "sleep_inactive_ac_type": "nothing",
                "sleep_inactive_ac_timeout": 900,
                "sleep_inactive_battery_type": "nothing",
                "sleep_inactive_battery_timeout": 900,
            },
        },
    }

    assert collector._status(
        values
    ) == Status.WARNING
