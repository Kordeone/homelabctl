"""Base screen for read-only module inspection."""

from __future__ import annotations

from typing import Any

from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static

from homelabctl.client import BackendClient
from homelabctl.core.errors import BackendError
from homelabctl.tui.widgets.status_badge import StatusBadge


class ModuleScreen(Screen):
    MODULE = ""
    SCREEN_TITLE = ""

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(classes="module-screen"):
            with Horizontal(classes="screen-heading"):
                yield Label(
                    self.SCREEN_TITLE,
                    classes="screen-title",
                )

                yield StatusBadge(
                    "unknown",
                    id="module-screen-status",
                )

                yield Button(
                    "Refresh",
                    id="module-refresh",
                    variant="primary",
                )

                yield Button(
                    "Back",
                    id="module-back",
                )

            yield Static(
                "Loading...",
                id="module-screen-summary",
            )

            with VerticalScroll(
                id="module-values"
            ):
                yield Static(
                    "Waiting for backend data...",
                    id="module-values-content",
                )

        yield Footer()

    def on_mount(self) -> None:
        self.refresh_state()

    def action_refresh(self) -> None:
        self.refresh_state()

    def on_button_pressed(
        self,
        event: Button.Pressed,
    ) -> None:
        if event.button.id == "module-back":
            self.app.pop_screen()

        elif event.button.id == "module-refresh":
            self.refresh_state()

    @work(
        exclusive=True,
        group="module-refresh",
    )
    async def refresh_state(self) -> None:
        try:
            data = await BackendClient().get_module(
                self.MODULE
            )
        except BackendError as exc:
            self._show_error(str(exc))
            return

        status = str(
            data.get(
                "status",
                "unknown",
            )
        )

        summary = str(
            data.get(
                "summary",
                "",
            )
        )

        self.query_one(
            "#module-screen-status",
            StatusBadge,
        ).set_status(status)

        self.query_one(
            "#module-screen-summary",
            Static,
        ).update(summary)

        values = data.get(
            "values",
            {}
        )

        self.query_one(
            "#module-values-content",
            Static,
        ).update(
            self._format_values(values)
        )

    def _show_error(
        self,
        message: str,
    ) -> None:
        self.query_one(
            "#module-screen-status",
            StatusBadge,
        ).set_status("error")

        self.query_one(
            "#module-screen-summary",
            Static,
        ).update(message)

        self.query_one(
            "#module-values-content",
            Static,
        ).update(
            "No module data available."
        )

    def _format_values(
        self,
        values: Any,
    ) -> str:
        if not isinstance(values, dict):
            return "No values available."

        lines: list[str] = []

        for key in sorted(values):
            item = values[key]

            if isinstance(item, dict):
                value = item.get(
                    "value"
                )

                readable = item.get(
                    "readable",
                    True,
                )

                error = item.get(
                    "error"
                )

                source = item.get(
                    "source"
                )

                if not readable:
                    displayed = (
                        f"UNREADABLE"
                        f" ({error or 'unknown error'})"
                    )
                else:
                    displayed = self._display_value(
                        value
                    )

                line = (
                    f"{key:<36} {displayed}"
                )

                if source:
                    line += f"    [{source}]"

                lines.append(line)

            else:
                lines.append(
                    f"{key:<36} "
                    f"{self._display_value(item)}"
                )

        if not lines:
            return "No values collected."

        return "\n".join(lines)

    def _display_value(
        self,
        value: Any,
    ) -> str:
        if value is None:
            return "—"

        if isinstance(value, bool):
            return "yes" if value else "no"

        if isinstance(value, (list, dict)):
            return repr(value)

        return str(value)
