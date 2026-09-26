"""Persistent HomeLabCTL application shell.

Owns:
- top service/status bar
- feature navigation sidebar
- backend connection/snapshot refresh
- switching between feature content views

Feature views do NOT recreate navigation chrome.
"""

from __future__ import annotations

from typing import Any

from textual import events, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import (
    Container,
    Horizontal,
    Vertical,
)
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Input,
    Select,
    Static,
    DataTable,
)

from homelabctl import __version__
from homelabctl.client import BackendClient
from homelabctl.core.errors import BackendError
from homelabctl.tui.dashboard import DashboardView
from homelabctl.tui.navigation import (
    NavigableView,
    SIDEBAR_TARGET,
)
from homelabctl.tui.screens.headless import HeadlessView
from homelabctl.tui.screens.firewall import FirewallView
from homelabctl.tui.screens.ssh import SSHView
from homelabctl.tui.widgets.feature_row import (
    FeatureRow,
)


FEATURES = (
    ("dashboard", "Dashboard"),
    ("ssh", "SSH"),
    ("headless", "Headless & Power"),
    ("firewall", "Firewall"),
    ("gateway", "Gateway / Wi-Fi"),
    ("storage", "Storage / NAS"),
    ("dev", "Docker / Git / Dev"),
    ("vpn", "VPN Gateway"),
    ("vpn_failover", "VPN Failover"),
    ("sandbox", "Agent Sandbox"),
    ("monitoring", "Monitoring / Backup"),
)

FEATURE_KEYS = tuple(
    key
    for key, _title in FEATURES
)

IMPLEMENTED_FEATURES = {
    "dashboard",
    "ssh",
    "headless",
    "firewall",
}


class ControlCenterScreen(Screen):
    """Persistent HomeLabCTL shell."""

    BINDINGS = [
        Binding(
            "r",
            "refresh",
            "Refresh",
        ),
        Binding(
            "escape",
            "focus_sidebar",
            "Sidebar",
        ),
        Binding(
            "ctrl+left",
            "focus_sidebar",
            "Sidebar",
            show=False,
        ),
        Binding(
            "d",
            "cycle_density",
            "Density",
        ),
        Binding(
            "q",
            "quit",
            "Quit",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()

        self.current_feature = "dashboard"

        self._ping: dict[str, Any] = {}
        self._snapshot: dict[str, Any] = {}

        self._backend_online = False

        # UI density:
        # auto -> normal / compact / tiny based on terminal cells.
        self._density_mode = "auto"
        self._effective_density = "normal"

    # ========================================================
    # COMPOSE
    # ========================================================

    def compose(self) -> ComposeResult:
        with Vertical(
            id="control-shell"
        ):

            # --------------------------------------------------
            # GLOBAL SERVICE STRIP
            # --------------------------------------------------

            with Horizontal(
                id="shell-service-strip"
            ):
                yield Static(
                    (
                        "[b cyan]HomeLab Control Center[/b cyan]"
                        "   │   "
                        "Backend [yellow]CHECKING[/yellow]"
                        "   │   "
                        "homelabd ?"
                        "   │   "
                        "protocol ?"
                        "   │   "
                        "read-only"
                        "   │   "
                        f"frontend {__version__}"
                    ),
                    id="shell-service-info",
                    markup=True,
                )

                yield Button(
                    "Refresh",
                    id="shell-refresh",
                    variant="primary",
                )

            # --------------------------------------------------
            # GLOBAL BODY
            # --------------------------------------------------

            with Horizontal(
                id="shell-body"
            ):

                # ==============================================
                # PERSISTENT FEATURE SIDEBAR
                # ==============================================

                with Vertical(
                    id="shell-sidebar"
                ):
                    yield Static(
                        "Features",
                        id="shell-sidebar-title",
                    )

                    for (
                        key,
                        title,
                    ) in FEATURES:
                        yield FeatureRow(
                            feature_key=key,
                            title=title,
                            status="--",
                            enabled=(
                                key
                                in IMPLEMENTED_FEATURES
                            ),
                            id=f"feature-{key}",
                        )

                # ==============================================
                # DYNAMIC CONTENT HOST
                # ==============================================

                yield Container(
                    id="feature-host"
                )

        yield Footer()

    # ========================================================
    # STARTUP
    # ========================================================

    def on_mount(self) -> None:
        self.call_after_refresh(
            self._mount_initial_view
        )

        self.set_interval(
            2.0,
            self.refresh_backend,
        )

        self._apply_density(
            self.size.width,
            self.size.height,
        )

        self.refresh_backend()

    def on_resize(
        self,
        event: events.Resize,
    ) -> None:
        self._apply_density(
            event.size.width,
            event.size.height,
        )

    def _apply_density(
        self,
        width: int,
        height: int,
    ) -> None:
        if self._density_mode == "auto":
            if (
                width < 112
                or height < 32
            ):
                density = "tiny"

            elif (
                width < 150
                or height < 40
            ):
                density = "compact"

            else:
                density = "normal"

        else:
            density = self._density_mode

        self._effective_density = density

        self.set_class(
            density == "compact",
            "compact-ui",
        )

        self.set_class(
            density == "tiny",
            "tiny-ui",
        )

    def action_cycle_density(
        self,
    ) -> None:
        modes = (
            "auto",
            "normal",
            "compact",
            "tiny",
        )

        index = modes.index(
            self._density_mode
        )

        self._density_mode = modes[
            (index + 1) % len(modes)
        ]

        self._apply_density(
            self.size.width,
            self.size.height,
        )

        self.notify(
            (
                "UI density: "
                f"{self._density_mode}"
                " → "
                f"{self._effective_density}"
            ),
            timeout=1.5,
        )

    def action_focus_sidebar(
        self,
    ) -> None:
        try:
            self.query_one(
                (
                    "#feature-"
                    f"{self.current_feature}"
                ),
                FeatureRow,
            ).focus()
        except Exception:
            self.query_one(
                "#feature-dashboard",
                FeatureRow,
            ).focus()

    async def _mount_initial_view(
        self,
    ) -> None:
        await self.show_feature(
            "dashboard"
        )

        self.query_one(
            "#feature-dashboard",
            FeatureRow,
        ).focus()

    # ========================================================
    # FEATURE SWITCHING
    # ========================================================

    async def show_feature(
        self,
        feature_key: str,
    ) -> None:
        if (
            feature_key
            not in IMPLEMENTED_FEATURES
        ):
            return

        host = self.query_one(
            "#feature-host",
            Container,
        )

        await host.remove_children()

        if feature_key == "dashboard":
            view = DashboardView()

        elif feature_key == "ssh":
            view = SSHView()

        elif feature_key == "headless":
            view = HeadlessView()

        elif feature_key == "firewall":
            view = FirewallView()

        else:
            return

        self.current_feature = (
            feature_key
        )

        await host.mount(
            view
        )

        self._update_sidebar_selection()

        self._deliver_snapshot_to_view()

    def _update_sidebar_selection(
        self,
    ) -> None:
        for (
            key,
            _title,
        ) in FEATURES:
            row = self.query_one(
                f"#feature-{key}",
                FeatureRow,
            )

            row.set_class(
                key
                == self.current_feature,
                "current-feature",
            )

    # ========================================================
    # FEATURE ROW ACTIVATION
    # ========================================================

    async def on_feature_row_activated(
        self,
        event: FeatureRow.Activated,
    ) -> None:
        if (
            event.feature_key
            not in IMPLEMENTED_FEATURES
        ):
            return

        await self.show_feature(
            event.feature_key
        )

        # Enter means "open this feature".
        # After the new view is mounted, move focus into it.
        self.call_after_refresh(
            self._focus_active_view
        )

    # ========================================================
    # ARROW NAVIGATION
    # ========================================================

    def on_key(
        self,
        event: events.Key,
    ) -> None:
        """Global directional navigation.

        Sidebar:
            Up / Down -> feature rows
            Right     -> enter current feature
            Enter     -> activate selected feature

        Feature content:
            Arrow keys follow that view's NAVIGATION map.

        Exceptions:
            - expanded Select owns its option-list navigation
            - DataTable owns arrow navigation internally
            - Input owns Left / Right cursor movement
              while Up / Down remain available globally
        """

        focused = self.app.focused

        if focused is None:
            return

        # --------------------------------------------------
        # SIDEBAR NAVIGATION
        # --------------------------------------------------

        if isinstance(
            focused,
            FeatureRow,
        ):
            try:
                index = FEATURE_KEYS.index(
                    focused.feature_key
                )

            except ValueError:
                return

            if event.key == "up":
                if index > 0:
                    self.query_one(
                        (
                            "#feature-"
                            f"{FEATURE_KEYS[index - 1]}"
                        ),
                        FeatureRow,
                    ).focus()

                event.stop()
                return

            if event.key == "down":
                if index < (
                    len(FEATURE_KEYS) - 1
                ):
                    self.query_one(
                        (
                            "#feature-"
                            f"{FEATURE_KEYS[index + 1]}"
                        ),
                        FeatureRow,
                    ).focus()

                event.stop()
                return

            if event.key == "right":
                # Only enter the feature that is actually
                # loaded in the content area.
                if (
                    focused.feature_key
                    == self.current_feature
                ):
                    self._focus_active_view()

                    event.stop()

                return

            return

        # --------------------------------------------------
        # ONLY ARROW KEYS ARE GLOBAL NAVIGATION
        # --------------------------------------------------

        if event.key not in {
            "up",
            "down",
            "left",
            "right",
        }:
            return

        # --------------------------------------------------
        # WIDGETS THAT OWN THEIR ARROWS
        # --------------------------------------------------

        # A table uses arrows for row/cell movement.
        if isinstance(
            focused,
            DataTable,
        ):
            return

        # Once a Select menu is open, its option list should
        # use normal arrows.
        if isinstance(
            focused,
            Select,
        ) and bool(
            getattr(
                focused,
                "expanded",
                False,
            )
        ):
            return

        # Input Left / Right remain cursor movement.
        #
        # Input doesn't bind Up / Down, so those bubble here
        # and become vertical component navigation.
        if (
            isinstance(
                focused,
                Input,
            )
            and event.key
            in {
                "left",
                "right",
            }
        ):
            return

        # --------------------------------------------------
        # ASK THE ACTIVE VIEW FOR THE DESTINATION
        # --------------------------------------------------

        host = self.query_one(
            "#feature-host",
            Container,
        )

        if not host.children:
            return

        view = host.children[0]

        if not isinstance(
            view,
            NavigableView,
        ):
            return

        target = view.navigation_target(
            focused,
            event.key,
        )

        if not target:
            return

        if target == SIDEBAR_TARGET:
            self.action_focus_sidebar()

            event.stop()
            return

        if view.focus_target(
            target
        ):
            event.stop()

    def _focus_active_view(
        self,
    ) -> None:
        host = self.query_one(
            "#feature-host",
            Container,
        )

        if not host.children:
            return

        view = host.children[0]

        focus_entry = getattr(
            view,
            "focus_entry",
            None,
        )

        if callable(
            focus_entry
        ):
            focus_entry()

    # ========================================================
    # GLOBAL ACTIONS
    # ========================================================

    def action_refresh(self) -> None:
        self.refresh_backend()

    def on_button_pressed(
        self,
        event: Button.Pressed,
    ) -> None:
        if (
            event.button.id
            == "shell-refresh"
        ):
            self.refresh_backend()

    # ========================================================
    # BACKEND
    # ========================================================

    @work(
        exclusive=True,
        group="shell-backend-refresh",
    )
    async def refresh_backend(
        self,
    ) -> None:
        client = BackendClient()

        try:
            ping = await client.ping()
            snapshot = (
                await client.snapshot()
            )

        except BackendError as exc:
            self._backend_online = False

            self._ping = {}
            self._snapshot = {}

            self._show_backend_offline(
                str(exc)
            )

            self._update_feature_states()

            self._deliver_snapshot_to_view()

            return

        self._backend_online = True

        self._ping = ping
        self._snapshot = snapshot

        self._show_backend_online()

        self._update_feature_states()

        self._deliver_snapshot_to_view()

    def _show_backend_online(
        self,
    ) -> None:
        self.query_one(
            "#shell-service-info",
            Static,
        ).update(
            (
                "[b cyan]HomeLab Control Center[/b cyan]"
                "   │   "
                "Backend [green]PASS[/green]"
                "   │   "
                "homelabd "
                f"{self._ping.get('backend_version', '?')}"
                "   │   "
                "protocol "
                f"{self._ping.get('protocol_version', '?')}"
                "   │   "
                f"{self._ping.get('mode', 'unknown')}"
                "   │   "
                f"frontend {__version__}"
            )
        )

    def _show_backend_offline(
        self,
        reason: str,
    ) -> None:
        self.query_one(
            "#shell-service-info",
            Static,
        ).update(
            (
                "[b cyan]HomeLab Control Center[/b cyan]"
                "   │   "
                "Backend [red]OFFLINE[/red]"
                "   │   "
                f"{reason}"
                "   │   "
                f"frontend {__version__}"
            )
        )

    # ========================================================
    # SIDEBAR FEATURE STATES
    # ========================================================

    def _update_feature_states(
        self,
    ) -> None:
        modules = self._snapshot.get(
            "modules",
            {},
        )

        if not isinstance(
            modules,
            dict,
        ):
            modules = {}

        # Dashboard
        self._set_feature(
            "dashboard",
            "Dashboard",
            (
                "READY"
                if self._backend_online
                else "OFF"
            ),
            enabled=True,
        )

        # SSH
        ssh = modules.get(
            "ssh"
        )

        ssh_detected = False

        if isinstance(
            ssh,
            dict,
        ):
            values = ssh.get(
                "values",
                {},
            )

            if isinstance(
                values,
                dict,
            ):
                service_exists = (
                    values.get(
                        "service_exists"
                    )
                )

                if isinstance(
                    service_exists,
                    dict,
                ):
                    ssh_detected = bool(
                        service_exists.get(
                            "value"
                        )
                    )

        self._set_feature(
            "ssh",
            "SSH",
            (
                "NEXT"
                if ssh_detected
                else "--"
            ),
            enabled=ssh_detected,
        )

        # Headless & Power
        headless = modules.get(
            "headless"
        )

        power = modules.get(
            "power"
        )

        headless_available = (
            isinstance(
                headless,
                dict,
            )
            and isinstance(
                power,
                dict,
            )
        )

        headless_status = "--"

        if headless_available:
            raw_status = str(
                headless.get(
                    "status",
                    "unknown",
                )
            ).upper()

            headless_status = (
                "PASS"
                if raw_status == "PASS"
                else raw_status
            )

        self._set_feature(
            "headless",
            "Headless & Power",
            headless_status,
            enabled=headless_available,
        )

        # Firewall
        firewall = modules.get(
            "firewall"
        )

        firewall_available = isinstance(
            firewall,
            dict,
        )

        firewall_status = "--"

        if firewall_available:
            raw_status = firewall.get(
                "status",
                "unknown",
            )

            firewall_status = str(
                raw_status
            ).upper()

        self._set_feature(
            "firewall",
            "Firewall",
            firewall_status,
            enabled=firewall_available,
        )

        # Detection-only features
        availability = {
            "gateway": self._wifi_detected(
                modules.get(
                    "network"
                )
            ),
            "storage": isinstance(
                modules.get(
                    "storage"
                ),
                dict,
            ),
        }

        titles = {
            "gateway": "Gateway / Wi-Fi",
            "storage": "Storage / NAS",
        }

        for key in (
            "gateway",
            "storage",
        ):
            self._set_feature(
                key,
                titles[key],
                (
                    "AVAIL"
                    if availability[key]
                    else "--"
                ),
                enabled=False,
            )

        # Future features
        future = {
            "dev": "Docker / Git / Dev",
            "vpn": "VPN Gateway",
            "vpn_failover": "VPN Failover",
            "sandbox": "Agent Sandbox",
            "monitoring": "Monitoring / Backup",
        }

        for (
            key,
            title,
        ) in future.items():
            self._set_feature(
                key,
                title,
                "--",
                enabled=False,
            )

    def _set_feature(
        self,
        key: str,
        title: str,
        status: str,
        *,
        enabled: bool,
    ) -> None:
        row = self.query_one(
            f"#feature-{key}",
            FeatureRow,
        )

        row.set_state(
            status=status,
            enabled=enabled,
        )

    # ========================================================
    # SNAPSHOT -> ACTIVE VIEW
    # ========================================================

    def _deliver_snapshot_to_view(
        self,
    ) -> None:
        host = self.query_one(
            "#feature-host",
            Container,
        )

        if not host.children:
            return

        view = host.children[0]

        update = getattr(
            view,
            "update_snapshot",
            None,
        )

        if callable(
            update
        ):
            update(
                self._ping,
                self._snapshot,
                self._backend_online,
            )

    # ========================================================
    # WIFI DETECTION
    # ========================================================

    def _wifi_detected(
        self,
        network: Any,
    ) -> bool:
        if not isinstance(
            network,
            dict,
        ):
            return False

        values = network.get(
            "values",
            {},
        )

        if not isinstance(
            values,
            dict,
        ):
            return False

        item = values.get(
            "interfaces"
        )

        if not isinstance(
            item,
            dict,
        ):
            return False

        interfaces = item.get(
            "value",
            [],
        )

        if not isinstance(
            interfaces,
            list,
        ):
            return False

        return any(
            isinstance(
                interface,
                dict,
            )
            and str(
                interface.get(
                    "name",
                    "",
                )
            ).startswith(
                (
                    "wl",
                    "wlan",
                )
            )
            for interface in interfaces
        )
