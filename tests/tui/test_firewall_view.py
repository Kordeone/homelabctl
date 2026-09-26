import asyncio
from pathlib import Path

from textual.app import (
    App,
    ComposeResult,
)
from textual.widgets import (
    Button,
    ContentSwitcher,
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
        "trusted_ipv4_cidrs": [],
        "allowed_tcp_ports": [],
        "allowed_udp_ports": [],
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



async def _run_multi_page_architecture_test():
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

        switcher = app.query_one(
            "#firewall-pages",
            ContentSwitcher,
        )

        assert (
            switcher.current
            == "firewall-page-overview"
        )

        pages = (
            "overview",
            "access",
            "rules",
            "advanced",
        )

        for page in pages:
            app.query_one(
                f"#firewall-nav-{page}",
                Button,
            )

            view._show_page(
                page
            )

            assert (
                switcher.current
                == f"firewall-page-{page}"
            )

        assert app.query_one(
            "#firewall-management-interface",
            Input,
        )

        assert app.query_one(
            "#firewall-management-cidr",
            Input,
        )

        assert app.query_one(
            "#firewall-ssh-port",
            Input,
        )

        preview = app.query_one(
            "#firewall-preview",
            Button,
        )

        apply = app.query_one(
            "#firewall-apply",
            Button,
        )

        reset = app.query_one(
            "#firewall-reset",
            Button,
        )

        assert preview is not None
        assert apply is not None
        assert reset is not None

        for page in pages:
            view._show_page(
                page
            )

            assert app.query_one(
                "#firewall-preview",
                Button,
            ) is preview

            assert app.query_one(
                "#firewall-apply",
                Button,
            ) is apply


def test_firewall_multi_page_architecture():
    asyncio.run(
        _run_multi_page_architecture_test()
    )



async def _run_polished_layout_test():
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

        runtime = app.query_one(
            "#firewall-overview-runtime",
            Static,
        )

        management = app.query_one(
            "#firewall-overview-management",
            Static,
        )

        traffic = app.query_one(
            "#firewall-overview-traffic",
            Static,
        )

        policy = app.query_one(
            "#firewall-overview-policy",
            Static,
        )

        assert "active" in str(
            runtime.content
        )

        assert "mgmt0" in str(
            management.content
        )

        assert "IPv4 ICMP" in str(
            traffic.content
        )

        assert "Input" in str(
            policy.content
        )

        panel = app.query_one(
            "#firewall-actions-panel"
        )

        assert not panel.has_class(
            "preview-open"
        )

        assert view._render_preview() is True

        assert panel.has_class(
            "preview-open"
        )

        view._reset_draft()

        assert not panel.has_class(
            "preview-open"
        )


def test_firewall_polished_layout():
    asyncio.run(
        _run_polished_layout_test()
    )



async def _run_access_containment_test():
    app = _FirewallHarness()

    async with app.run_test(
        size=(160, 50)
    ) as pilot:
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

        view._show_page(
            "access"
        )

        await pilot.pause()

        management_panel = app.query_one(
            "#firewall-management-panel"
        )

        traffic_panel = app.query_one(
            "#firewall-traffic-panel"
        )

        management_controls = (
            app.query_one(
                "#firewall-management-interface"
            ),
            app.query_one(
                "#firewall-management-cidr"
            ),
            app.query_one(
                "#firewall-ssh-port"
            ),
        )

        traffic_controls = (
            app.query_one(
                "#firewall-dhcp"
            ),
            app.query_one(
                "#firewall-ipv4-icmp"
            ),
            app.query_one(
                "#firewall-ipv6-icmp"
            ),
        )

        for control in management_controls:
            assert control.region.height > 0
            assert (
                control.region.y
                >= management_panel.region.y
            )
            assert (
                control.region.bottom
                <= management_panel.region.bottom
            )

        for control in traffic_controls:
            assert control.region.height > 0
            assert (
                control.region.y
                >= traffic_panel.region.y
            )
            assert (
                control.region.bottom
                <= traffic_panel.region.bottom
            )


def test_firewall_access_controls_stay_inside_panels():
    asyncio.run(
        _run_access_containment_test()
    )


async def _run_rules_services_manager_test():
    from textual.widgets import DataTable

    from homelabctl.features.firewall.rules import (
        FirewallServiceRule,
    )

    app = _FirewallHarness()

    async with app.run_test(
        size=(160, 50)
    ) as pilot:
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

        view._show_page(
            "rules"
        )

        view._service_rules = [
            FirewallServiceRule(
                id="a" * 32,
                name="HTTPS",
                protocol="tcp",
                port=443,
                enabled=True,
            ),
            FirewallServiceRule(
                id="b" * 32,
                name="Jellyfin",
                protocol="tcp",
                port=8096,
                enabled=False,
            ),
            FirewallServiceRule(
                id="c" * 32,
                name="DNS",
                protocol="udp",
                port=53,
                enabled=True,
            ),
        ]

        view._service_rules_initialized = True

        view._render_service_rules_table()

        table = app.query_one(
            "#firewall-rules-table",
            DataTable,
        )

        assert table.row_count == 3

        assert not app.query_one(
            "#firewall-rule-add",
            Button,
        ).disabled

        assert not app.query_one(
            "#firewall-rule-edit",
            Button,
        ).disabled

        assert not app.query_one(
            "#firewall-rule-remove",
            Button,
        ).disabled

        assert not app.query_one(
            "#firewall-rule-toggle",
            Button,
        ).disabled

        settings = (
            view._build_settings_from_form()
        )

        assert (
            settings.allowed_tcp_ports
            == (
                443,
            )
        )

        assert (
            settings.allowed_udp_ports
            == (
                53,
            )
        )

        view._open_rule_editor(
            view._service_rules[0]
        )

        editor = app.query_one(
            "#firewall-rule-editor"
        )

        assert editor.has_class(
            "editing"
        )

        assert app.query_one(
            "#firewall-rule-name",
            Input,
        ).value == "HTTPS"

        assert app.query_one(
            "#firewall-rule-port",
            Input,
        ).value == "443"

        view._close_rule_editor()

        assert not editor.has_class(
            "editing"
        )


def test_firewall_rules_services_manager():
    asyncio.run(
        _run_rules_services_manager_test()
    )
