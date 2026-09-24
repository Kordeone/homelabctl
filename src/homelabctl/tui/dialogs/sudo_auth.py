"""Sudo authorization information dialog.

HomeLabCTL never collects the sudo password itself. Authentication is handled
by sudo in the foreground terminal.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class SudoAuthDialog(ModalScreen[bool]):
    def compose(self) -> ComposeResult:
        with Container(classes="dialog"):
            yield Label(
                "Administrator authorization",
                classes="dialog-title",
            )

            yield Static(
                (
                    "This change requires temporary "
                    "administrator privileges.\n\n"
                    "HomeLabCTL does not store or read "
                    "your sudo password. Authentication "
                    "will be handled directly by sudo."
                ),
                classes="dialog-summary",
            )

            yield Button(
                "Authorize with sudo",
                id="sudo-continue",
                variant="primary",
            )

            yield Button(
                "Cancel",
                id="sudo-cancel",
            )

    def on_button_pressed(
        self,
        event: Button.Pressed,
    ) -> None:
        if event.button.id == "sudo-continue":
            self.dismiss(True)

        elif event.button.id == "sudo-cancel":
            self.dismiss(False)
