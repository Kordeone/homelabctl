"""Firewall feature content."""

from __future__ import annotations

from typing import Any

from homelabctl.apply.sudo import (
    confirm_firewall_transaction,
    rollback_firewall_transaction,
    run_privileged_transaction,
)
from homelabctl.features.firewall.apply import (
    build_apply_transaction,
)

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import (
    Grid,
    Horizontal,
    Vertical,
    VerticalScroll,
)
from textual.widgets import (
    Button,
    ContentSwitcher,
    Input,
    Static,
)

from homelabctl.apply.firewall_safety import (
    FIREWALL_ROLLBACK_TIMEOUT_SECONDS,
)
from homelabctl.core.actual_state import (
    make_actual_state,
)
from homelabctl.core.models import Status
from homelabctl.features.firewall.plan import (
    render_config,
)
from textual.widgets import DataTable

from homelabctl.features.firewall.rules import (
    FirewallServiceRule,
    compile_allowed_ports,
    load_managed_service_rules,
    new_service_rule,
    save_managed_service_rules,
    service_rules_from_active_ports,
    validate_service_rules,
)

from homelabctl.features.firewall.schema import (
    FirewallSettings,
)
from homelabctl.features.firewall.verify import (
    verify,
)
from homelabctl.tui.dialogs import (
    ConfirmDialog,
)
from homelabctl.tui.navigation import (
    NavigableView,
    SIDEBAR_TARGET,
    SpaceSelect,
)
from homelabctl.tui.screens.base import (
    ModuleScreen,
)


YES_NO = (
    ("Yes", "yes"),
    ("No", "no"),
)


class FirewallView(NavigableView):
    """nftables firewall management view."""

    ENTRY_ID = "firewall-nav-overview"

    BINDINGS = [
        Binding(
            "ctrl+1",
            "show_configure",
            "Configure",
            show=False,
        ),
        Binding(
            "ctrl+2",
            "show_inspect",
            "Inspect",
            show=False,
        ),
    ]

    NAVIGATION = {
        "firewall-nav-overview": {
            "left": SIDEBAR_TARGET,
            "right": "firewall-nav-access",
            "down": "firewall-preview",
        },
        "firewall-nav-access": {
            "left": "firewall-nav-overview",
            "right": "firewall-nav-rules",
            "down": "firewall-management-interface",
        },
        "firewall-nav-rules": {
            "left": "firewall-nav-access",
            "right": "firewall-nav-advanced",
            "down": "firewall-preview",
        },
        "firewall-nav-advanced": {
            "left": "firewall-nav-rules",
            "down": "firewall-preview",
        },

        "firewall-management-interface": {
            "left": SIDEBAR_TARGET,
            "up": "firewall-nav-access",
            "down": "firewall-management-cidr",
        },
        "firewall-management-cidr": {
            "left": SIDEBAR_TARGET,
            "up": "firewall-management-interface",
            "down": "firewall-ssh-port",
        },
        "firewall-ssh-port": {
            "left": SIDEBAR_TARGET,
            "up": "firewall-management-cidr",
            "down": "firewall-dhcp",
        },

        "firewall-dhcp": {
            "left": SIDEBAR_TARGET,
            "right": "firewall-ipv4-icmp",
            "up": "firewall-ssh-port",
        },
        "firewall-ipv4-icmp": {
            "left": "firewall-dhcp",
            "right": "firewall-ipv6-icmp",
            "up": "firewall-ssh-port",
        },
        "firewall-ipv6-icmp": {
            "left": "firewall-ipv4-icmp",
            "up": "firewall-ssh-port",
        },

        "firewall-preview": {
            "left": SIDEBAR_TARGET,
            "right": "firewall-reset",
            "up": "firewall-nav-advanced",
        },
        "firewall-reset": {
            "left": "firewall-preview",
            "right": "firewall-apply",
            "up": "firewall-nav-advanced",
        },
        "firewall-apply": {
            "left": "firewall-reset",
            "right": "firewall-confirm-connectivity",
            "up": "firewall-nav-advanced",
        },
        "firewall-confirm-connectivity": {
            "left": "firewall-apply",
            "right": "firewall-rollback-now",
            "up": "firewall-nav-advanced",
        },
        "firewall-rollback-now": {
            "left": "firewall-confirm-connectivity",
            "up": "firewall-nav-advanced",
        },
    }

    def __init__(self) -> None:
        super().__init__(
            id="firewall-view"
        )

        self._page = "overview"
        self._backend_online = False
        self._module: dict[str, Any] = {}
        self._draft_initialized = False

        self._pending_firewall_apply: Any | None = None
        self._pending_firewall_confirmation_id: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical(
            id="firewall-root"
        ):
            with Horizontal(
                id="firewall-feature-header"
            ):
                yield Static(
                    "Firewall",
                    id="firewall-title",
                )

                yield Static(
                    "UNKNOWN",
                    id="firewall-status",
                )

            with Horizontal(
                id="firewall-section-nav"
            ):
                yield Button(
                    "Overview",
                    id="firewall-nav-overview",
                    classes=(
                        "firewall-section-button "
                        "active-page-tab"
                    ),
                )

                yield Button(
                    "Access & Network",
                    id="firewall-nav-access",
                    classes="firewall-section-button",
                )

                yield Button(
                    "Rules & Services",
                    id="firewall-nav-rules",
                    classes="firewall-section-button",
                )

                yield Button(
                    "Advanced",
                    id="firewall-nav-advanced",
                    classes="firewall-section-button",
                )

            with ContentSwitcher(
                initial="firewall-page-overview",
                id="firewall-pages",
            ):
                with VerticalScroll(
                    id="firewall-page-overview",
                    classes="firewall-section-page",
                ):
                    with Horizontal(
                        classes="firewall-overview-row"
                    ):
                        with Vertical(
                            classes=(
                                "firewall-panel "
                                "firewall-summary-card"
                            ),
                        ):
                            yield Static(
                                "Runtime",
                                classes="firewall-panel-title",
                            )

                            yield Static(
                                "",
                                id="firewall-overview-runtime",
                                markup=False,
                            )

                        with Vertical(
                            classes=(
                                "firewall-panel "
                                "firewall-summary-card"
                            ),
                        ):
                            yield Static(
                                "Management",
                                classes="firewall-panel-title",
                            )

                            yield Static(
                                "",
                                id="firewall-overview-management",
                                markup=False,
                            )

                    with Horizontal(
                        classes="firewall-overview-row"
                    ):
                        with Vertical(
                            classes=(
                                "firewall-panel "
                                "firewall-summary-card"
                            ),
                        ):
                            yield Static(
                                "Traffic",
                                classes="firewall-panel-title",
                            )

                            yield Static(
                                "",
                                id="firewall-overview-traffic",
                                markup=False,
                            )

                        with Vertical(
                            classes=(
                                "firewall-panel "
                                "firewall-summary-card"
                            ),
                        ):
                            yield Static(
                                "Policy",
                                classes="firewall-panel-title",
                            )

                            yield Static(
                                "",
                                id="firewall-overview-policy",
                                markup=False,
                            )

                with VerticalScroll(
                    id="firewall-page-access",
                    classes="firewall-section-page",
                ):
                    with Horizontal(
                        id="firewall-access-top"
                    ):
                        with Vertical(
                            id="firewall-management-panel",
                            classes=(
                                "firewall-panel "
                                "firewall-access-panel"
                            ),
                        ):
                            yield Static(
                                "Management Access",
                                classes="firewall-panel-title",
                            )

                            yield Static(
                                "Management interface",
                                classes="firewall-field-label",
                            )

                            yield Input(
                                id=(
                                    "firewall-management-interface"
                                ),
                            )

                            yield Static(
                                "Management IPv4 CIDR",
                                classes="firewall-field-label",
                            )

                            yield Input(
                                id=(
                                    "firewall-management-cidr"
                                ),
                            )

                            yield Static(
                                "SSH port",
                                classes="firewall-field-label",
                            )

                            yield Input(
                                id="firewall-ssh-port",
                                type="integer",
                            )

                        with Vertical(
                            id="firewall-trusted-panel",
                            classes=(
                                "firewall-panel "
                                "firewall-access-panel"
                            ),
                        ):
                            yield Static(
                                "Trusted Networks",
                                classes="firewall-panel-title",
                            )

                            yield Static(
                                "",
                                id="firewall-networks-content",
                                markup=False,
                            )

                            yield Static(
                                (
                                    "Add / Edit / Remove "
                                    "manager comes next."
                                ),
                                classes="firewall-section-note",
                            )

                    with Vertical(
                        id="firewall-traffic-panel",
                        classes="firewall-panel",
                    ):
                        yield Static(
                            "Network Traffic",
                            classes="firewall-panel-title",
                        )

                        with Horizontal(
                            id="firewall-traffic-row"
                        ):
                            with Vertical(
                                classes=(
                                    "firewall-traffic-setting"
                                ),
                            ):
                                yield Static(
                                    "DHCP client replies",
                                    classes=(
                                        "firewall-field-label"
                                    ),
                                )

                                yield SpaceSelect(
                                    YES_NO,
                                    value="yes",
                                    allow_blank=False,
                                    id="firewall-dhcp",
                                )

                            with Vertical(
                                classes=(
                                    "firewall-traffic-setting"
                                ),
                            ):
                                yield Static(
                                    "IPv4 ICMP",
                                    classes=(
                                        "firewall-field-label"
                                    ),
                                )

                                yield SpaceSelect(
                                    YES_NO,
                                    value="yes",
                                    allow_blank=False,
                                    id="firewall-ipv4-icmp",
                                )

                            with Vertical(
                                classes=(
                                    "firewall-traffic-setting"
                                ),
                            ):
                                yield Static(
                                    "IPv6 ICMP",
                                    classes=(
                                        "firewall-field-label"
                                    ),
                                )

                                yield SpaceSelect(
                                    YES_NO,
                                    value="yes",
                                    allow_blank=False,
                                    id="firewall-ipv6-icmp",
                                )

                with VerticalScroll(
                    id="firewall-page-rules",
                    classes="firewall-section-page",
                ):
                    with Horizontal(
                        id="firewall-rules-layout"
                    ):
                        with Vertical(
                            id="firewall-rules-list-panel",
                            classes="firewall-panel",
                        ):
                            yield Static(
                                "Rules & Services",
                                classes="firewall-panel-title",
                            )

                            yield Static(
                                (
                                    "Inbound services allowed from "
                                    "Trusted Networks on the "
                                    "Management interface."
                                ),
                                classes="firewall-section-note",
                            )

                            yield DataTable(
                                id="firewall-rules-table",
                            )

                            with Horizontal(
                                id="firewall-rule-actions"
                            ):
                                yield Button(
                                    "+ Add",
                                    id="firewall-rule-add",
                                    variant="primary",
                                )

                                yield Button(
                                    "Edit",
                                    id="firewall-rule-edit",
                                    disabled=True,
                                )

                                yield Button(
                                    "Remove",
                                    id="firewall-rule-remove",
                                    disabled=True,
                                )

                                yield Button(
                                    "Enable / Disable",
                                    id="firewall-rule-toggle",
                                    disabled=True,
                                )

                        with Vertical(
                            id="firewall-rule-editor"
                        ):
                            yield Static(
                                "Add Service",
                                id="firewall-rule-editor-title",
                                classes="firewall-panel-title",
                            )

                            yield Static(
                                "Name",
                                classes="firewall-field-label",
                            )

                            yield Input(
                                id="firewall-rule-name",
                                placeholder="e.g. Jellyfin",
                            )

                            yield Static(
                                "Protocol",
                                classes="firewall-field-label",
                            )

                            yield SpaceSelect(
                                [
                                    ("TCP", "tcp"),
                                    ("UDP", "udp"),
                                ],
                                value="tcp",
                                allow_blank=False,
                                id="firewall-rule-protocol",
                            )

                            yield Static(
                                "Port",
                                classes="firewall-field-label",
                            )

                            yield Input(
                                id="firewall-rule-port",
                                type="integer",
                                placeholder="1-65535",
                            )

                            yield Static(
                                (
                                    "Source: Trusted Networks\n"
                                    "Interface: Management\n"
                                    "Action: Allow"
                                ),
                                id="firewall-rule-fixed-policy",
                                markup=False,
                            )

                            with Horizontal(
                                id="firewall-rule-editor-actions"
                            ):
                                yield Button(
                                    "Save",
                                    id="firewall-rule-save",
                                    variant="primary",
                                )

                                yield Button(
                                    "Cancel",
                                    id="firewall-rule-cancel",
                                )
                with VerticalScroll(
                    id="firewall-page-advanced",
                    classes="firewall-section-page",
                ):
                    with Horizontal(
                        classes="firewall-advanced-row"
                    ):
                        with Vertical(
                            classes=(
                                "firewall-panel "
                                "firewall-advanced-panel"
                            ),
                        ):
                            yield Static(
                                "Default Policies",
                                classes="firewall-panel-title",
                            )

                            yield Static(
                                "",
                                id="firewall-policies-content",
                                markup=False,
                            )

                        with Vertical(
                            classes=(
                                "firewall-panel "
                                "firewall-advanced-panel"
                            ),
                        ):
                            yield Static(
                                "Logging & Protection",
                                classes="firewall-panel-title",
                            )

                            yield Static(
                                (
                                    "Drop logging, counters, "
                                    "rate limits, and protection "
                                    "controls will live here."
                                ),
                                id="firewall-logging-content",
                                markup=False,
                            )

                    with Horizontal(
                        classes="firewall-advanced-row"
                    ):
                        with Vertical(
                            classes=(
                                "firewall-panel "
                                "firewall-advanced-panel"
                            ),
                        ):
                            yield Static(
                                "Diagnostics",
                                classes="firewall-panel-title",
                            )

                            yield Static(
                                "",
                                id=(
                                    "firewall-verification-content"
                                ),
                                markup=False,
                            )

                        with Vertical(
                            classes=(
                                "firewall-panel "
                                "firewall-advanced-panel"
                            ),
                        ):
                            yield Static(
                                "Runtime / Safety",
                                classes="firewall-panel-title",
                            )

                            yield Static(
                                "",
                                id="firewall-runtime-content",
                                markup=False,
                            )

            with Vertical(
                id="firewall-actions-panel",
            ):
                with Horizontal(
                    id="firewall-change-actions"
                ):
                    yield Static(
                        "Change Control",
                        id="firewall-change-title",
                    )

                    yield Static(
                        (
                            "No pending apply · guarded "
                            f"{FIREWALL_ROLLBACK_TIMEOUT_SECONDS}s "
                            "rollback"
                        ),
                        id="firewall-safety-note",
                    )

                    yield Button(
                        "Preview",
                        id="firewall-preview",
                        variant="primary",
                    )

                    yield Button(
                        "Reset",
                        id="firewall-reset",
                    )

                    yield Button(
                        "Apply",
                        id="firewall-apply",
                        disabled=True,
                    )

                    yield Button(
                        "Confirm Connectivity",
                        id=(
                            "firewall-confirm-connectivity"
                        ),
                        disabled=True,
                    )

                    yield Button(
                        "Rollback Now",
                        id="firewall-rollback-now",
                        disabled=True,
                    )

                with VerticalScroll(
                    id="firewall-preview-scroll"
                ):
                    yield Static(
                        (
                            "Press Preview to review the "
                            "complete desired nftables "
                            "configuration."
                        ),
                        id="firewall-preview-content",
                        markup=False,
                    )

    def action_show_configure(
        self,
    ) -> None:
        self._show_page(
            "access"
        )

    def action_show_inspect(
        self,
    ) -> None:
        self._show_page(
            "advanced"
        )

    def _show_page(
        self,
        page: str,
    ) -> None:
        pages = (
            "overview",
            "access",
            "rules",
            "advanced",
        )

        if page not in pages:
            page = "overview"

        switcher = self.query_one(
            "#firewall-pages",
            ContentSwitcher,
        )

        switcher.current = (
            f"firewall-page-{page}"
        )

        for name in pages:
            button = self.query_one(
                f"#firewall-nav-{name}",
                Button,
            )

            if name == page:
                button.add_class(
                    "active-page-tab"
                )
            else:
                button.remove_class(
                    "active-page-tab"
                )

        self._page = page

    @staticmethod
    def _wire_value(
        wire: dict[str, Any],
        key: str,
        default: Any = None,
    ) -> Any:
        item = wire.get(
            key
        )

        if (
            isinstance(
                item,
                dict,
            )
            and "value" in item
        ):
            return item.get(
                "value",
                default,
            )

        if item is None:
            return default

        return item

    def _values(
        self,
    ) -> dict[str, Any]:
        wire = self._module.get(
            "values",
            {},
        )

        if not isinstance(
            wire,
            dict,
        ):
            return {}

        return {
            key: self._wire_value(
                wire,
                key,
            )
            for key in wire
        }

    def update_snapshot(
        self,
        ping: dict[str, Any],
        snapshot: dict[str, Any],
        backend_online: bool,
    ) -> None:
        del ping

        self._backend_online = (
            backend_online
        )

        modules = snapshot.get(
            "modules",
            {},
        )

        if not isinstance(
            modules,
            dict,
        ):
            modules = {}

        module = modules.get(
            "firewall",
            {},
        )

        self._module = (
            module
            if isinstance(
                module,
                dict,
            )
            else {}
        )

        if (
            not self._draft_initialized
            and self._can_load_live_policy()
        ):
            self._load_live_state_into_form()
            self._draft_initialized = True

        self._render_current_state()
        self._render_section_summaries()
        self._render_verification()
        self._render_runtime_state()

    def _can_load_live_policy(
        self,
    ) -> bool:
        values = self._values()

        return all(
            values.get(
                key
            )
            is not None
            for key in (
                "management_interface",
                "management_ipv4_cidr",
                "ssh_port",
                "allow_dhcp_client",
                "allow_ipv4_icmp",
                "allow_ipv6_icmp",
            )
        )

    def _set_select_bool(
        self,
        selector: str,
        value: bool,
    ) -> None:
        self.query_one(
            selector,
            SpaceSelect,
        ).value = (
            "yes"
            if value
            else "no"
        )

    def _load_live_state_into_form(
        self,
    ) -> None:
        values = self._values()

        if not self._can_load_live_policy():
            return

        self.query_one(
            "#firewall-management-interface",
            Input,
        ).value = str(
            values[
                "management_interface"
            ]
        )

        self.query_one(
            "#firewall-management-cidr",
            Input,
        ).value = str(
            values[
                "management_ipv4_cidr"
            ]
        )

        self.query_one(
            "#firewall-ssh-port",
            Input,
        ).value = str(
            values[
                "ssh_port"
            ]
        )

        self._set_select_bool(
            "#firewall-dhcp",
            bool(
                values[
                    "allow_dhcp_client"
                ]
            ),
        )

        self._set_select_bool(
            "#firewall-ipv4-icmp",
            bool(
                values[
                    "allow_ipv4_icmp"
                ]
            ),
        )

        self._set_select_bool(
            "#firewall-ipv6-icmp",
            bool(
                values[
                    "allow_ipv6_icmp"
                ]
            ),
        )

    def _select_bool(
        self,
        selector: str,
    ) -> bool:
        value = self.query_one(
            selector,
            SpaceSelect,
        ).value

        if value == "yes":
            return True

        if value == "no":
            return False

        raise ValueError(
            "Select a Yes/No value."
        )

    def _build_settings_from_form(
        self,
    ) -> FirewallSettings:
        raw_port = self.query_one(
            "#firewall-ssh-port",
            Input,
        ).value.strip()

        try:
            ssh_port = int(
                raw_port
            )
        except ValueError as exc:
            raise ValueError(
                "SSH port must be an integer."
            ) from exc

        self._ensure_service_rules_loaded()

        allowed_tcp_ports, allowed_udp_ports = (
            compile_allowed_ports(
                tuple(
                    self._service_rules
                )
            )
        )

        live_values = self._values()

        raw_trusted = live_values.get(
            "trusted_ipv4_cidrs"
        )

        if raw_trusted is None:
            raise ValueError(
                "Trusted network state is unreadable."
            )

        trusted_ipv4_cidrs = tuple(
            str(value)
            for value in raw_trusted
        )

        settings = FirewallSettings(
            management_interface=(
                self.query_one(
                    "#firewall-management-interface",
                    Input,
                ).value.strip()
            ),
            management_ipv4_cidr=(
                self.query_one(
                    "#firewall-management-cidr",
                    Input,
                ).value.strip()
            ),
            ssh_port=ssh_port,
            allow_dhcp_client=(
                self._select_bool(
                    "#firewall-dhcp"
                )
            ),
            allow_ipv4_icmp=(
                self._select_bool(
                    "#firewall-ipv4-icmp"
                )
            ),
            allow_ipv6_icmp=(
                self._select_bool(
                    "#firewall-ipv6-icmp"
                )
            ),
            trusted_ipv4_cidrs=(
                trusted_ipv4_cidrs
            ),
            allowed_tcp_ports=(
                allowed_tcp_ports
            ),
            allowed_udp_ports=(
                allowed_udp_ports
            ),
        )

        settings.validate()

        return settings

    def _actual_state(
        self,
    ):
        if not self._module:
            return None

        values = self._values()

        raw_status = self._module.get(
            "status",
            "unknown",
        )

        try:
            status = Status(
                raw_status
            )
        except ValueError:
            status = Status.UNKNOWN

        return make_actual_state(
            "firewall",
            status=status,
            summary=str(
                self._module.get(
                    "summary",
                    "",
                )
            ),
            values=values,
        )

    @staticmethod
    def _yes_no(
        value: Any,
    ) -> str:
        if value is True:
            return "yes"

        if value is False:
            return "no"

        return "--"

    def _render_current_state(
        self,
    ) -> None:
        status_target = self.query_one(
            "#firewall-status",
            Static,
        )

        cards = (
            self.query_one(
                "#firewall-overview-runtime",
                Static,
            ),
            self.query_one(
                "#firewall-overview-management",
                Static,
            ),
            self.query_one(
                "#firewall-overview-traffic",
                Static,
            ),
            self.query_one(
                "#firewall-overview-policy",
                Static,
            ),
        )

        if not self._backend_online:
            status_target.update(
                "[red]OFFLINE[/red]"
            )

            for card in cards:
                card.update(
                    "Backend unavailable."
                )

            return

        values = self._values()

        raw_status = str(
            self._module.get(
                "status",
                "unknown",
            )
        ).upper()

        status_target.update(
            raw_status
        )

        trusted = (
            values.get(
                "trusted_ipv4_cidrs"
            )
            or []
        )

        tcp_ports = (
            values.get(
                "allowed_tcp_ports"
            )
            or []
        )

        udp_ports = (
            values.get(
                "allowed_udp_ports"
            )
            or []
        )

        cards[0].update(
            "\n".join(
                [
                    (
                        "nftables   "
                        + self._yes_no(
                            values.get(
                                "nft_available"
                            )
                        )
                    ),
                    (
                        "Service    "
                        + str(
                            values.get(
                                "service_active",
                                "--",
                            )
                        )
                    ),
                    (
                        "Enabled    "
                        + str(
                            values.get(
                                "service_enabled",
                                "--",
                            )
                        )
                    ),
                    (
                        "Ruleset    "
                        + self._yes_no(
                            values.get(
                                "ruleset_present"
                            )
                        )
                    ),
                ]
            )
        )

        cards[1].update(
            "\n".join(
                [
                    (
                        "Interface  "
                        + str(
                            values.get(
                                "management_interface",
                                "--",
                            )
                        )
                    ),
                    (
                        "Network    "
                        + str(
                            values.get(
                                "management_ipv4_cidr",
                                "--",
                            )
                        )
                    ),
                    (
                        "SSH port   "
                        + str(
                            values.get(
                                "ssh_port",
                                "--",
                            )
                        )
                    ),
                    (
                        "Trusted    "
                        + str(
                            len(
                                trusted
                            )
                        )
                    ),
                ]
            )
        )

        cards[2].update(
            "\n".join(
                [
                    (
                        "DHCP       "
                        + self._yes_no(
                            values.get(
                                "allow_dhcp_client"
                            )
                        )
                    ),
                    (
                        "IPv4 ICMP  "
                        + self._yes_no(
                            values.get(
                                "allow_ipv4_icmp"
                            )
                        )
                    ),
                    (
                        "IPv6 ICMP  "
                        + self._yes_no(
                            values.get(
                                "allow_ipv6_icmp"
                            )
                        )
                    ),
                    (
                        "Ports      "
                        + str(
                            len(tcp_ports)
                            + len(udp_ports)
                        )
                    ),
                ]
            )
        )

        cards[3].update(
            "\n".join(
                [
                    (
                        "Input      "
                        + (
                            "DROP"
                            if values.get(
                                "input_policy_drop"
                            )
                            else "--"
                        )
                    ),
                    (
                        "Forward    "
                        + (
                            "DROP"
                            if values.get(
                                "forward_policy_drop"
                            )
                            else "--"
                        )
                    ),
                ]
            )
        )

    def _service_rules_from_live(
        self,
    ) -> tuple[
        FirewallServiceRule,
        ...,
    ]:
        values = self._values()

        tcp_ports = values.get(
            "allowed_tcp_ports"
        )

        udp_ports = values.get(
            "allowed_udp_ports"
        )

        if (
            tcp_ports is None
            or udp_ports is None
        ):
            raise ValueError(
                "Active service-rule state is unreadable."
            )

        current = tuple(
            getattr(
                self,
                "_service_rules",
                (),
            )
        )

        existing = {
            (
                rule.protocol,
                rule.port,
            ): rule
            for rule in current
        }

        generated = (
            service_rules_from_active_ports(
                tcp_ports=tcp_ports,
                udp_ports=udp_ports,
            )
        )

        preserved = []

        for rule in generated:
            old = existing.get(
                (
                    rule.protocol,
                    rule.port,
                )
            )

            if old is None:
                preserved.append(
                    rule
                )
                continue

            preserved.append(
                FirewallServiceRule(
                    id=old.id,
                    name=old.name,
                    protocol=rule.protocol,
                    port=rule.port,
                    enabled=True,
                )
            )

        return validate_service_rules(
            preserved
        )

    def _ensure_service_rules_loaded(
        self,
    ) -> None:
        if getattr(
            self,
            "_service_rules_initialized",
            False,
        ):
            return

        try:
            managed = (
                load_managed_service_rules()
            )
        except Exception as exc:
            self.notify(
                (
                    "Stored firewall service rules "
                    f"could not be loaded: {exc}"
                ),
                severity="warning",
                timeout=6,
            )

            managed = None

        try:
            rules = (
                managed
                if managed is not None
                else self._service_rules_from_live()
            )
        except Exception as exc:
            self.notify(
                (
                    "Live firewall service rules "
                    f"could not be read: {exc}"
                ),
                severity="error",
                timeout=6,
            )

            rules = ()

        self._service_rules = list(
            rules
        )

        self._service_rules_initialized = (
            True
        )

    def _persist_service_rules(
        self,
        rules: tuple[
            FirewallServiceRule,
            ...,
        ],
    ) -> None:
        save_managed_service_rules(
            rules
        )

        self._service_rules = list(
            rules
        )

        self._service_rules_initialized = (
            True
        )

    def _render_service_rules_table(
        self,
    ) -> None:
        self._ensure_service_rules_loaded()

        table = self.query_one(
            "#firewall-rules-table",
            DataTable,
        )

        if not table.columns:
            table.add_columns(
                "Name",
                "Protocol",
                "Port",
                "Source",
                "Enabled",
            )

        table.clear(
            columns=False
        )

        rules = tuple(
            self._service_rules
        )

        for rule in rules:
            table.add_row(
                rule.name,
                rule.protocol.upper(),
                str(rule.port),
                "Trusted",
                (
                    "Yes"
                    if rule.enabled
                    else "No"
                ),
                key=rule.id,
            )

        has_rules = bool(
            rules
        )

        for selector in (
            "#firewall-rule-edit",
            "#firewall-rule-remove",
            "#firewall-rule-toggle",
        ):
            self.query_one(
                selector,
                Button,
            ).disabled = not has_rules

    def _selected_service_rule(
        self,
    ) -> FirewallServiceRule | None:
        self._ensure_service_rules_loaded()

        if not self._service_rules:
            return None

        table = self.query_one(
            "#firewall-rules-table",
            DataTable,
        )

        index = table.cursor_row

        if (
            index < 0
            or index >= len(
                self._service_rules
            )
        ):
            index = 0

        return self._service_rules[
            index
        ]

    def _set_rule_editor_open(
        self,
        open_: bool,
    ) -> None:
        editor = self.query_one(
            "#firewall-rule-editor"
        )

        editor.set_class(
            open_,
            "editing",
        )

    def _open_rule_editor(
        self,
        rule: FirewallServiceRule | None,
    ) -> None:
        self._editing_service_rule_id = (
            None
            if rule is None
            else rule.id
        )

        self.query_one(
            "#firewall-rule-editor-title",
            Static,
        ).update(
            "Add Service"
            if rule is None
            else "Edit Service"
        )

        self.query_one(
            "#firewall-rule-name",
            Input,
        ).value = (
            ""
            if rule is None
            else rule.name
        )

        self.query_one(
            "#firewall-rule-protocol",
            SpaceSelect,
        ).value = (
            "tcp"
            if rule is None
            else rule.protocol
        )

        self.query_one(
            "#firewall-rule-port",
            Input,
        ).value = (
            ""
            if rule is None
            else str(
                rule.port
            )
        )

        self._set_rule_editor_open(
            True
        )

        self.query_one(
            "#firewall-rule-name",
            Input,
        ).focus()

    def _close_rule_editor(
        self,
    ) -> None:
        self._editing_service_rule_id = (
            None
        )

        self._set_rule_editor_open(
            False
        )

    def _mark_service_rules_dirty(
        self,
    ) -> None:
        self._set_preview_expanded(
            False
        )

        self.query_one(
            "#firewall-preview-content",
            Static,
        ).update(
            "Rules & Services changed.\n\n"
            "Press Preview to review the desired "
            "nftables configuration."
        )

        self.query_one(
            "#firewall-apply",
            Button,
        ).disabled = True

        self._render_service_rules_table()

    def _save_rule_editor(
        self,
    ) -> None:
        self._ensure_service_rules_loaded()

        name = self.query_one(
            "#firewall-rule-name",
            Input,
        ).value.strip()

        protocol_value = self.query_one(
            "#firewall-rule-protocol",
            SpaceSelect,
        ).value

        protocol = str(
            protocol_value
        ).strip().lower()

        raw_port = self.query_one(
            "#firewall-rule-port",
            Input,
        ).value.strip()

        try:
            port = int(
                raw_port
            )
        except ValueError:
            self.notify(
                "Port must be an integer.",
                severity="error",
                timeout=5,
            )
            return

        editing_id = getattr(
            self,
            "_editing_service_rule_id",
            None,
        )

        try:
            if editing_id is None:
                rule = new_service_rule(
                    name=name,
                    protocol=protocol,
                    port=port,
                )

                candidate = (
                    *self._service_rules,
                    rule,
                )

            else:
                old = next(
                    (
                        item
                        for item in self._service_rules
                        if item.id == editing_id
                    ),
                    None,
                )

                if old is None:
                    raise ValueError(
                        "The selected service rule "
                        "no longer exists."
                    )

                replacement = (
                    FirewallServiceRule(
                        id=old.id,
                        name=name,
                        protocol=protocol,
                        port=port,
                        enabled=old.enabled,
                    )
                )

                replacement.validate()

                candidate = tuple(
                    (
                        replacement
                        if item.id == editing_id
                        else item
                    )
                    for item in self._service_rules
                )

            normalized = (
                validate_service_rules(
                    candidate
                )
            )

            self._persist_service_rules(
                normalized
            )

        except Exception as exc:
            self.notify(
                f"Could not save service rule: {exc}",
                severity="error",
                timeout=6,
            )
            return

        self._close_rule_editor()
        self._mark_service_rules_dirty()

        self.notify(
            "Service rule saved.",
            timeout=4,
        )

    def _toggle_selected_service_rule(
        self,
    ) -> None:
        rule = (
            self._selected_service_rule()
        )

        if rule is None:
            return

        replacement = FirewallServiceRule(
            id=rule.id,
            name=rule.name,
            protocol=rule.protocol,
            port=rule.port,
            enabled=not rule.enabled,
        )

        candidate = tuple(
            (
                replacement
                if item.id == rule.id
                else item
            )
            for item in self._service_rules
        )

        try:
            self._persist_service_rules(
                validate_service_rules(
                    candidate
                )
            )
        except Exception as exc:
            self.notify(
                (
                    "Could not change service rule: "
                    f"{exc}"
                ),
                severity="error",
                timeout=6,
            )
            return

        self._mark_service_rules_dirty()

    def _request_remove_service_rule(
        self,
    ) -> None:
        rule = (
            self._selected_service_rule()
        )

        if rule is None:
            return

        self._pending_service_rule_removal = (
            rule.id
        )

        self.app.push_screen(
            ConfirmDialog(
                title="Remove service rule",
                message=(
                    f"Remove {rule.name} "
                    f"({rule.protocol.upper()} "
                    f"{rule.port}) from the desired "
                    "firewall configuration?"
                ),
            ),
            self._on_service_rule_remove_confirmed,
        )

    def _on_service_rule_remove_confirmed(
        self,
        confirmed: bool,
    ) -> None:
        rule_id = getattr(
            self,
            "_pending_service_rule_removal",
            None,
        )

        self._pending_service_rule_removal = (
            None
        )

        if (
            not confirmed
            or rule_id is None
        ):
            return

        candidate = tuple(
            rule
            for rule in self._service_rules
            if rule.id != rule_id
        )

        try:
            self._persist_service_rules(
                validate_service_rules(
                    candidate
                )
            )
        except Exception as exc:
            self.notify(
                (
                    "Could not remove service rule: "
                    f"{exc}"
                ),
                severity="error",
                timeout=6,
            )
            return

        self._close_rule_editor()
        self._mark_service_rules_dirty()

        self.notify(
            "Service rule removed.",
            timeout=4,
        )

    def _reset_service_rules_to_live(
        self,
    ) -> None:
        try:
            rules = (
                self._service_rules_from_live()
            )

            self._persist_service_rules(
                rules
            )

        except Exception as exc:
            self.notify(
                (
                    "Could not reset service rules "
                    f"to live state: {exc}"
                ),
                severity="error",
                timeout=6,
            )
            return

        self._close_rule_editor()
        self._render_service_rules_table()

    def _render_section_summaries(
        self,
    ) -> None:
        values = self._values()

        trusted = (
            values.get(
                "trusted_ipv4_cidrs"
            )
            or []
        )

        tcp_ports = (
            values.get(
                "allowed_tcp_ports"
            )
            or []
        )

        udp_ports = (
            values.get(
                "allowed_udp_ports"
            )
            or []
        )

        networks = self.query_one(
            "#firewall-networks-content",
            Static,
        )

        if trusted:
            networks.update(
                "Current trusted networks:\n\n"
                + "\n".join(
                    f"  {value}"
                    for value in trusted
                )
            )
        else:
            networks.update(
                "No additional trusted networks."
            )

        self._ensure_service_rules_loaded()
        self._render_service_rules_table()

        policies = self.query_one(
            "#firewall-policies-content",
            Static,
        )

        policies.update(
            "\n".join(
                [
                    (
                        "Input DROP: "
                        + self._yes_no(
                            values.get(
                                "input_policy_drop"
                            )
                        )
                    ),
                    (
                        "Forward DROP: "
                        + self._yes_no(
                            values.get(
                                "forward_policy_drop"
                            )
                        )
                    ),
                ]
            )
        )

    def _set_preview_expanded(
        self,
        expanded: bool,
    ) -> None:
        panel = self.query_one(
            "#firewall-actions-panel"
        )

        if expanded:
            panel.add_class(
                "preview-open"
            )
        else:
            panel.remove_class(
                "preview-open"
            )

    def _render_preview(
        self,
    ) -> bool:
        self._set_preview_expanded(
            True
        )
        target = self.query_one(
            "#firewall-preview-content",
            Static,
        )

        try:
            settings = (
                self._build_settings_from_form()
            )

            rendered = render_config(
                settings
            )

        except Exception as exc:
            target.update(
                f"Validation error:\n{exc}"
            )

            self.query_one(
                "#firewall-apply",
                Button,
            ).disabled = True

            return False

        target.update(
            rendered
        )

        if (
            self._pending_firewall_confirmation_id
            is None
        ):
            self.query_one(
                "#firewall-apply",
                Button,
            ).disabled = False

        return True

    def _render_verification(
        self,
    ) -> None:
        target = self.query_one(
            "#firewall-verification-content",
            Static,
        )

        if (
            not self._backend_online
            or not self._module
        ):
            target.update(
                "No live Firewall state."
            )
            return

        try:
            settings = (
                self._build_settings_from_form()
            )
        except Exception as exc:
            target.update(
                f"Desired policy invalid:\n{exc}"
            )
            return

        report = verify(
            self._actual_state(),
            settings,
        )

        lines = [
            (
                "Result: "
                + (
                    "PASS"
                    if report.passed
                    else "DRIFT"
                )
            ),
            "",
        ]

        for check in report.checks:
            lines.append(
                (
                    "PASS "
                    if check.passed
                    else "FAIL "
                )
                + check.key
            )

            if not check.passed:
                lines.append(
                    (
                        "  desired: "
                        f"{check.expected!r}"
                    )
                )

                lines.append(
                    (
                        "  actual:  "
                        f"{check.actual!r}"
                    )
                )

        target.update(
            "\n".join(
                lines
            )
        )

    def _render_runtime_state(
        self,
    ) -> None:
        target = self.query_one(
            "#firewall-runtime-content",
            Static,
        )

        values = self._values()

        target.update(
            "\n".join(
                [
                    (
                        "Service exists: "
                        f"{self._yes_no(values.get('service_exists'))}"
                    ),
                    (
                        "Service active: "
                        f"{values.get('service_active', '--')}"
                    ),
                    (
                        "Service enabled: "
                        f"{values.get('service_enabled', '--')}"
                    ),
                    (
                        "Ruleset present: "
                        f"{self._yes_no(values.get('ruleset_present'))}"
                    ),
                    (
                        "inet filter table: "
                        f"{self._yes_no(values.get('inet_filter_table'))}"
                    ),
                    "",
                    (
                        "Timed rollback: "
                        f"{FIREWALL_ROLLBACK_TIMEOUT_SECONDS}s"
                    ),
                    (
                        "Connectivity confirmation: "
                        "required after Apply"
                    ),
                    "",
                    (
                        "No firewall mutation is "
                        "performed by this UI stage."
                    ),
                ]
            )
        )

    def _reset_draft(
        self,
    ) -> None:
        self._set_preview_expanded(
            False
        )
        self._load_live_state_into_form()
        self._reset_service_rules_to_live()

        self.query_one(
            "#firewall-preview-content",
            Static,
        ).update(
            "Draft reset to the current live state.\n\n"
            "Press Preview to review the configuration."
        )

        self.query_one(
            "#firewall-apply",
            Button,
        ).disabled = True

        self._render_verification()

    def _set_pending_firewall_state(
        self,
        transaction_id: str | None,
        *,
        message: str | None = None,
    ) -> None:
        self._pending_firewall_confirmation_id = (
            transaction_id
        )

        pending = transaction_id is not None

        if pending:
            self._set_preview_expanded(
                False
            )

        self.query_one(
            "#firewall-preview",
            Button,
        ).disabled = pending

        self.query_one(
            "#firewall-apply",
            Button,
        ).disabled = True

        self.query_one(
            "#firewall-reset",
            Button,
        ).disabled = pending

        confirm = self.query_one(
            "#firewall-confirm-connectivity",
            Button,
        )

        rollback = self.query_one(
            "#firewall-rollback-now",
            Button,
        )

        confirm.disabled = not pending
        rollback.disabled = not pending

        note = self.query_one(
            "#firewall-safety-note",
            Static,
        )

        if pending:
            note.update(
                (
                    "[b yellow]ROLLBACK ARMED[/b yellow]\n\n"
                    "The new firewall rules are active.\n"
                    f"Automatic rollback is armed for "
                    f"{FIREWALL_ROLLBACK_TIMEOUT_SECONDS} "
                    "seconds from Apply.\n\n"
                    "Confirm connectivity only if this "
                    "session is still working normally, "
                    "or choose Rollback Now."
                )
            )

            confirm.focus()

        else:
            note.update(
                message
                or (
                    "Firewall Apply is high risk.\n\n"
                    "Every change arms an independent "
                    f"{FIREWALL_ROLLBACK_TIMEOUT_SECONDS}"
                    "-second rollback timer before the "
                    "active ruleset is changed.\n\n"
                    "Connectivity must be explicitly "
                    "confirmed to cancel rollback."
                )
            )

    def _request_firewall_apply(
        self,
    ) -> None:
        if (
            self._pending_firewall_confirmation_id
            is not None
        ):
            self.notify(
                (
                    "A firewall transaction is already "
                    "awaiting connectivity confirmation."
                ),
                severity="warning",
                timeout=5,
            )
            return

        if not self._render_preview():
            return

        try:
            settings = (
                self._build_settings_from_form()
            )

            transaction = (
                build_apply_transaction(
                    settings
                )
            )

        except (ValueError, TypeError) as exc:
            self.query_one(
                "#firewall-apply",
                Button,
            ).disabled = True

            self.notify(
                (
                    "Invalid firewall configuration: "
                    f"{exc}"
                ),
                severity="error",
                timeout=5,
            )
            return

        self._pending_firewall_apply = (
            transaction
        )

        self.app.push_screen(
            ConfirmDialog(
                title="Apply firewall configuration",
                message=(
                    "HomeLabCTL will:\n\n"
                    "1. Back up /etc/nftables.conf.\n"
                    "2. Arm an independent "
                    f"{FIREWALL_ROLLBACK_TIMEOUT_SECONDS}"
                    "-second rollback timer.\n"
                    "3. Write the desired ruleset.\n"
                    "4. Validate it with nft -c.\n"
                    "5. Activate it with nft -f.\n"
                    "6. Keep rollback armed until "
                    "connectivity is confirmed.\n\n"
                    "An incorrect management interface, "
                    "CIDR, or SSH port may interrupt this "
                    "connection."
                ),
            ),
            self._on_firewall_apply_confirmed,
        )

    def _on_firewall_apply_confirmed(
        self,
        confirmed: bool,
    ) -> None:
        if not confirmed:
            self._pending_firewall_apply = None
            return

        transaction = (
            self._pending_firewall_apply
        )

        self._pending_firewall_apply = None

        if transaction is None:
            return

        self.query_one(
            "#firewall-apply",
            Button,
        ).disabled = True

        try:
            with self.app.suspend():
                return_code = (
                    run_privileged_transaction(
                        transaction
                    )
                )

        except Exception as exc:
            self.notify(
                (
                    "Firewall Apply failed: "
                    f"{exc}"
                ),
                severity="error",
                timeout=7,
            )

            self._set_pending_firewall_state(
                None
            )

            return

        if return_code != 0:
            self.notify(
                (
                    "Firewall Apply failed. "
                    "The previous ruleset was restored "
                    "if necessary."
                ),
                severity="error",
                timeout=7,
            )

            self._set_pending_firewall_state(
                None
            )

            return

        try:
            save_managed_service_rules(
                tuple(
                    self._service_rules
                ),
                transaction_id=transaction.id,
            )
        except Exception as exc:
            self.notify(
                (
                    "Firewall applied, but HomeLabCTL "
                    "could not record firewall rule transaction: "
                    f"{exc}"
                ),
                severity="warning",
                timeout=7,
            )

        self._set_pending_firewall_state(
            transaction.id
        )

        self.app.push_screen(
            ConfirmDialog(
                title="Confirm firewall connectivity",
                message=(
                    "The new firewall rules are active.\n\n"
                    "If this terminal/session is still "
                    "working normally, confirm connectivity "
                    "to cancel the rollback timer.\n\n"
                    f"If confirmation is not received, "
                    "the previous firewall configuration "
                    "will be restored automatically."
                ),
            ),
            self._on_firewall_connectivity_prompt,
        )

    def _on_firewall_connectivity_prompt(
        self,
        confirmed: bool,
    ) -> None:
        if confirmed:
            self._confirm_pending_firewall()
            return

        if (
            self._pending_firewall_confirmation_id
            is not None
        ):
            self.notify(
                (
                    "Firewall connectivity was not "
                    "confirmed. Automatic rollback "
                    "remains armed."
                ),
                severity="warning",
                timeout=6,
            )

    def _request_firewall_confirmation(
        self,
    ) -> None:
        if (
            self._pending_firewall_confirmation_id
            is None
        ):
            return

        self.app.push_screen(
            ConfirmDialog(
                title="Confirm firewall connectivity",
                message=(
                    "Confirm only if network and SSH "
                    "connectivity are working normally.\n\n"
                    "Confirmation permanently cancels "
                    "the automatic rollback for this "
                    "transaction."
                ),
            ),
            self._on_firewall_connectivity_prompt,
        )

    def _confirm_pending_firewall(
        self,
    ) -> None:
        transaction_id = (
            self._pending_firewall_confirmation_id
        )

        if not transaction_id:
            return

        try:
            with self.app.suspend():
                return_code = (
                    confirm_firewall_transaction(
                        transaction_id
                    )
                )

        except Exception as exc:
            self.notify(
                (
                    "Firewall confirmation failed: "
                    f"{exc}. Automatic rollback may "
                    "still be armed."
                ),
                severity="error",
                timeout=7,
            )
            return

        if return_code != 0:
            self.notify(
                (
                    "Firewall confirmation was rejected "
                    "or the rollback already expired. "
                    "Check the current firewall state."
                ),
                severity="error",
                timeout=7,
            )
            return

        self._set_pending_firewall_state(
            None,
            message=(
                "[green]Connectivity confirmed.[/green]\n\n"
                "Automatic firewall rollback was cancelled.\n"
                "Press Preview before another Apply."
            ),
        )

        self.notify(
            (
                "Firewall connectivity confirmed. "
                "Automatic rollback cancelled."
            ),
            timeout=5,
        )

    def _request_firewall_rollback(
        self,
    ) -> None:
        if (
            self._pending_firewall_confirmation_id
            is None
        ):
            return

        self.app.push_screen(
            ConfirmDialog(
                title="Roll back firewall now",
                message=(
                    "Restore the firewall configuration "
                    "that existed before this Apply and "
                    "activate it immediately?"
                ),
            ),
            self._on_firewall_rollback_confirmed,
        )

    def _on_firewall_rollback_confirmed(
        self,
        confirmed: bool,
    ) -> None:
        if not confirmed:
            return

        transaction_id = (
            self._pending_firewall_confirmation_id
        )

        if not transaction_id:
            return

        try:
            with self.app.suspend():
                return_code = (
                    rollback_firewall_transaction(
                        transaction_id
                    )
                )

        except Exception as exc:
            self.notify(
                (
                    "Firewall rollback failed: "
                    f"{exc}"
                ),
                severity="error",
                timeout=7,
            )
            return

        if return_code != 0:
            self.notify(
                (
                    "Firewall rollback was rejected "
                    "or already expired. Check the "
                    "current firewall state."
                ),
                severity="error",
                timeout=7,
            )
            return

        self._set_pending_firewall_state(
            None,
            message=(
                "[green]Previous firewall restored.[/green]\n\n"
                "The managed configuration and active "
                "ruleset were rolled back."
            ),
        )

        self._reset_draft()

        self.notify(
            "Previous firewall configuration restored.",
            timeout=5,
        )

    def on_button_pressed(
        self,
        event: Button.Pressed,
    ) -> None:

        button_id = event.button.id

        if button_id == "firewall-rule-add":
            self._open_rule_editor(
                None
            )
            return

        if button_id == "firewall-rule-edit":
            rule = (
                self._selected_service_rule()
            )

            if rule is not None:
                self._open_rule_editor(
                    rule
                )

            return

        if button_id == "firewall-rule-remove":
            self._request_remove_service_rule()
            return

        if button_id == "firewall-rule-toggle":
            self._toggle_selected_service_rule()
            return

        if button_id == "firewall-rule-save":
            self._save_rule_editor()
            return

        if button_id == "firewall-rule-cancel":
            self._close_rule_editor()
            return
        button_id = (
            event.button.id
            or ""
        )

        if button_id.startswith(
            "firewall-nav-"
        ):
            self._show_page(
                button_id.removeprefix(
                    "firewall-nav-"
                )
            )
            return

        button_id = (
            event.button.id
        )

        if (
            button_id
            == "firewall-tab-configure"
        ):
            self._show_page(
                "configure"
            )
            return

        if (
            button_id
            == "firewall-tab-inspect"
        ):
            self._show_page(
                "inspect"
            )
            return

        if (
            button_id
            == "firewall-preview"
        ):
            self._render_preview()
            return

        if (
            button_id
            == "firewall-apply"
        ):
            self._request_firewall_apply()
            return

        if (
            button_id
            == "firewall-reset"
        ):
            self._reset_draft()
            return

        if (
            button_id
            == "firewall-confirm-connectivity"
        ):
            self._request_firewall_confirmation()
            return

        if (
            button_id
            == "firewall-rollback-now"
        ):
            self._request_firewall_rollback()
            return


# Legacy standalone screen kept for import compatibility.
class FirewallScreen(ModuleScreen):
    MODULE = "firewall"
    SCREEN_TITLE = "Firewall"
