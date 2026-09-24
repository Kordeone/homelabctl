"""Dashboard content view.

Navigation chrome is owned by ControlCenterScreen.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Any

from textual.app import ComposeResult
from textual.containers import (
    Container,
    Grid,
)
from textual.widget import Widget
from homelabctl.tui.navigation import (
    NavigableView,
    SIDEBAR_TARGET,
)

from textual.widgets import (
    Button,
    RichLog,
    Static,
)


class DashboardView(NavigableView):
    """Dashboard content only."""

    ENTRY_ID = "panel-state"

    NAVIGATION = {
        "panel-state": {
            "left": SIDEBAR_TARGET,
            "right": "panel-logs",
            "down": "panel-diagnostics",
        },
        "panel-logs": {
            "left": "panel-state",
            "down": "panel-file-watch",
        },
        "panel-diagnostics": {
            "left": SIDEBAR_TARGET,
            "right": "panel-file-watch",
            "up": "panel-state",
        },
        "panel-file-watch": {
            "left": "panel-diagnostics",
            "up": "panel-logs",
        },
    }

    can_focus = False

    def __init__(self) -> None:
        super().__init__(
            id="dashboard-view"
        )

        self._events: deque[
            tuple[str, str, str]
        ] = deque(
            maxlen=80
        )

        self._previous_statuses: dict[
            str,
            str,
        ] = {}

        self._seen_file_events: set[
            tuple[str, str, str]
        ] = set()

        self._started = False

    def compose(self) -> ComposeResult:
        with Grid(
            id="dashboard-grid"
        ):

            # STATE
            with Container(
                id="dashboard-state-panel",
                classes="dashboard-panel",
            ):
                yield Button(
                    "Backend State & Snapshot",
                    id="panel-state",
                    classes="panel-header-button",
                )

                yield Static(
                    "Waiting for backend...",
                    id="state-content",
                    classes="panel-content",
                )

            # LOGS
            with Container(
                id="dashboard-logs-panel",
                classes="dashboard-panel",
            ):
                yield Button(
                    "Logs (live)",
                    id="panel-logs",
                    classes="panel-header-button",
                )

                yield RichLog(
                    id="logs-live",
                    markup=True,
                    wrap=False,
                    highlight=False,
                    max_lines=80,
                )

            # DIAGNOSTICS
            with Container(
                id="dashboard-diagnostics-panel",
                classes="dashboard-panel",
            ):
                yield Button(
                    "Diagnostics (live)",
                    id="panel-diagnostics",
                    classes="panel-header-button",
                )

                yield RichLog(
                    id="diagnostics-live",
                    markup=True,
                    wrap=False,
                    highlight=False,
                    max_lines=60,
                )

            # FILE WATCH
            with Container(
                id="dashboard-file-watch-panel",
                classes="dashboard-panel",
            ):
                yield Button(
                    "File Watch (recent changes)",
                    id="panel-file-watch",
                    classes="panel-header-button",
                )

                yield RichLog(
                    id="file-watch-live",
                    markup=True,
                    wrap=False,
                    highlight=False,
                    max_lines=40,
                )

    # ========================================================
    # SHELL API
    # ========================================================

    def focus_entry(self) -> None:
        self.query_one(
            "#panel-state",
            Button,
        ).focus()

    def update_snapshot(
        self,
        ping: dict[str, Any],
        snapshot: dict[str, Any],
        online: bool,
    ) -> None:
        if not self._started:
            self._started = True

            self._log(
                "INFO",
                "frontend dashboard active",
            )

        if not online:
            self.query_one(
                "#state-content",
                Static,
            ).update(
                "Backend offline."
            )

            self._log(
                "WARN",
                "backend unavailable",
            )

            self._render_logs()

            return

        modules = snapshot.get(
            "modules",
            {},
        )

        capabilities = snapshot.get(
            "capabilities",
            {},
        )

        if not isinstance(
            modules,
            dict,
        ):
            modules = {}

        if not isinstance(
            capabilities,
            dict,
        ):
            capabilities = {}

        self._record_state_changes(
            modules
        )

        self._consume_file_events(
            modules
        )

        self._render_state(
            modules
        )

        self._render_diagnostics(
            modules,
            capabilities,
        )

        self._render_file_watch(
            modules
        )

        self._render_logs()

    # ========================================================
    # RENDER STATE
    # ========================================================

    def _render_state(
        self,
        modules: dict[str, Any],
    ) -> None:
        system = modules.get(
            "system",
            {},
        )

        values = (
            system.get(
                "values",
                {},
            )
            if isinstance(
                system,
                dict,
            )
            else {}
        )

        hostname = self._value(
            values,
            "hostname",
            "—",
        )

        os_id = self._value(
            values,
            "os_id",
            "Linux",
        )

        os_version = self._value(
            values,
            "os_version",
            "",
        )

        kernel = self._value(
            values,
            "kernel",
            "—",
        )

        uptime = self._format_duration(
            self._value(
                values,
                "uptime_seconds",
                None,
            )
        )

        load_1 = self._value(
            values,
            "load_1",
            None,
        )

        load_5 = self._value(
            values,
            "load_5",
            None,
        )

        load_15 = self._value(
            values,
            "load_15",
            None,
        )

        memory_used = self._value(
            values,
            "memory_used_bytes",
            None,
        )

        memory_total = self._value(
            values,
            "memory_total_bytes",
            None,
        )

        memory_percent = self._value(
            values,
            "memory_used_percent",
            None,
        )

        root_used = self._value(
            values,
            "root_used_bytes",
            None,
        )

        root_total = self._value(
            values,
            "root_total_bytes",
            None,
        )

        root_percent = self._value(
            values,
            "root_used_percent",
            None,
        )

        ip = self._primary_ipv4(
            modules
        )

        load_text = "—"

        if None not in (
            load_1,
            load_5,
            load_15,
        ):
            load_text = (
                f"{load_1:.2f}  "
                f"{load_5:.2f}  "
                f"{load_15:.2f}"
            )

        memory_text = "—"

        if (
            memory_used is not None
            and memory_total is not None
        ):
            memory_text = (
                f"{self._human_bytes(memory_used)} / "
                f"{self._human_bytes(memory_total)}"
            )

            if memory_percent is not None:
                memory_text += (
                    f"  {memory_percent}%"
                )

        disk_text = "—"

        if (
            root_used is not None
            and root_total is not None
        ):
            disk_text = (
                f"{self._human_bytes(root_used)} / "
                f"{self._human_bytes(root_total)}"
            )

            if root_percent is not None:
                disk_text += (
                    f"  {root_percent}%"
                )

        os_text = (
            f"{str(os_id).capitalize()} "
            f"{os_version}"
        ).strip()

        lines = [
            f"Hostname       {hostname}",
            f"OS             {os_text}",
            f"Kernel         {kernel}",
            f"Uptime         {uptime}",
            f"Load 1/5/15    {load_text}",
            f"Memory         {memory_text}",
            f"Disk /         {disk_text}",
            f"LAN IPv4       {ip}",
        ]

        self.query_one(
            "#state-content",
            Static,
        ).update(
            "\n".join(
                lines
            )
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def _render_diagnostics(
        self,
        modules: dict[str, Any],
        capabilities: dict[str, Any],
    ) -> None:
        widget = self.query_one(
            "#diagnostics-live",
            RichLog,
        )

        widget.clear()

        labels = {
            "system": "Host",
            "ssh": "SSH",
            "firewall": "Firewall",
            "headless": "Headless",
            "security": "Security",
            "encryption": "Encryption",
            "power": "Power",
            "network": "Network",
            "storage": "Storage",
            "file_watch": "File Watch",
        }

        for (
            key,
            label,
        ) in labels.items():
            module = modules.get(
                key
            )

            if not isinstance(
                module,
                dict,
            ):
                self._diagnostic_line(
                    widget,
                    "UNKNOWN",
                    label,
                    "No data",
                )

                continue

            status = str(
                module.get(
                    "status",
                    "unknown",
                )
            ).upper()

            self._diagnostic_line(
                widget,
                status,
                label,
                self._diagnostic_detail(
                    key,
                    module,
                ),
            )

        hibernate = capabilities.get(
            "power.hibernate"
        )

        if (
            isinstance(
                hibernate,
                dict,
            )
            and hibernate.get(
                "state"
            )
            == "unavailable"
        ):
            self._diagnostic_line(
                widget,
                "WARN",
                "Hibernate",
                str(
                    hibernate.get(
                        "reason",
                        "Unavailable",
                    )
                ),
            )

    def _diagnostic_detail(
        self,
        key: str,
        module: dict[str, Any],
    ) -> str:
        values = module.get(
            "values",
            {},
        )

        if key == "system":
            return "Snapshot ready"

        if key in {
            "ssh",
            "firewall",
        }:
            return (
                "Service "
                + str(
                    self._value(
                        values,
                        "service_active",
                        "?",
                    )
                )
            )

        if key == "headless":
            return (
                "Lid "
                + str(
                    self._value(
                        values,
                        "lid_switch",
                        "?",
                    )
                )
            )

        if key == "security":
            return (
                "Secure Boot on"
                if self._value(
                    values,
                    "secure_boot",
                    False,
                )
                else "Secure Boot off"
            )

        if key == "encryption":
            return (
                "LUKS detected"
                if self._value(
                    values,
                    "luks_present",
                    False,
                )
                else "No LUKS"
            )

        if key == "power":
            return (
                "Profile "
                + str(
                    self._value(
                        values,
                        "power_profile",
                        "?",
                    )
                )
            )

        if key == "network":
            return (
                "LAN "
                + self._primary_ipv4_from_values(
                    values
                )
            )

        if key == "storage":
            return (
                str(
                    self._value(
                        values,
                        "device_count",
                        "?",
                    )
                )
                + " device(s)"
            )

        if key == "file_watch":
            return (
                str(
                    self._value(
                        values,
                        "watched_count",
                        "?",
                    )
                )
                + " managed files"
            )

        return str(
            module.get(
                "summary",
                "",
            )
        )

    # ========================================================
    # FILE WATCH
    # ========================================================

    def _render_file_watch(
        self,
        modules: dict[str, Any],
    ) -> None:
        widget = self.query_one(
            "#file-watch-live",
            RichLog,
        )

        widget.clear()

        module = modules.get(
            "file_watch"
        )

        if not isinstance(
            module,
            dict,
        ):
            widget.write(
                "[dim]File Watch unavailable[/dim]"
            )

            return

        events = self._value(
            module.get(
                "values",
                {},
            ),
            "changed_files",
            [],
        )

        if not isinstance(
            events,
            list,
        ):
            events = []

        widget.write(
            "[dim]TIME      EVENT      FILE[/dim]"
        )

        if not events:
            widget.write("")

            widget.write(
                (
                    "[dim]"
                    "No managed files changed "
                    "since watcher startup."
                    "[/dim]"
                )
            )

            return

        for event in events[:8]:
            if not isinstance(
                event,
                dict,
            ):
                continue

            timestamp = str(
                event.get(
                    "time",
                    "",
                )
            )

            short_time = (
                timestamp[11:19]
                if len(timestamp) >= 19
                else timestamp
            )

            action = str(
                event.get(
                    "event",
                    "changed",
                )
            )

            path = str(
                event.get(
                    "path",
                    "",
                )
            )

            color = (
                "green"
                if action == "created"
                else (
                    "red"
                    if action == "deleted"
                    else "yellow"
                )
            )

            widget.write(
                (
                    f"{short_time:<9} "
                    f"[{color}]"
                    f"{action:<9}"
                    f"[/{color}] "
                    f"{path}"
                )
            )

    # ========================================================
    # LOGS
    # ========================================================

    def _record_state_changes(
        self,
        modules: dict[str, Any],
    ) -> None:
        for (
            name,
            module,
        ) in modules.items():
            if not isinstance(
                module,
                dict,
            ):
                continue

            current = str(
                module.get(
                    "status",
                    "unknown",
                )
            )

            previous = (
                self._previous_statuses.get(
                    name
                )
            )

            if previous is None:
                if current in {
                    "warning",
                    "fail",
                    "error",
                }:
                    self._log(
                        "WARN",
                        (
                            f"{name}: "
                            f"{module.get('summary', current)}"
                        ),
                    )

            elif previous != current:
                self._log(
                    (
                        "INFO"
                        if current == "pass"
                        else "WARN"
                    ),
                    (
                        f"{name}: "
                        f"{previous} -> {current}"
                    ),
                )

            self._previous_statuses[
                name
            ] = current

    def _consume_file_events(
        self,
        modules: dict[str, Any],
    ) -> None:
        module = modules.get(
            "file_watch"
        )

        if not isinstance(
            module,
            dict,
        ):
            return

        events = self._value(
            module.get(
                "values",
                {},
            ),
            "changed_files",
            [],
        )

        if not isinstance(
            events,
            list,
        ):
            return

        for event in reversed(
            events
        ):
            if not isinstance(
                event,
                dict,
            ):
                continue

            identity = (
                str(
                    event.get(
                        "time",
                        "",
                    )
                ),
                str(
                    event.get(
                        "path",
                        "",
                    )
                ),
                str(
                    event.get(
                        "event",
                        "",
                    )
                ),
            )

            if (
                identity
                in self._seen_file_events
            ):
                continue

            self._seen_file_events.add(
                identity
            )

            self._log(
                "INFO",
                (
                    "file: "
                    f"{identity[2]} "
                    f"{identity[1]}"
                ),
            )

    def _log(
        self,
        level: str,
        message: str,
    ) -> None:
        self._events.append(
            (
                datetime.now().strftime(
                    "%H:%M:%S"
                ),
                level,
                message,
            )
        )

    def _render_logs(
        self,
    ) -> None:
        widget = self.query_one(
            "#logs-live",
            RichLog,
        )

        widget.clear()

        for (
            timestamp,
            level,
            message,
        ) in list(
            self._events
        )[-9:]:
            color = (
                "yellow"
                if level == "WARN"
                else (
                    "red"
                    if level == "ERROR"
                    else "green"
                )
            )

            widget.write(
                (
                    f"{timestamp}  "
                    f"[{color}]"
                    f"{level:<5}"
                    f"[/{color}] "
                    f"{message}"
                )
            )

    # ========================================================
    # HELPERS
    # ========================================================

    def _diagnostic_line(
        self,
        widget: RichLog,
        status: str,
        name: str,
        summary: str,
    ) -> None:
        normalized = (
            status.lower()
        )

        if normalized == "pass":
            color = "green"

        elif normalized in {
            "warning",
            "warn",
        }:
            color = "yellow"

        elif normalized in {
            "fail",
            "error",
        }:
            color = "red"

        else:
            color = "dim"

        display = (
            "WARN"
            if normalized == "warning"
            else status
        )

        widget.write(
            (
                f"[{color}]"
                f"{display:<5}"
                f"[/{color}] "
                f"{name:<12} "
                f"{summary}"
            )
        )

    def _value(
        self,
        values: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        if not isinstance(
            values,
            dict,
        ):
            return default

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

        return default

    def _primary_ipv4_from_values(
        self,
        values: dict[str, Any],
    ) -> str:
        addresses = self._value(
            values,
            "addresses",
            [],
        )

        if not isinstance(
            addresses,
            list,
        ):
            return "—"

        for interface in addresses:
            if not isinstance(
                interface,
                dict,
            ):
                continue

            if interface.get(
                "ifname"
            ) == "lo":
                continue

            for address in interface.get(
                "addr_info",
                [],
            ):
                if (
                    isinstance(
                        address,
                        dict,
                    )
                    and address.get(
                        "family"
                    )
                    == "inet"
                    and address.get(
                        "scope"
                    )
                    == "global"
                ):
                    return str(
                        address.get(
                            "local",
                            "—",
                        )
                    )

        return "—"

    def _primary_ipv4(
        self,
        modules: dict[str, Any],
    ) -> str:
        network = modules.get(
            "network"
        )

        if not isinstance(
            network,
            dict,
        ):
            return "—"

        return (
            self._primary_ipv4_from_values(
                network.get(
                    "values",
                    {},
                )
            )
        )

    def _human_bytes(
        self,
        value: Any,
    ) -> str:
        try:
            number = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return "—"

        units = (
            "B",
            "KiB",
            "MiB",
            "GiB",
            "TiB",
        )

        for unit in units:
            if (
                abs(number) < 1024
                or unit
                == units[-1]
            ):
                if unit in {
                    "GiB",
                    "TiB",
                }:
                    return (
                        f"{number:.1f} "
                        f"{unit}"
                    )

                return (
                    f"{number:.0f} "
                    f"{unit}"
                )

            number /= 1024

        return "—"

    def _format_duration(
        self,
        value: Any,
    ) -> str:
        try:
            seconds = int(
                float(
                    value
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            return "—"

        days, seconds = divmod(
            seconds,
            86400,
        )

        hours, seconds = divmod(
            seconds,
            3600,
        )

        minutes, _ = divmod(
            seconds,
            60,
        )

        parts: list[str] = []

        if days:
            parts.append(
                f"{days}d"
            )

        if (
            hours
            or days
        ):
            parts.append(
                f"{hours}h"
            )

        parts.append(
            f"{minutes}m"
        )

        return " ".join(
            parts
        )
