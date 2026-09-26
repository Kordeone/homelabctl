import asyncio
from pathlib import Path

from textual.app import (
    App,
    ComposeResult,
)
from textual.widgets import (
    Button,
    Input,
    Static,
)

from homelabctl.tui.screens.firewall import (
    FirewallView,
)
from homelabctl.tui.shell import (
    IMPLEMENTED_FEATURES,
)


def _module():
    raw = {
        "nft_available": True,
        "service_exists": True,
        "service_active": "active",
        "service_enabled": "enabled",
        "ruleset_present": True,
        "inet_filter_table": True,
        "input_policy_drop": True,
        "forward_policy_drop": True,
        "management_interface": "mgmt0",
        "management_ipv4_cidr": (
            "192.0.2.0/24"
        ),
        "ssh_port": 2222,
        "allow_dhcp_client": True,
        "allow_ipv4_icmp": False,
        "allow_ipv6_icmp": True,
    }

    return {
        "status": "pass",
        "summary": "test",
        "values": {
            key: {
                "value": value,
                "readable": True,
            }
            for key, value in raw.items()
        },
    }


class _FirewallHarness(App):
    CSS_PATH = str(
        Path(
            "src/homelabctl/tui/homelabctl.tcss"
        ).resolve()
    )

    def compose(self) -> ComposeResult:
        yield FirewallView()


async def _run_live_form_test():
    app = _FirewallHarness()

    async with app.run_test() as pilot:
        await pilot.pause()

        view = app.query_one(
            FirewallView
        )

        view.update_snapshot(
            {},
            {
                "modules": {
                    "firewall": _module(),
                }
            },
            True,
        )

        await pilot.pause()

        assert app.query_one(
            "#firewall-management-interface",
            Input,
        ).value == "mgmt0"

        assert app.query_one(
            "#firewall-management-cidr",
            Input,
        ).value == "192.0.2.0/24"

        assert app.query_one(
            "#firewall-ssh-port",
            Input,
        ).value == "2222"

        settings = (
            view._build_settings_from_form()
        )

        assert (
            settings.management_interface
            == "mgmt0"
        )

        assert (
            settings.management_ipv4_cidr
            == "192.0.2.0/24"
        )

        assert settings.ssh_port == 2222
        assert (
            settings.allow_dhcp_client
            is True
        )
        assert (
            settings.allow_ipv4_icmp
            is False
        )
        assert (
            settings.allow_ipv6_icmp
            is True
        )


def test_live_snapshot_loads_firewall_form():
    asyncio.run(
        _run_live_form_test()
    )


async def _run_reset_test():
    app = _FirewallHarness()

    async with app.run_test() as pilot:
        await pilot.pause()

        view = app.query_one(
            FirewallView
        )

        view.update_snapshot(
            {},
            {
                "modules": {
                    "firewall": _module(),
                }
            },
            True,
        )

        app.query_one(
            "#firewall-ssh-port",
            Input,
        ).value = "9999"

        view._render_preview()

        preview = app.query_one(
            "#firewall-preview-content",
            Static,
        )

        assert (
            "tcp dport 9999"
            in str(preview.content)
        )

        view._reset_draft()

        assert app.query_one(
            "#firewall-ssh-port",
            Input,
        ).value == "2222"

        reset_content = str(
            preview.content
        )

        assert (
            "Draft reset to the current live state."
            in reset_content
        )

        assert (
            "tcp dport 9999"
            not in reset_content
        )

        assert (
            "Press Preview"
            in reset_content
        )


def test_reset_restores_live_firewall_policy():
    asyncio.run(
        _run_reset_test()
    )


async def _run_preview_test():
    app = _FirewallHarness()

    async with app.run_test() as pilot:
        await pilot.pause()

        view = app.query_one(
            FirewallView
        )

        view.update_snapshot(
            {},
            {
                "modules": {
                    "firewall": _module(),
                }
            },
            True,
        )

        view._render_preview()

        content = app.query_one(
            "#firewall-preview-content",
            Static,
        )

        rendered = str(
            content.content
        )

        assert (
            'iifname "mgmt0"'
            in rendered
        )

        assert (
            "192.0.2.0/24"
            in rendered
        )

        assert (
            "tcp dport 2222"
            in rendered
        )


def test_preview_renders_desired_ruleset():
    asyncio.run(
        _run_preview_test()
    )


def test_firewall_is_implemented_feature():
    assert (
        "firewall"
        in IMPLEMENTED_FEATURES
    )


async def _run_safe_apply_control_test():
    app = _FirewallHarness()

    async with app.run_test() as pilot:
        await pilot.pause()

        view = app.query_one(
            FirewallView
        )

        view.update_snapshot(
            {},
            {
                "modules": {
                    "firewall": _module(),
                }
            },
            True,
        )

        await pilot.pause()

        apply = app.query_one(
            "#firewall-apply",
            Button,
        )

        confirm = app.query_one(
            "#firewall-confirm-connectivity",
            Button,
        )

        rollback = app.query_one(
            "#firewall-rollback-now",
            Button,
        )

        assert apply.disabled is True
        assert confirm.disabled is True
        assert rollback.disabled is True

        assert view._render_preview() is True
        assert apply.disabled is False

        view._set_pending_firewall_state(
            "a" * 32
        )

        assert apply.disabled is True
        assert confirm.disabled is False
        assert rollback.disabled is False

        view._set_pending_firewall_state(
            None
        )

        assert apply.disabled is True
        assert confirm.disabled is True
        assert rollback.disabled is True


def test_firewall_safe_apply_control_states():
    asyncio.run(
        _run_safe_apply_control_test()
    )
