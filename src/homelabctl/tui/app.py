"""Main HomeLabCTL Textual application."""

from __future__ import annotations

from textual.app import App

from homelabctl.tui.shell import (
    ControlCenterScreen,
)

# Auxiliary screens may remain registered for
# later use from dashboard panels.
from homelabctl.tui.screens.diagnostics import (
    DiagnosticsScreen,
)
from homelabctl.tui.screens.logs import (
    LogsScreen,
)


class HomeLabApp(App):
    TITLE = "HomeLab Control Center"
    SUB_TITLE = "homelabctl"

    CSS_PATH = "homelabctl.tcss"

    BINDINGS = [
        (
            "ctrl+q",
            "quit",
            "Quit",
        ),
    ]

    SCREENS = {
        "control": ControlCenterScreen,
        "diagnostics": DiagnosticsScreen,
        "logs": LogsScreen,
    }

    def on_mount(self) -> None:
        self.push_screen(
            "control"
        )
