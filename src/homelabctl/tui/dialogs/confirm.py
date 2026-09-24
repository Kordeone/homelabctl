"""First configuration-change confirmation dialog."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class ConfirmDialog(ModalScreen[bool]):
    def __init__(
        self,
        *,
        title: str,
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
                classes="dialog-summary",
            )

            yield Button(
                "Continue",
                id="confirm-yes",
                variant="warning",
            )

            yield Button(
                "Cancel",
                id="confirm-no",
            )

    def on_button_pressed(
        self,
        event: Button.Pressed,
    ) -> None:
        if event.button.id == "confirm-yes":
            self.dismiss(True)

        elif event.button.id == "confirm-no":
            self.dismiss(False)
