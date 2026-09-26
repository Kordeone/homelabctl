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

    ENTRY_ID = "firewall-tab-configure"

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
        "firewall-tab-configure": {
            "left": SIDEBAR_TARGET,
            "right": "firewall-tab-inspect",
            "down": "firewall-management-interface",
        },
        "firewall-tab-inspect": {
            "left": "firewall-tab-configure",
            "down": "firewall-preview",
        },
        "firewall-management-interface": {
            "left": SIDEBAR_TARGET,
            "down": "firewall-management-cidr",
            "up": "firewall-tab-configure",
        },
        "firewall-management-cidr": {
            "left": SIDEBAR_TARGET,
            "down": "firewall-ssh-port",
            "up": "firewall-management-interface",
        },
        "firewall-ssh-port": {
            "left": SIDEBAR_TARGET,
            "down": "firewall-dhcp",
            "up": "firewall-management-cidr",
        },
        "firewall-dhcp": {
            "left": SIDEBAR_TARGET,
            "down": "firewall-ipv4-icmp",
            "up": "firewall-ssh-port",
        },
        "firewall-ipv4-icmp": {
            "left": SIDEBAR_TARGET,
            "down": "firewall-ipv6-icmp",
            "up": "firewall-dhcp",
        },
        "firewall-ipv6-icmp": {
            "left": SIDEBAR_TARGET,
            "right": "firewall-preview",
            "up": "firewall-ipv4-icmp",
        },
        "firewall-preview": {
            "left": "firewall-ipv6-icmp",
            "down": "firewall-apply",
            "up": "firewall-tab-inspect",
        },
        "firewall-apply": {
            "left": "firewall-ipv6-icmp",
            "up": "firewall-preview",
            "down": "firewall-reset",
        },
        "firewall-reset": {
            "left": "firewall-ipv6-icmp",
            "up": "firewall-apply",
            "down": "firewall-confirm-connectivity",
        },
        "firewall-confirm-connectivity": {
            "left": "firewall-ipv6-icmp",
            "up": "firewall-reset",
            "down": "firewall-rollback-now",
        },
        "firewall-rollback-now": {
            "left": "firewall-ipv6-icmp",
            "up": "firewall-confirm-connectivity",
        },
    }

    def __init__(self) -> None:
        super().__init__(
            id="firewall-view"
        )

        self._page = "configure"
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
                    "WAIT",
                    id="firewall-status",
                )

            with Horizontal(
                id="firewall-page-selector"
            ):
                yield Button(
                    "Configure",
                    id="firewall-tab-configure",
                    classes="firewall-page-tab",
                )

                yield Button(
                    "Inspect",
                    id="firewall-tab-inspect",
                    classes="firewall-page-tab",
                )

            with ContentSwitcher(
                initial=(
                    "firewall-page-configure"
                ),
                id="firewall-pages",
            ):
                with VerticalScroll(
                    id="firewall-page-configure"
                ):
                    with Grid(
                        id="firewall-configure-grid"
                    ):
                        with Vertical(
                            id="firewall-current-panel",
                            classes="firewall-panel",
                        ):
                            yield Static(
                                "Current State",
                                classes=(
                                    "firewall-panel-title"
                                ),
                            )

                            yield Static(
                                "Waiting for backend...",
                                id=(
                                    "firewall-current-content"
                                ),
                            )

                        with VerticalScroll(
                            id="firewall-policy-panel",
                            classes="firewall-panel",
                        ):
                            yield Static(
                                "Desired Firewall Policy",
                                classes=(
                                    "firewall-panel-title"
                                ),
                            )

                            yield Static(
                                "Management interface",
                                classes=(
                                    "firewall-field-label"
                                ),
                            )

                            yield Input(
                                id=(
                                    "firewall-management-interface"
                                ),
                            )

                            yield Static(
                                "Management IPv4 CIDR",
                                classes=(
                                    "firewall-field-label"
                                ),
                            )

                            yield Input(
                                id=(
                                    "firewall-management-cidr"
                                ),
                            )

                            yield Static(
                                "SSH port",
                                classes=(
                                    "firewall-field-label"
                                ),
                            )

                            yield Input(
                                id="firewall-ssh-port",
                                type="integer",
                            )

                            yield Static(
                                "Allow DHCP client replies",
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

                            yield Static(
                                "Allow IPv4 ICMP",
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

                            yield Static(
                                "Allow IPv6 ICMP",
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

                        with Vertical(
                            id="firewall-actions-panel",
                            classes="firewall-panel",
                        ):
                            yield Static(
                                "Actions",
                                classes=(
                                    "firewall-panel-title"
                                ),
                            )

                            yield Button(
                                "Preview",
                                id="firewall-preview",
                                variant="primary",
                            )

                            yield Button(
                                "Apply",
                                id="firewall-apply",
                                disabled=True,
                            )

                            yield Button(
                                "Reset to Live",
                                id="firewall-reset",
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

                            yield Static(
                                (
                                    "Firewall Apply is high risk.\n\n"
                                    "Every change arms an independent "
                                    f"{FIREWALL_ROLLBACK_TIMEOUT_SECONDS}"
                                    "-second rollback timer before the "
                                    "active ruleset is changed.\n\n"
                                    "Connectivity must be explicitly "
                                    "confirmed to cancel rollback."
                                ),
                                id="firewall-safety-note",
                            )

                            with VerticalScroll(
                                id=(
                                    "firewall-preview-scroll"
                                )
                            ):
                                yield Static(
                                    (
                                        "Press Preview to render "
                                        "the desired nftables "
                                        "configuration."
                                    ),
                                    id=(
                                        "firewall-preview-content"
                                    ),
                                    markup=False,
                                )

                with VerticalScroll(
                    id="firewall-page-inspect"
                ):
                    with Grid(
                        id="firewall-inspect-grid"
                    ):
                        with Vertical(
                            id=(
                                "firewall-verification-panel"
                            ),
                            classes="firewall-panel",
                        ):
                            yield Static(
                                "Verification",
                                classes=(
                                    "firewall-panel-title"
                                ),
                            )

                            yield Static(
                                "Waiting for backend...",
                                id=(
                                    "firewall-verification-content"
                                ),
                            )

                        with Vertical(
                            id=(
                                "firewall-runtime-panel"
                            ),
                            classes="firewall-panel",
                        ):
                            yield Static(
                                "Runtime / Safety",
                                classes=(
                                    "firewall-panel-title"
                                ),
                            )

                            yield Static(
                                "Waiting for backend...",
                                id=(
                                    "firewall-runtime-content"
                                ),
                            )

    def action_show_configure(
        self,
    ) -> None:
        self._show_page(
            "configure"
        )

    def action_show_inspect(
        self,
    ) -> None:
        self._show_page(
            "inspect"
        )

    def _show_page(
        self,
        page: str,
    ) -> None:
        self._page = page

        switcher = self.query_one(
            "#firewall-pages",
            ContentSwitcher,
        )

        switcher.current = (
            f"firewall-page-{page}"
        )

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
        target = self.query_one(
            "#firewall-current-content",
            Static,
        )

        status_target = self.query_one(
            "#firewall-status",
            Static,
        )

        if not self._backend_online:
            status_target.update(
                "[red]OFFLINE[/red]"
            )

            target.update(
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

        lines = [
            (
                "nftables binary: "
                f"{self._yes_no(values.get('nft_available'))}"
            ),
            (
                "service: "
                f"{values.get('service_active', '--')}"
                " / "
                f"{values.get('service_enabled', '--')}"
            ),
            "",
            "Management access",
            "-----------------",
            (
                "Interface: "
                f"{values.get('management_interface', '--')}"
            ),
            (
                "IPv4 CIDR: "
                f"{values.get('management_ipv4_cidr', '--')}"
            ),
            (
                "SSH port: "
                f"{values.get('ssh_port', '--')}"
            ),
            "",
            "Allowed traffic",
            "---------------",
            (
                "DHCP client: "
                f"{self._yes_no(values.get('allow_dhcp_client'))}"
            ),
            (
                "IPv4 ICMP: "
                f"{self._yes_no(values.get('allow_ipv4_icmp'))}"
            ),
            (
                "IPv6 ICMP: "
                f"{self._yes_no(values.get('allow_ipv6_icmp'))}"
            ),
            "",
            "Base policy",
            "-----------",
            (
                "Input DROP: "
                f"{self._yes_no(values.get('input_policy_drop'))}"
            ),
            (
                "Forward DROP: "
                f"{self._yes_no(values.get('forward_policy_drop'))}"
            ),
        ]

        target.update(
            "\n".join(
                lines
            )
        )

    def _render_preview(
        self,
    ) -> bool:
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
        self._load_live_state_into_form()

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
