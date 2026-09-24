"""SSH feature content.

Stage 1B:
- Two internal pages
- Configure page
- Inspect page
- Local desired-config preview
- No system mutation yet
"""

from __future__ import annotations

import subprocess

from homelabctl.apply.sudo import (
    confirm_ssh_transaction,
    run_privileged_transaction,
)

from homelabctl.features.ssh.apply import build_apply_transaction
from homelabctl.features.ssh.session_actions import (
    build_disconnect_session_transaction,
)

from typing import Any

from rich.text import Text

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import (
    Container,
    Grid,
    Horizontal,
    Vertical,
    VerticalScroll,
)
from textual.widget import Widget
from textual.widgets import (
    Button,
    ContentSwitcher,
    DataTable,
    Input,
    Select,
    Static,
)

from homelabctl.features.ssh.constants import (
    MANAGED_SSH_FILENAME,
)
from homelabctl.features.ssh.plan import (
    render_config,
)
from homelabctl.system.runtime_defaults import current_user
from homelabctl.features.ssh.schema import (
    SSHSettings,
)

from homelabctl.tui.dialogs import ConfirmDialog

from homelabctl.tui.navigation import (
    NavigableView,
    SIDEBAR_TARGET,
    SpaceSelect,
)


YES_NO = (
    ("Yes", "yes"),
    ("No", "no"),
)

ROOT_LOGIN_OPTIONS = (
    ("No", "no"),
    (
        "Keys only",
        "prohibit-password",
    ),
    ("Yes", "yes"),
)

TCP_FORWARD_OPTIONS = (
    ("No", "no"),
    ("Yes", "yes"),
    ("Local only", "local"),
    ("Remote only", "remote"),
)




class SSHView(NavigableView):
    """SSH content inside the shared application shell."""

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

    def __init__(self) -> None:
        super().__init__(
            id="ssh-view"
        )

        self._page = "configure"

        self._active_sessions: list[dict[str, Any]] = []
        self._selected_session_id: str | None = None
        self._pending_disconnect_session: dict[str, Any] | None = None
        self._pending_ssh_apply: Any | None = None
        self._pending_ssh_confirmation_id: str | None = None
        self._current_session_id = (
            self._detect_current_session_id()
        )

    @staticmethod
    def _detect_current_session_id(
    ) -> str | None:
        result = subprocess.run(
            [
                "/usr/bin/loginctl",
                "show-session",
                "self",
                "-p",
                "Id",
                "--value",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return None

        value = result.stdout.strip()

        return value or None

    # ========================================================
    # GLOBAL NAVIGATION GRAPH
    # ========================================================

    ENTRY_ID = "ssh-tab-configure"

    NAVIGATION = {
        # ----------------------------------------------------
        # PAGE SELECTOR
        # ----------------------------------------------------

        "ssh-tab-configure": {
            "left": SIDEBAR_TARGET,
            "right": "ssh-tab-inspect",
        },

        "ssh-tab-inspect": {
            "left": "ssh-tab-configure",
        },

        # ----------------------------------------------------
        # CONFIG FORM
        # ----------------------------------------------------

        "ssh-port": {
            "up": "ssh-tab-configure",
            "down": "ssh-root-login",
        },

        "ssh-root-login": {
            "up": "ssh-port",
            "down": "ssh-password-auth",
            "right": "ssh-action-preview",
            "left": SIDEBAR_TARGET,
        },

        "ssh-password-auth": {
            "up": "ssh-root-login",
            "down": "ssh-pubkey-auth",
            "right": "ssh-action-preview",
            "left": SIDEBAR_TARGET,
        },

        "ssh-pubkey-auth": {
            "up": "ssh-password-auth",
            "down": "ssh-allow-users",
            "right": "ssh-action-preview",
            "left": SIDEBAR_TARGET,
        },

        "ssh-allow-users": {
            "up": "ssh-pubkey-auth",
            "down": "ssh-allow-groups",
        },

        "ssh-allow-groups": {
            "up": "ssh-allow-users",
            "down": "ssh-max-auth-tries",
        },

        "ssh-max-auth-tries": {
            "up": "ssh-allow-groups",
            "down": "ssh-client-alive-interval",
        },

        "ssh-client-alive-interval": {
            "up": "ssh-max-auth-tries",
            "down": "ssh-client-alive-count-max",
        },

        "ssh-client-alive-count-max": {
            "up": "ssh-client-alive-interval",
            "down": "ssh-x11-forwarding",
        },

        "ssh-x11-forwarding": {
            "up": "ssh-client-alive-count-max",
            "down": "ssh-tcp-forwarding",
            "right": "ssh-reset",
            "left": SIDEBAR_TARGET,
        },

        "ssh-tcp-forwarding": {
            "up": "ssh-x11-forwarding",
            "right": "ssh-reset",
            "left": SIDEBAR_TARGET,
        },

        # ----------------------------------------------------
        # ACTIONS
        #
        # Apply / Verify are intentionally disabled in the
        # current development stage, so navigation skips them.
        # ----------------------------------------------------

        "ssh-action-preview": {
            "left": "ssh-root-login",
            "right": "ssh-apply",
            "down": "ssh-verify",
            "up": "ssh-tab-configure",
        },

        "ssh-apply": {
            "left": "ssh-action-preview",
            "down": "ssh-reset",
            "up": "ssh-tab-configure",
        },

        "ssh-verify": {
            "up": "ssh-action-preview",
            "right": "ssh-reset",
            "left": "ssh-x11-forwarding",
        },

        "ssh-reset": {
            "up": "ssh-apply",
            "left": "ssh-verify",
        },

        # ----------------------------------------------------
        # PAGE 2 TABLES
        # ----------------------------------------------------

        "ssh-sessions-table": {
            "up": "ssh-tab-inspect",
            "down": "ssh-disconnect-session",
            "right": "ssh-keys-table",
        },

        "ssh-disconnect-session": {
            "up": "ssh-sessions-table",
            "right": "ssh-keys-table",
        },

        "ssh-keys-table": {
            "up": "ssh-tab-inspect",
            "left": "ssh-sessions-table",
        },
    }

    def navigation_target(
        self,
        focused,
        direction: str,
    ) -> str | None:
        """Resolve SSH navigation including active internal page."""

        focused_id = getattr(
            focused,
            "id",
            None,
        )

        # Down from the active page tab enters that page.
        if (
            focused_id
            == "ssh-tab-configure"
            and direction
            == "down"
        ):
            if self._page == "configure":
                return "ssh-port"

            return "ssh-sessions-table"

        if (
            focused_id
            == "ssh-tab-inspect"
            and direction
            == "down"
        ):
            if self._page == "inspect":
                return "ssh-sessions-table"

            return "ssh-port"

        return super().navigation_target(
            focused,
            direction,
        )

    # ========================================================
    # COMPOSE
    # ========================================================

    def compose(self) -> ComposeResult:
        with Vertical(
            id="ssh-content"
        ):

            # --------------------------------------------------
            # FEATURE HEADER
            # --------------------------------------------------

            with Horizontal(
                id="ssh-feature-header"
            ):
                with Vertical(
                    id="ssh-feature-heading"
                ):
                    yield Static(
                        (
                            "SSH — Secure Shell "
                            "Configuration"
                        ),
                        id="ssh-title",
                    )

                    yield Static(
                        (
                            "Inspect the effective SSH state, "
                            "prepare the HomelabCTL-managed "
                            "configuration, then apply and verify it."
                        ),
                        id="ssh-description",
                    )

                yield Static(
                    (
                        "Status: "
                        "[yellow]DETECTED[/yellow]"
                    ),
                    id="ssh-status",
                    markup=True,
                )

            # --------------------------------------------------
            # INTERNAL PAGE SELECTOR
            # --------------------------------------------------

            with Horizontal(
                id="ssh-page-selector"
            ):
                yield Button(
                    "1  Configure",
                    id="ssh-tab-configure",
                    classes=(
                        "ssh-page-tab "
                        "active-page-tab"
                    ),
                )

                yield Button(
                    "2  Inspect",
                    id="ssh-tab-inspect",
                    classes="ssh-page-tab",
                )

                yield Static(
                    (
                        f"Managed file: "
                        f"{MANAGED_SSH_FILENAME}"
                    ),
                    id="ssh-managed-file-label",
                )

            # --------------------------------------------------
            # TWO PAGE CONTENT
            # --------------------------------------------------

            with ContentSwitcher(
                initial="ssh-page-configure",
                id="ssh-page-switcher",
            ):

                # ==============================================
                # PAGE 1 — CONFIGURE
                # ==============================================

                with VerticalScroll(
                    id="ssh-page-configure"
                ):
                    with Grid(
                        id="ssh-page-one-grid"
                    ):

                        # --------------------------------------
                        # CURRENT STATE
                        # --------------------------------------

                        with Container(
                            id="ssh-current-panel",
                            classes=(
                                "ssh-box "
                                "ssh-page-panel"
                            ),
                        ):
                            yield Static(
                                "Current State (live)",
                                classes="ssh-box-title",
                            )

                            yield Static(
                                (
                                    "Waiting for SSH "
                                    "snapshot..."
                                ),
                                id="ssh-current-content",
                                classes="ssh-box-body",
                                markup=True,
                            )

                        # --------------------------------------
                        # DESIRED CONFIGURATION
                        # --------------------------------------

                        with Container(
                            id="ssh-config-panel",
                            classes=(
                                "ssh-box "
                                "ssh-page-panel"
                            ),
                        ):
                            yield Static(
                                "Desired Configuration",
                                classes="ssh-box-title",
                            )

                            with VerticalScroll(
                                id="ssh-config-scroll"
                            ):
                                with Grid(
                                    id="ssh-config-grid"
                                ):
                                    yield Static(
                                        "SSH Port",
                                        classes="ssh-field-label",
                                    )

                                    yield Input(
                                        value="22",
                                        type="integer",
                                        max_length=5,
                                        id="ssh-port",
                                        classes="ssh-field-control",
                                    )

                                    yield Static(
                                        "Permit Root Login",
                                        classes="ssh-field-label",
                                    )

                                    yield SpaceSelect(
                                        ROOT_LOGIN_OPTIONS,
                                        value="no",
                                        allow_blank=False,
                                        id="ssh-root-login",
                                        classes="ssh-field-control",
                                    )

                                    yield Static(
                                        "Password Authentication",
                                        classes="ssh-field-label",
                                    )

                                    yield SpaceSelect(
                                        YES_NO,
                                        value="no",
                                        allow_blank=False,
                                        id="ssh-password-auth",
                                        classes="ssh-field-control",
                                    )

                                    yield Static(
                                        "Public Key Authentication",
                                        classes="ssh-field-label",
                                    )

                                    yield SpaceSelect(
                                        YES_NO,
                                        value="yes",
                                        allow_blank=False,
                                        id="ssh-pubkey-auth",
                                        classes="ssh-field-control",
                                    )

                                    yield Static(
                                        "Allow Users",
                                        classes="ssh-field-label",
                                    )

                                    yield Input(
                                        value=current_user(),
                                        placeholder=(
                                            "e.g. server-user"
                                        ),
                                        id="ssh-allow-users",
                                        classes="ssh-field-control",
                                    )

                                    yield Static(
                                        "Allow Groups",
                                        classes="ssh-field-label",
                                    )

                                    yield Input(
                                        value="",
                                        placeholder="optional",
                                        id="ssh-allow-groups",
                                        classes="ssh-field-control",
                                    )

                                    yield Static(
                                        "Max Auth Tries",
                                        classes="ssh-field-label",
                                    )

                                    yield Input(
                                        value="3",
                                        type="integer",
                                        max_length=2,
                                        id="ssh-max-auth-tries",
                                        classes="ssh-field-control",
                                    )

                                    yield Static(
                                        "Client Alive Interval",
                                        classes="ssh-field-label",
                                    )

                                    yield Input(
                                        value="300",
                                        type="integer",
                                        max_length=6,
                                        id=(
                                            "ssh-client-"
                                            "alive-interval"
                                        ),
                                        classes="ssh-field-control",
                                    )

                                    yield Static(
                                        "Client Alive Count Max",
                                        classes="ssh-field-label",
                                    )

                                    yield Input(
                                        value="2",
                                        type="integer",
                                        max_length=3,
                                        id=(
                                            "ssh-client-"
                                            "alive-count-max"
                                        ),
                                        classes="ssh-field-control",
                                    )

                                    yield Static(
                                        "X11 Forwarding",
                                        classes="ssh-field-label",
                                    )

                                    yield SpaceSelect(
                                        YES_NO,
                                        value="no",
                                        allow_blank=False,
                                        id="ssh-x11-forwarding",
                                        classes="ssh-field-control",
                                    )

                                    yield Static(
                                        "Allow TCP Forwarding",
                                        classes="ssh-field-label",
                                    )

                                    yield SpaceSelect(
                                        TCP_FORWARD_OPTIONS,
                                        value="no",
                                        allow_blank=False,
                                        id="ssh-tcp-forwarding",
                                        classes="ssh-field-control",
                                    )

                        # --------------------------------------
                        # ACTIONS + FILE PREVIEW
                        # --------------------------------------

                        with Container(
                            id="ssh-actions-preview-panel",
                            classes=(
                                "ssh-box "
                                "ssh-page-panel"
                            ),
                        ):
                            yield Static(
                                "Actions",
                                classes="ssh-box-title",
                            )

                            with Grid(
                                id="ssh-actions-grid"
                            ):
                                yield Button(
                                    "Preview",
                                    id="ssh-action-preview",
                                    classes="ssh-small-action",
                                )

                                yield Button(
                                    "Apply",
                                    id="ssh-apply",
                                    classes="ssh-small-action",
                                    disabled=True,
                                )

                                yield Button(
                                    "Verify",
                                    id="ssh-verify",
                                    classes="ssh-small-action",
                                    disabled=True,
                                )

                                yield Button(
                                    "Reset",
                                    id="ssh-reset",
                                    variant="warning",
                                    classes="ssh-small-action",
                                )

                            yield Static(
                                "Configuration to Apply",
                                id="ssh-preview-title",
                            )

                            yield Static(
                                (
                                    "[dim]"
                                    "Press Preview to render "
                                    "the managed SSH file.\n\n"
                                    "Nothing is written to "
                                    "the system yet."
                                    "[/dim]"
                                ),
                                id="ssh-diff-content",
                                classes="ssh-preview-body",
                                markup=True,
                            )

                # ==============================================
                # PAGE 2 — INSPECT
                # ==============================================

                with VerticalScroll(
                    id="ssh-page-inspect"
                ):
                    with Grid(
                        id="ssh-page-two-grid"
                    ):

                        with Container(
                            id="ssh-verification-panel",
                            classes="ssh-box",
                        ):
                            yield Static(
                                "Verification Results",
                                classes="ssh-box-title",
                            )

                            yield Static(
                                (
                                    "[yellow]"
                                    "Not verified yet."
                                    "[/yellow]\n\n"
                                    "After Apply this section "
                                    "will check syntax, effective "
                                    "sshd settings, service state "
                                    "and managed-file consistency."
                                ),
                                id="ssh-verification-content",
                                classes="ssh-box-body",
                                markup=True,
                            )

                        with Container(
                            id="ssh-sessions-panel",
                            classes="ssh-box",
                        ):
                            yield Static(
                                "Active Sessions",
                                classes="ssh-box-title",
                            )

                            yield DataTable(
                                id="ssh-sessions-table",
                                cursor_type="row",
                                zebra_stripes=True,
                            )

                            yield Button(
                                "Disconnect Selected",
                                id="ssh-disconnect-session",
                                variant="error",
                                disabled=True,
                            )

                        with Container(
                            id="ssh-keys-panel",
                            classes="ssh-box",
                        ):
                            yield Static(
                                "Authorized Keys",
                                classes="ssh-box-title",
                            )

                            yield DataTable(
                                id="ssh-keys-table",
                                cursor_type="row",
                                zebra_stripes=True,
                            )

    # ========================================================
    # MOUNT
    # ========================================================

    def on_mount(self) -> None:
        sessions = self.query_one(
            "#ssh-sessions-table",
            DataTable,
        )

        sessions.add_columns(
            "ID",
            "USER",
            "FROM",
            "LOGIN",
            "IDLE",
            "STATUS",
        )

        keys = self.query_one(
            "#ssh-keys-table",
            DataTable,
        )

        keys.add_columns(
            "USER",
            "TYPE",
            "FINGERPRINT",
            "COMMENT",
        )

    # ========================================================
    # SHELL API
    # ========================================================

    def focus_entry(self) -> bool:
        # Entering SSH always starts at page selection.
        return self.focus_target(
            "ssh-tab-configure"
        )

    def update_snapshot(
        self,
        ping: dict[str, Any],
        snapshot: dict[str, Any],
        online: bool,
    ) -> None:
        if not online:
            self.query_one(
                "#ssh-current-content",
                Static,
            ).update(
                (
                    "[red]"
                    "Backend unavailable."
                    "[/red]"
                )
            )

            self.query_one(
                "#ssh-verify",
                Button,
            ).disabled = True

            self._render_verification({})
            self._render_sessions({})
            self._render_authorized_keys({})

            return

        modules = snapshot.get(
            "modules",
            {},
        )

        if not isinstance(
            modules,
            dict,
        ):
            modules = {}

        ssh = modules.get(
            "ssh",
            {},
        )

        if not isinstance(
            ssh,
            dict,
        ):
            ssh = {}

        values = ssh.get(
            "values",
            {},
        )

        if not isinstance(
            values,
            dict,
        ):
            values = {}

        verify_ready = (
            bool(
                self._value(
                    values,
                    "managed_file_present",
                    False,
                )
            )
            and bool(
                self._value(
                    values,
                    "effective_config_available",
                    False,
                )
            )
            and self._value(
                values,
                "service_active",
                "unknown",
            ) == "active"
        )

        self.query_one(
            "#ssh-verify",
            Button,
        ).disabled = not verify_ready

        self._render_current_state(
            values
        )

        self._render_verification(
            values
        )

        self._render_sessions(
            values
        )

        self._render_authorized_keys(
            values
        )

    # ========================================================
    # INSPECT DATA
    # ========================================================

    def _render_verification(
        self,
        values: dict[str, Any],
    ) -> None:
        target = self.query_one(
            "#ssh-verification-content",
            Static,
        )

        if not values:
            target.update(
                (
                    "[red]"
                    "Backend unavailable."
                    "[/red]"
                )
            )

            return

        service = self._value(
            values,
            "service",
            "ssh.service",
        )

        service_exists = bool(
            self._value(
                values,
                "service_exists",
                False,
            )
        )

        service_active = self._value(
            values,
            "service_active",
            "unknown",
        )

        effective_available = bool(
            self._value(
                values,
                "effective_config_available",
                False,
            )
        )

        effective_error = self._value(
            values,
            "effective_config_error",
            None,
        )

        main_config = self._value(
            values,
            "main_config",
            "/etc/ssh/sshd_config",
        )

        main_present = bool(
            self._value(
                values,
                "main_config_present",
                False,
            )
        )

        main_error = self._value(
            values,
            "main_config_error",
            None,
        )

        managed_file = self._value(
            values,
            "managed_file",
            (
                "/etc/ssh/sshd_config.d/"
                "00-homelabctl.conf"
            ),
        )

        managed_present = bool(
            self._value(
                values,
                "managed_file_present",
                False,
            )
        )

        legacy_files = self._value(
            values,
            "legacy_managed_files",
            [],
        )

        key_scan_complete = bool(
            self._value(
                values,
                "authorized_keys_scan_complete",
                False,
            )
        )

        key_errors = self._value(
            values,
            "authorized_keys_errors",
            [],
        )

        lines: list[str] = []

        if (
            service_exists
            and str(service_active).lower() == "active"
        ):
            lines.append(
                (
                    "[green]PASS[/green]  "
                    f"Service active: {service}"
                )
            )
        else:
            lines.append(
                (
                    "[red]FAIL[/red]  "
                    f"Service state: {service_active}"
                )
            )

        if effective_available:
            lines.append(
                (
                    "[green]PASS[/green]  "
                    "Effective OpenSSH configuration "
                    "is readable"
                )
            )
        else:
            detail = (
                str(effective_error)
                if effective_error
                else "unavailable"
            )

            lines.append(
                (
                    "[red]FAIL[/red]  "
                    "Effective configuration: "
                    f"{detail}"
                )
            )

        if main_present and not main_error:
            lines.append(
                (
                    "[green]PASS[/green]  "
                    f"Main config present: {main_config}"
                )
            )
        else:
            detail = (
                str(main_error)
                if main_error
                else "not present"
            )

            lines.append(
                (
                    "[red]FAIL[/red]  "
                    f"Main config: {detail}"
                )
            )

        if managed_present:
            lines.append(
                (
                    "[green]PASS[/green]  "
                    f"Managed file present: {managed_file}"
                )
            )
        else:
            lines.append(
                (
                    "[yellow]INFO[/yellow]  "
                    "HomeLabCTL managed file not "
                    f"installed yet: {managed_file}"
                )
            )

        if (
            isinstance(legacy_files, list)
            and legacy_files
        ):
            lines.append(
                (
                    "[yellow]WARN[/yellow]  "
                    "Legacy managed drop-in detected: "
                    + ", ".join(
                        str(item)
                        for item in legacy_files
                    )
                )
            )
        else:
            lines.append(
                (
                    "[green]PASS[/green]  "
                    "No legacy HomeLabCTL SSH "
                    "drop-ins detected"
                )
            )

        if key_scan_complete:
            lines.append(
                (
                    "[green]PASS[/green]  "
                    "Authorized-key scan complete"
                )
            )
        else:
            detail = "scan incomplete"

            if (
                isinstance(key_errors, list)
                and key_errors
            ):
                detail = str(
                    key_errors[0]
                )

            lines.append(
                (
                    "[yellow]WARN[/yellow]  "
                    "Authorized-key scan: "
                    f"{detail}"
                )
            )

        target.update(
            "\n".join(
                lines
            )
        )

    def _render_sessions(
        self,
        values: dict[str, Any],
    ) -> None:
        table = self.query_one(
            "#ssh-sessions-table",
            DataTable,
        )

        disconnect = self.query_one(
            "#ssh-disconnect-session",
            Button,
        )

        available = self._value(
            values,
            "sessions_available",
            False,
        )

        error = self._value(
            values,
            "sessions_error",
            None,
        )

        sessions = self._value(
            values,
            "sessions",
            [],
        )

        if not isinstance(
            sessions,
            list,
        ):
            sessions = []

        active_sessions = [
            item
            for item in sessions
            if (
                isinstance(item, dict)
                and item.get("state") == "active"
            )
        ]

        self._active_sessions = active_sessions

        active_ids = [
            str(
                item.get(
                    "session_id",
                    "",
                )
                or ""
            )
            for item in active_sessions
        ]

        selected_disappeared = (
            self._selected_session_id is not None
            and self._selected_session_id
            not in active_ids
        )

        if selected_disappeared:
            self._selected_session_id = None

        disconnect.disabled = (
            self._selected_session_id is None
            or self._selected_session_id
            == self._current_session_id
        )

        # Ordinary polling must not disturb interaction.
        # If the selected session actually disappeared,
        # allow one repaint so the stale row is removed.
        if (
            (
                table.has_focus
                or disconnect.has_focus
            )
            and not selected_disappeared
        ):
            return

        previous_cursor_id: str | None = None

        cursor_row = table.cursor_row

        if (
            0 <= cursor_row
            < len(active_sessions)
        ):
            previous_cursor_id = str(
                active_sessions[
                    cursor_row
                ].get(
                    "session_id",
                    "",
                )
                or ""
            )

        table.clear()

        if not available:
            self._selected_session_id = None
            disconnect.disabled = True

            message = (
                str(error)
                if error
                else "Session data unavailable"
            )

            table.add_row(
                "—",
                "—",
                "—",
                message,
                "—",
                "—",
            )

            return

        if not active_sessions:
            self._selected_session_id = None
            disconnect.disabled = True

            table.add_row(
                "—",
                "—",
                "—",
                "No active SSH sessions",
                "—",
                "—",
            )

            return

        for session in active_sessions:
            session_id = str(
                session.get(
                    "session_id",
                    "—",
                )
                or "—"
            )

            status = (
                "CURRENT"
                if (
                    session_id
                    == self._current_session_id
                )
                else ""
            )

            table.add_row(
                session_id,
                str(
                    session.get(
                        "user",
                        "—",
                    )
                    or "—"
                ),
                str(
                    session.get(
                        "from",
                        "—",
                    )
                    or "—"
                ),
                str(
                    session.get(
                        "login",
                        "—",
                    )
                    or "—"
                ),
                str(
                    session.get(
                        "idle",
                        "—",
                    )
                    or "—"
                ),
                status,
            )

        restore_id = (
            self._selected_session_id
            or previous_cursor_id
        )

        if restore_id in active_ids:
            table.move_cursor(
                row=active_ids.index(
                    restore_id
                ),
                animate=False,
                scroll=False,
            )

    def _render_authorized_keys(
        self,
        values: dict[str, Any],
    ) -> None:
        table = self.query_one(
            "#ssh-keys-table",
            DataTable,
        )

        table.clear()

        complete = self._value(
            values,
            "authorized_keys_scan_complete",
            False,
        )

        errors = self._value(
            values,
            "authorized_keys_errors",
            [],
        )

        keys = self._value(
            values,
            "authorized_keys",
            [],
        )

        if not complete:
            detail = "Authorized-key scan incomplete"

            if (
                isinstance(errors, list)
                and errors
            ):
                detail = str(
                    errors[0]
                )

            table.add_row(
                "—",
                "—",
                detail,
                "—",
            )

            return

        if not isinstance(
            keys,
            list,
        ):
            keys = []

        if not keys:
            table.add_row(
                "—",
                "—",
                "No authorized keys",
                "—",
            )

            return

        for item in keys:
            if not isinstance(
                item,
                dict,
            ):
                continue

            table.add_row(
                str(
                    item.get(
                        "user",
                        "—",
                    )
                    or "—"
                ),
                str(
                    item.get(
                        "type",
                        "—",
                    )
                    or "—"
                ),
                str(
                    item.get(
                        "fingerprint",
                        "—",
                    )
                    or "—"
                ),
                str(
                    item.get(
                        "comment",
                        "—",
                    )
                    or "—"
                ),
            )

    # ========================================================
    # PAGES
    # ========================================================

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
        switcher = self.query_one(
            "#ssh-page-switcher",
            ContentSwitcher,
        )

        configure = self.query_one(
            "#ssh-tab-configure",
            Button,
        )

        inspect = self.query_one(
            "#ssh-tab-inspect",
            Button,
        )

        if page == "inspect":
            switcher.current = (
                "ssh-page-inspect"
            )

            configure.remove_class(
                "active-page-tab"
            )

            inspect.add_class(
                "active-page-tab"
            )

            self._page = "inspect"

        else:
            switcher.current = (
                "ssh-page-configure"
            )

            inspect.remove_class(
                "active-page-tab"
            )

            configure.add_class(
                "active-page-tab"
            )

            self._page = "configure"

    # ========================================================
    # BUTTONS
    # ========================================================


    def on_button_pressed(
        self,
        event: Button.Pressed,
    ) -> None:
        button_id = (
            event.button.id
            or ""
        )

        if button_id == "ssh-tab-configure":
            self._show_page(
                "configure"
            )

            return

        if button_id == "ssh-tab-inspect":
            self._show_page(
                "inspect"
            )

            return

        if button_id == "ssh-action-preview":
            self._render_preview()

            try:
                self._build_settings_from_form()
            except (ValueError, TypeError):
                self.query_one(
                    "#ssh-apply",
                    Button,
                ).disabled = True
            else:
                self.query_one(
                    "#ssh-apply",
                    Button,
                ).disabled = False

            return

        if button_id == "ssh-apply":
            self._request_ssh_apply()
            return

        if button_id == "ssh-verify":
            self._show_page(
                "inspect"
            )

            self.notify(
                (
                    "Showing live SSH verification "
                    "from homelabd."
                ),
                timeout=3,
            )

            return

        if button_id == "ssh-disconnect-session":
            self._request_disconnect_session()
            return

        if button_id == "ssh-reset":
            self._reset_draft()

            self.query_one(
                "#ssh-apply",
                Button,
            ).disabled = True

            return

    def _request_ssh_apply(
        self,
    ) -> None:
        # Re-render immediately before confirmation so
        # the displayed config always matches the form.
        self._render_preview()

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
                "#ssh-apply",
                Button,
            ).disabled = True

            self.notify(
                f"Invalid SSH configuration: {exc}",
                severity="error",
                timeout=5,
            )

            return

        self._pending_ssh_apply = transaction

        self.app.push_screen(
            ConfirmDialog(
                title="Apply SSH configuration",
                message=(
                    "HomeLabCTL will:\n\n"
                    "1. Back up the managed SSH file.\n"
                    "2. Arm a 90-second automatic rollback.\n"
                    "3. Write the new configuration.\n"
                    "4. Validate it with sshd -t.\n"
                    "5. Reload OpenSSH.\n\n"
                    "If connectivity is not explicitly "
                    "confirmed, the previous configuration "
                    "will be restored automatically."
                ),
            ),
            self._on_ssh_apply_confirmed,
        )

    def _on_ssh_apply_confirmed(
        self,
        confirmed: bool,
    ) -> None:
        if not confirmed:
            self._pending_ssh_apply = None
            return

        transaction = self._pending_ssh_apply
        self._pending_ssh_apply = None

        if transaction is None:
            return

        # Do not permit another Apply while this one
        # is waiting for connectivity confirmation.
        self.query_one(
            "#ssh-apply",
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
                    "SSH Apply failed: "
                    f"{exc}"
                ),
                severity="error",
                timeout=6,
            )

            return

        if return_code != 0:
            self.notify(
                (
                    "SSH Apply failed. "
                    "The previous configuration "
                    "was restored if necessary."
                ),
                severity="error",
                timeout=6,
            )

            return

        self._pending_ssh_confirmation_id = (
            transaction.id
        )

        self.app.push_screen(
            ConfirmDialog(
                title="Confirm SSH connectivity",
                message=(
                    "The new SSH configuration is active.\n\n"
                    "If this session is working normally, "
                    "confirm connectivity now.\n\n"
                    "The automatic rollback remains armed "
                    "until confirmation and will restore "
                    "the previous configuration after "
                    "90 seconds if confirmation is not "
                    "received."
                ),
            ),
            self._on_ssh_connectivity_confirmed,
        )

    def _on_ssh_connectivity_confirmed(
        self,
        confirmed: bool,
    ) -> None:
        transaction_id = (
            self._pending_ssh_confirmation_id
        )

        self._pending_ssh_confirmation_id = None

        if not transaction_id:
            return

        if not confirmed:
            self.notify(
                (
                    "Connectivity was not confirmed. "
                    "Automatic SSH rollback remains armed."
                ),
                severity="warning",
                timeout=6,
            )

            return

        try:
            with self.app.suspend():
                return_code = (
                    confirm_ssh_transaction(
                        transaction_id
                    )
                )

        except Exception as exc:
            self.notify(
                (
                    "SSH confirmation failed: "
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
                    "SSH connectivity confirmation "
                    "was rejected or expired. "
                    "Check the current SSH state."
                ),
                severity="error",
                timeout=7,
            )

            return

        self.notify(
            (
                "SSH connectivity confirmed. "
                "Automatic rollback cancelled."
            ),
            timeout=5,
        )

    def on_data_table_row_selected(
        self,
        event: DataTable.RowSelected,
    ) -> None:
        if event.data_table.id != "ssh-sessions-table":
            return

        index = event.cursor_row

        if not (
            0 <= index < len(self._active_sessions)
        ):
            return

        session = self._active_sessions[index]

        session_id = str(
            session.get("session_id", "")
            or ""
        ).strip()

        if not session_id:
            return

        self._selected_session_id = session_id

        disconnect = self.query_one(
            "#ssh-disconnect-session",
            Button,
        )

        if (
            session_id
            == self._current_session_id
        ):
            disconnect.disabled = True

            self.notify(
                (
                    f"Session {session_id} is CURRENT. "
                    "Disconnect is blocked."
                ),
                severity="warning",
                timeout=2.5,
            )
            return

        disconnect.disabled = False

        self.notify(
            f"Selected SSH session {session_id}.",
            timeout=1.5,
        )

    def _request_disconnect_session(
        self,
    ) -> None:
        selected_id = self._selected_session_id

        if not selected_id:
            self.notify(
                "Select an active SSH session first.",
                severity="warning",
            )
            return

        if (
            selected_id
            == self._current_session_id
        ):
            self.notify(
                "Current SSH session cannot be disconnected.",
                severity="warning",
            )
            return

        session = next(
            (
                item
                for item in self._active_sessions
                if str(
                    item.get("session_id", "")
                    or ""
                ) == selected_id
            ),
            None,
        )

        if session is None:
            self._selected_session_id = None

            self.query_one(
                "#ssh-disconnect-session",
                Button,
            ).disabled = True

            self.notify(
                "That SSH session is no longer active.",
                severity="warning",
            )
            return

        session_id = str(
            session.get("session_id", "—")
        )
        user = str(
            session.get("user", "—")
        )
        remote = str(
            session.get("from", "—")
        )
        login = str(
            session.get("login", "—")
        )

        self._pending_disconnect_session = session

        self.app.push_screen(
            ConfirmDialog(
                title="Disconnect SSH session",
                message=(
                    f"Session: {session_id}\n"
                    f"User: {user}\n"
                    f"From: {remote}\n"
                    f"Login: {login}\n\n"
                    "This will terminate that SSH session."
                ),
            ),
            self._on_disconnect_confirmed,
        )

    def _on_disconnect_confirmed(
        self,
        confirmed: bool,
    ) -> None:
        if not confirmed:
            self._pending_disconnect_session = None
            return

        session = self._pending_disconnect_session
        self._pending_disconnect_session = None

        if not session:
            return

        session_id = str(
            session.get("session_id", "")
            or ""
        ).strip()

        if not session_id:
            self.notify(
                "SSH session ID is unavailable.",
                severity="error",
            )
            return

        # UI-side defense in depth.
        if (
            session_id
            == self._current_session_id
        ):
            self.notify(
                "Current SSH session cannot be disconnected.",
                severity="error",
            )
            return

        try:
            transaction = (
                build_disconnect_session_transaction(
                    session_id
                )
            )
        except ValueError as exc:
            self.notify(
                f"Invalid SSH session: {exc}",
                severity="error",
            )
            return

        try:
            # Restore the real terminal while sudo authenticates
            # and the root-owned helper runs.
            with self.app.suspend():
                return_code = (
                    run_privileged_transaction(
                        transaction
                    )
                )
        except Exception as exc:
            self.notify(
                (
                    "SSH disconnect failed: "
                    f"{exc}"
                ),
                severity="error",
                timeout=5,
            )
            return

        if return_code != 0:
            self.notify(
                (
                    f"Failed to disconnect SSH "
                    f"session {session_id}."
                ),
                severity="error",
                timeout=5,
            )
            return

        # Prevent a second activation while homelabd catches up.
        self.query_one(
            "#ssh-disconnect-session",
            Button,
        ).disabled = True

        self.notify(
            (
                f"SSH session {session_id} "
                "disconnected."
            ),
            timeout=4,
        )

    def _render_current_state(
        self,
        values: dict[str, Any],
    ) -> None:
        service = self._value(
            values,
            "service",
            "ssh.service",
        )

        exists = self._value(
            values,
            "service_exists",
            False,
        )

        active = self._value(
            values,
            "service_active",
            "unknown",
        )

        enabled = self._value(
            values,
            "service_enabled",
            "unknown",
        )

        port = self._value_any(
            values,
            (
                "port",
                "listen_port",
            ),
            "not reported",
        )

        root_login = self._value_any(
            values,
            (
                "permitrootlogin",
                "permit_root_login",
            ),
            "not reported",
        )

        password_auth = self._value_any(
            values,
            (
                "passwordauthentication",
                "password_authentication",
            ),
            "not reported",
        )

        pubkey_auth = self._value_any(
            values,
            (
                "pubkeyauthentication",
                "pubkey_authentication",
            ),
            "not reported",
        )

        allow_users = self._value_any(
            values,
            (
                "allowusers",
                "allow_users",
            ),
            "not reported",
        )

        allow_groups = self._value_any(
            values,
            (
                "allowgroups",
                "allow_groups",
            ),
            "not reported",
        )

        max_auth = self._value_any(
            values,
            (
                "maxauthtries",
                "max_auth_tries",
            ),
            "not reported",
        )

        alive_interval = self._value_any(
            values,
            (
                "clientaliveinterval",
                "client_alive_interval",
            ),
            "not reported",
        )

        alive_count = self._value_any(
            values,
            (
                "clientalivecountmax",
                "client_alive_count_max",
            ),
            "not reported",
        )

        x11 = self._value_any(
            values,
            (
                "x11forwarding",
                "x11_forwarding",
            ),
            "not reported",
        )

        tcp_forward = self._value_any(
            values,
            (
                "allowtcpforwarding",
                "allow_tcp_forwarding",
            ),
            "not reported",
        )

        allow_users_text = (
            self._format_access_list(
                allow_users
            )
        )

        allow_groups_text = (
            self._format_access_list(
                allow_groups
            )
        )

        active_ok = (
            str(active).lower()
            == "active"
        )

        active_color = (
            "green"
            if active_ok
            else "yellow"
        )

        lines = [
            (
                "● ssh service: "
                f"[{active_color}]"
                f"{active}"
                f"[/{active_color}]"
            ),
            "",
            f"Unit                    {service}",
            (
                "Installed               "
                f"{'yes' if exists else 'no'}"
            ),
            f"Enabled                 {enabled}",
            "",
            f"Port                    {port}",
            f"PermitRootLogin         {root_login}",
            (
                "PasswordAuthentication  "
                f"{password_auth}"
            ),
            (
                "PubkeyAuthentication    "
                f"{pubkey_auth}"
            ),
            (
                "AllowUsers              "
                f"{allow_users_text}"
            ),
            (
                "AllowGroups             "
                f"{allow_groups_text}"
            ),
            f"MaxAuthTries            {max_auth}",
            (
                "ClientAliveInterval     "
                f"{alive_interval}"
            ),
            (
                "ClientAliveCountMax     "
                f"{alive_count}"
            ),
            f"X11Forwarding           {x11}",
            (
                "AllowTcpForwarding      "
                f"{tcp_forward}"
            ),
            "",
            (
                "[dim]"
                "Values shown above are the live "
                "effective OpenSSH configuration."
                "[/dim]"
            ),
        ]

        self.query_one(
            "#ssh-current-content",
            Static,
        ).update(
            "\n".join(
                lines
            )
        )

    # ========================================================
    # LOCAL CONFIG PREVIEW
    # ========================================================

    def _render_preview(
        self,
    ) -> None:
        target = self.query_one(
            "#ssh-diff-content",
            Static,
        )

        try:
            settings = (
                self._build_settings_from_form()
            )

            rendered = render_config(
                settings
            )

        except ValueError as exc:
            message = Text()

            message.append(
                "Invalid configuration",
                style="bold red",
            )

            message.append(
                "\n\n"
            )

            message.append(
                str(exc)
            )

            target.update(
                message
            )

            return

        preview = Text()

        preview.append(
            MANAGED_SSH_FILENAME,
            style="bold cyan",
        )

        preview.append(
            "\n\n"
        )

        preview.append(
            rendered
        )

        target.update(
            preview
        )

    def _build_settings_from_form(
        self,
    ) -> SSHSettings:
        port = self._form_integer(
            "#ssh-port",
            "SSH Port",
        )

        max_auth_tries = self._form_integer(
            "#ssh-max-auth-tries",
            "Max Auth Tries",
        )

        client_alive_interval = (
            self._form_integer(
                "#ssh-client-alive-interval",
                "Client Alive Interval",
            )
        )

        client_alive_count_max = (
            self._form_integer(
                "#ssh-client-alive-count-max",
                "Client Alive Count Max",
            )
        )

        allow_users = self._form_patterns(
            "#ssh-allow-users"
        )

        allow_groups = self._form_patterns(
            "#ssh-allow-groups"
        )

        settings = SSHSettings(
            port=port,
            permit_root_login=str(
                self.query_one(
                    "#ssh-root-login",
                    SpaceSelect,
                ).value
            ),
            password_authentication=str(
                self.query_one(
                    "#ssh-password-auth",
                    SpaceSelect,
                ).value
            ),
            pubkey_authentication=str(
                self.query_one(
                    "#ssh-pubkey-auth",
                    SpaceSelect,
                ).value
            ),

            # This setting remains part of the fixed
            # hardening profile until it receives its
            # own Configure control.
            kbd_interactive_authentication="no",

            allow_users=allow_users,
            allow_groups=allow_groups,

            max_auth_tries=max_auth_tries,

            client_alive_interval=(
                client_alive_interval
            ),
            client_alive_count_max=(
                client_alive_count_max
            ),

            x11_forwarding=str(
                self.query_one(
                    "#ssh-x11-forwarding",
                    SpaceSelect,
                ).value
            ),
            allow_tcp_forwarding=str(
                self.query_one(
                    "#ssh-tcp-forwarding",
                    SpaceSelect,
                ).value
            ),
        )

        settings.validate()

        return settings

    def _form_integer(
        self,
        selector: str,
        label: str,
    ) -> int:
        raw = self.query_one(
            selector,
            Input,
        ).value.strip()

        if not raw:
            raise ValueError(
                f"{label} is required."
            )

        try:
            return int(raw)
        except ValueError as exc:
            raise ValueError(
                f"{label} must be an integer."
            ) from exc

    def _form_patterns(
        self,
        selector: str,
    ) -> tuple[str, ...]:
        raw = self.query_one(
            selector,
            Input,
        ).value.strip()

        if not raw:
            return ()

        return tuple(
            raw.split()
        )

    # ========================================================
    # RESET DRAFT
    # ========================================================

    def _reset_draft(
        self,
    ) -> None:
        self.query_one(
            "#ssh-port",
            Input,
        ).value = "22"

        self.query_one(
            "#ssh-root-login",
            Select,
        ).value = "no"

        self.query_one(
            "#ssh-password-auth",
            Select,
        ).value = "no"

        self.query_one(
            "#ssh-pubkey-auth",
            Select,
        ).value = "yes"

        self.query_one(
            "#ssh-allow-users",
            Input,
        ).value = current_user()

        self.query_one(
            "#ssh-allow-groups",
            Input,
        ).value = ""

        self.query_one(
            "#ssh-max-auth-tries",
            Input,
        ).value = "3"

        self.query_one(
            "#ssh-client-alive-interval",
            Input,
        ).value = "300"

        self.query_one(
            "#ssh-client-alive-count-max",
            Input,
        ).value = "2"

        self.query_one(
            "#ssh-x11-forwarding",
            Select,
        ).value = "no"

        self.query_one(
            "#ssh-tcp-forwarding",
            Select,
        ).value = "no"

        self.query_one(
            "#ssh-diff-content",
            Static,
        ).update(
            (
                "[dim]"
                "Draft reset.\n\n"
                "Press Preview to render "
                "the managed file."
                "[/dim]"
            )
        )

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _format_access_list(
        value: Any,
    ) -> str:
        if isinstance(
            value,
            (list, tuple),
        ):
            if not value:
                return "none configured"

            return ", ".join(
                str(item)
                for item in value
            )

        if value is None or value == "":
            return "none configured"

        return str(value)

    def _value(
        self,
        values: dict[str, Any],
        key: str,
        default: Any = None,
    ) -> Any:
        item = values.get(
            key
        )

        if isinstance(
            item,
            dict,
        ):
            return item.get(
                "value",
                default,
            )

        if item is None:
            return default

        return item

    def _value_any(
        self,
        values: dict[str, Any],
        keys: tuple[str, ...],
        default: Any = None,
    ) -> Any:
        for key in keys:
            if key in values:
                return self._value(
                    values,
                    key,
                    default,
                )

        return default
