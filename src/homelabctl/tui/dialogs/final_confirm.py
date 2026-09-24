"""Final destructive-action confirmation."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Label,
    Static,
)


CONFIRMATION_TEXT = "APPLY"


class FinalConfirmDialog(ModalScreen[bool]):
    def __init__(
        self,
        *,
        title: str = "Final confirmation",
        message: str = (
            "This operation will modify system "
            "configuration."
        ),
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

            yield Static(
                (
                    "Type APPLY exactly to authorize "
                    "the change."
                ),
                classes="dialog-warning",
            )

            yield Input(
                placeholder="APPLY",
                id="final-confirm-input",
            )

            yield Button(
                "Apply",
                id="final-confirm-apply",
                variant="error",
                disabled=True,
            )

            yield Button(
                "Cancel",
                id="final-confirm-cancel",
            )

    def on_input_changed(
        self,
        event: Input.Changed,
    ) -> None:
        if event.input.id != "final-confirm-input":
            return

        button = self.query_one(
            "#final-confirm-apply",
            Button,
        )

        button.disabled = (
            event.value != CONFIRMATION_TEXT
        )

    def on_button_pressed(
        self,
        event: Button.Pressed,
    ) -> None:
        if event.button.id == "final-confirm-apply":
            value = self.query_one(
                "#final-confirm-input",
                Input,
            ).value

            if value == CONFIRMATION_TEXT:
                self.dismiss(True)

        elif event.button.id == "final-confirm-cancel":
            self.dismiss(False)
