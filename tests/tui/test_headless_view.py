import asyncio

from homelabctl.core.models import Status
from homelabctl.features.headless import (
    HeadlessSettings,
)
from homelabctl.features.headless.verify import (
    verify,
)
from homelabctl.tui.screens.headless import (
    HeadlessView,
)


def _module():
    def item(
        key,
        value,
    ):
        return {
            "key": key,
            "value": value,
            "source": None,
            "readable": True,
            "error": None,
        }

    return {
        "module": "headless",
        "status": "pass",
        "summary": "test",
        "values": {
            "lid_switch": item(
                "lid_switch",
                "ignore",
            ),
            "lid_switch_external_power": item(
                "lid_switch_external_power",
                "ignore",
            ),
            "lid_switch_docked": item(
                "lid_switch_docked",
                "ignore",
            ),
            "power_key": item(
                "power_key",
                "poweroff",
            ),
            "power_key_long_press": item(
                "power_key_long_press",
                "ignore",
            ),
            "idle_action": item(
                "idle_action",
                "ignore",
            ),
            "idle_action_sec": item(
                "idle_action_sec",
                1800,
            ),
            "gdm_sleep_inactive_ac_type": item(
                "gdm_sleep_inactive_ac_type",
                "nothing",
            ),
            "gdm_sleep_inactive_ac_timeout": item(
                "gdm_sleep_inactive_ac_timeout",
                0,
            ),
            "gdm_sleep_inactive_battery_type": item(
                "gdm_sleep_inactive_battery_type",
                "nothing",
            ),
            "gdm_sleep_inactive_battery_timeout": item(
                "gdm_sleep_inactive_battery_timeout",
                0,
            ),
            "desktop_users": item(
                "desktop_users",
                {
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
            ),
        },
    }


def test_value_unwraps_backend_state_value():
    values = {
        "example": {
            "value": "expected",
            "readable": True,
        },
    }

    assert HeadlessView._value(
        values,
        "example",
    ) == "expected"


def test_actual_state_from_backend_module_verifies():
    actual = (
        HeadlessView._actual_state_from_module(
            _module()
        )
    )

    assert actual.status == Status.PASS

    settings = HeadlessSettings(
        desktop_user="operator"
    )

    assert verify(
        actual,
        settings,
    ).passed


from textual.app import App, ComposeResult
from textual.widgets import Input


class _HeadlessHarness(App):
    def compose(self) -> ComposeResult:
        yield HeadlessView()


async def _live_snapshot_loads_desktop_timeouts():
    app = _HeadlessHarness()

    async with app.run_test() as pilot:
        view = app.query_one(
            HeadlessView
        )

        view.update_snapshot(
            {},
            {
                "modules": {
                    "headless": _module(),
                    "power": {},
                },
            },
            True,
        )

        await pilot.pause()

        assert app.query_one(
            "#headless-desktop-user",
            Input,
        ).value == "operator"

        assert app.query_one(
            "#headless-user-ac-timeout",
            Input,
        ).value == "900"

        assert app.query_one(
            "#headless-user-battery-timeout",
            Input,
        ).value == "900"

        assert app.query_one(
            "#headless-gdm-ac-timeout",
            Input,
        ).value == "0"

        assert app.query_one(
            "#headless-gdm-battery-timeout",
            Input,
        ).value == "0"


async def _reset_to_live_restores_desktop_timeouts():
    app = _HeadlessHarness()

    async with app.run_test() as pilot:
        view = app.query_one(
            HeadlessView
        )

        view.update_snapshot(
            {},
            {
                "modules": {
                    "headless": _module(),
                    "power": {},
                },
            },
            True,
        )

        await pilot.pause()

        app.query_one(
            "#headless-user-ac-timeout",
            Input,
        ).value = "0"

        app.query_one(
            "#headless-user-battery-timeout",
            Input,
        ).value = "0"

        view._reset_draft()

        await pilot.pause()

        assert app.query_one(
            "#headless-user-ac-timeout",
            Input,
        ).value == "900"

        assert app.query_one(
            "#headless-user-battery-timeout",
            Input,
        ).value == "900"



def test_live_snapshot_loads_desktop_timeouts():
    asyncio.run(
        _live_snapshot_loads_desktop_timeouts()
    )


def test_reset_to_live_restores_desktop_timeouts():
    asyncio.run(
        _reset_to_live_restores_desktop_timeouts()
    )


from pathlib import Path


class _StyledHeadlessHarness(App):
    CSS_PATH = str(
        Path(
            "src/homelabctl/tui/homelabctl.tcss"
        ).resolve()
    )

    def compose(self) -> ComposeResult:
        yield HeadlessView()


async def _styled_headless_mounts():
    app = _StyledHeadlessHarness()

    async with app.run_test() as pilot:
        await pilot.pause()

        assert app.query_one(
            "#headless-preview-scroll"
        )

        assert app.query_one(
            "#headless-preview-content"
        )


def test_headless_mounts_with_real_stylesheet():
    asyncio.run(
        _styled_headless_mounts()
    )
