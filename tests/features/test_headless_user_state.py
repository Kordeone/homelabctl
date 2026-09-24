from homelabctl.core.actual_state import make_actual_state
from homelabctl.core.models import Status
from homelabctl.features.headless import (
    HeadlessSettings,
    desired_state,
    evaluate,
    verify,
)


def _actual(
    *,
    user: str = "operator",
    ac_action: str = "nothing",
    battery_action: str = "nothing",
):
    return make_actual_state(
        "headless",
        status=Status.PASS,
        summary="test",
        values={
            "lid_switch": "ignore",
            "lid_switch_external_power": "ignore",
            "lid_switch_docked": "ignore",
            "idle_action": "ignore",
            "gdm_sleep_inactive_ac_type": "nothing",
            "gdm_sleep_inactive_ac_timeout": 0,
            "gdm_sleep_inactive_battery_type": "nothing",
            "gdm_sleep_inactive_battery_timeout": 0,
            "desktop_users": {
                user: {
                    "sleep_inactive_ac_type": ac_action,
                    "sleep_inactive_ac_timeout": 0,
                    "sleep_inactive_battery_type":
                        battery_action,
                    "sleep_inactive_battery_timeout": 0,
                },
            },
        },
    )


def test_desired_state_includes_desktop_user_policy():
    desired = desired_state(
        HeadlessSettings(
            desktop_user="operator"
        )
    )

    assert (
        desired.settings["desktop_user"].value
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
            "user_sleep_inactive_battery_type"
        ].value
        == "nothing"
    )


def test_selected_desktop_user_matches():
    settings = HeadlessSettings(
        desktop_user="operator"
    )

    actual = _actual()

    assert evaluate(
        actual,
        settings,
    ) == Status.PASS

    assert verify(
        actual,
        settings,
    ).passed


def test_selected_desktop_user_drift_is_detected():
    settings = HeadlessSettings(
        desktop_user="operator"
    )

    actual = _actual(
        ac_action="suspend"
    )

    assert evaluate(
        actual,
        settings,
    ) != Status.PASS

    report = verify(
        actual,
        settings,
    )

    assert not report.passed

    check = next(
        item
        for item in report.checks
        if item.key
        == "user_sleep_inactive_ac_type"
    )

    assert check.expected == "nothing"
    assert check.actual == "suspend"
    assert not check.passed


def test_missing_selected_desktop_user_is_detected():
    settings = HeadlessSettings(
        desktop_user="missing-user"
    )

    actual = _actual(
        user="operator"
    )

    report = verify(
        actual,
        settings,
    )

    assert not report.passed

    check = next(
        item
        for item in report.checks
        if item.key == "desktop_user"
    )

    assert check.expected == "missing-user"
    assert check.actual is None
    assert not check.passed
