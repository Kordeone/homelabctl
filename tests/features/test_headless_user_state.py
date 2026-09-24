from homelabctl.core.actual_state import (
    make_actual_state,
)
from homelabctl.core.models import Status
from homelabctl.features.headless.inspect import (
    desired_state,
    evaluate,
)
from homelabctl.features.headless.schema import (
    HeadlessSettings,
)


def _actual():
    return make_actual_state(
        "headless",
        status=Status.PASS,
        summary="test",
        values={
            "lid_switch": "ignore",
            "lid_switch_external_power": "ignore",
            "lid_switch_docked": "ignore",
            "power_key": "poweroff",
            "power_key_long_press": "ignore",
            "idle_action": "ignore",
            "idle_action_sec": 1800,
            "gdm_sleep_inactive_ac_type": "nothing",
            "gdm_sleep_inactive_ac_timeout": 0,
            "gdm_sleep_inactive_battery_type":
                "nothing",
            "gdm_sleep_inactive_battery_timeout": 0,
            "desktop_users": {
                "operator": {
                    "sleep_inactive_ac_type":
                        "nothing",
                    "sleep_inactive_ac_timeout":
                        900,
                    "sleep_inactive_battery_type":
                        "nothing",
                    "sleep_inactive_battery_timeout":
                        900,
                },
            },
        },
    )


def test_desired_state_includes_user_fields():
    settings = HeadlessSettings(
        desktop_user="operator"
    )

    desired = desired_state(
        settings
    )

    assert (
        desired.settings[
            "desktop_user"
        ].value
        == "operator"
    )

    assert (
        desired.settings[
            "user_sleep_inactive_ac_type"
        ].value
        == "nothing"
    )

    assert (
        desired.settings[
            "user_sleep_inactive_ac_timeout"
        ].value
        == 900
    )

    assert (
        desired.settings[
            "user_sleep_inactive_battery_type"
        ].value
        == "nothing"
    )

    assert (
        desired.settings[
            "user_sleep_inactive_battery_timeout"
        ].value
        == 900
    )


def test_selected_desktop_user_matches():
    settings = HeadlessSettings(
        desktop_user="operator"
    )

    assert evaluate(
        _actual(),
        settings,
    ) == Status.PASS


def test_selected_desktop_user_drift():
    settings = HeadlessSettings(
        desktop_user="operator"
    )

    actual = _actual()

    users = actual.get(
        "desktop_users"
    )

    users["operator"][
        "sleep_inactive_ac_type"
    ] = "suspend"

    assert evaluate(
        actual,
        settings,
    ) == Status.DRIFT


def test_missing_selected_user_is_drift():
    settings = HeadlessSettings(
        desktop_user="missing-user"
    )

    assert evaluate(
        _actual(),
        settings,
    ) == Status.DRIFT


def test_desired_state_includes_extended_power_policy():
    settings = HeadlessSettings(
        desktop_user="operator",
        handle_power_key="lock",
        handle_power_key_long_press="poweroff",
        idle_action="suspend",
        idle_action_sec=300,
        user_ac_timeout=1200,
        user_battery_timeout=600,
    )

    desired = desired_state(
        settings
    )

    assert (
        desired.settings[
            "power_key"
        ].value
        == "lock"
    )

    assert (
        desired.settings[
            "power_key_long_press"
        ].value
        == "poweroff"
    )

    assert (
        desired.settings[
            "idle_action"
        ].value
        == "suspend"
    )

    assert (
        desired.settings[
            "idle_action_sec"
        ].value
        == 300
    )

    assert (
        desired.settings[
            "user_sleep_inactive_ac_timeout"
        ].value
        == 1200
    )

    assert (
        desired.settings[
            "user_sleep_inactive_battery_timeout"
        ].value
        == 600
    )
