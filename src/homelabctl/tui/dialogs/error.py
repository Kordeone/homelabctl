"""Generic error dialog."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class ErrorDialog(ModalScreen[None]):
    def __init__(
        self,
        *,
        title: str = "Error",
        message: str,
    ) -> None:
        super().__init__()

        self.dialog_title = title
        self.message = message

    def compose(self) -> ComposeResult:
        with Container(classes="dialog"):
            yield Label(
                self.dialog_title,
                classes="dialog-title",
            )

            yield Static(
                self.message,
                classes="dialog-error",
            )

            yield Button(
                "Close",
                id="error-close",
                variant="primary",
            )

    def on_button_pressed(
        self,
        event: Button.Pressed,
    ) -> None:
        if event.button.id == "error-close":
            self.dismiss(None)
