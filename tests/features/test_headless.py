from homelabctl.features.headless.plan import (
    render_logind_config,
)
from homelabctl.features.headless.schema import (
    HeadlessSettings,
)


def test_headless_logind_config():
    output = render_logind_config(
        HeadlessSettings(desktop_user="operator")
    )

    assert "HandleLidSwitch=ignore" in output
    assert (
        "HandleLidSwitchExternalPower=ignore"
        in output
    )
    assert "HandleLidSwitchDocked=ignore" in output
    assert "IdleAction=ignore" in output


def test_headless_extended_logind_config():
    settings = HeadlessSettings(
        desktop_user="operator",
        handle_lid_switch="suspend",
        handle_lid_switch_external_power="ignore",
        handle_lid_switch_docked="lock",
        handle_power_key="poweroff",
        handle_power_key_long_press="reboot",
        idle_action="lock",
        idle_action_sec=600,
    )

    output = render_logind_config(
        settings
    )

    assert "HandleLidSwitch=suspend" in output
    assert "HandleLidSwitchDocked=lock" in output
    assert "HandlePowerKey=poweroff" in output
    assert "HandlePowerKeyLongPress=reboot" in output
    assert "IdleAction=lock" in output
    assert "IdleActionSec=600s" in output


def test_headless_rejects_unsafe_unmanaged_action():
    import pytest

    settings = HeadlessSettings(
        desktop_user="operator",
        handle_power_key="factory-reset",
    )

    with pytest.raises(
        ValueError
    ):
        settings.validate()


def test_headless_accepts_supported_desktop_actions():
    settings = HeadlessSettings(
        desktop_user="operator",
        user_ac_action="suspend",
        user_battery_action="hibernate",
        gdm_ac_action="interactive",
        gdm_battery_action="nothing",
    )

    settings.validate()


def test_headless_apply_reloads_logind_last():
    from homelabctl.apply.transaction import (
        ActionType,
    )
    from homelabctl.features.headless.apply import (
        build_apply_transaction,
    )

    transaction = build_apply_transaction(
        HeadlessSettings(
            desktop_user="operator"
        )
    )

    assert len(
        transaction.actions
    ) == 10

    last = transaction.actions[-1]

    assert (
        last.action_type
        == ActionType.RUN_COMMAND
    )

    assert last.argv == [
        "/usr/bin/systemctl",
        "kill",
        "--kill-whom=main",
        "--signal=HUP",
        "systemd-logind.service",
    ]
