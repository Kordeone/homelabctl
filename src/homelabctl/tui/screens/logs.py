"""HomeLabCTL logs screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static


class LogsScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(classes="module-screen"):
            yield Button(
                "Back",
                id="logs-back",
            )

            yield Static(
                (
                    "Log viewer is reserved for the "
                    "logging/audit integration stage."
                ),
                id="logs-content",
            )

        yield Footer()

    def on_button_pressed(
        self,
        event: Button.Pressed,
    ) -> None:
        if event.button.id == "logs-back":
            self.app.pop_screen()
