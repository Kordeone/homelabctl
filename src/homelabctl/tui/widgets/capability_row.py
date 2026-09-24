"""Single capability row."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label, Static

from homelabctl.tui.widgets.status_badge import (
    StatusBadge,
)


class CapabilityRow(Horizontal):
    def __init__(
        self,
        name: str,
        state: str,
        *,
        reason: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)

        self.capability_name = name
        self.capability_state = state
        self.reason = reason

    def compose(self) -> ComposeResult:
        yield Label(
            self.capability_name,
            classes="row-title",
        )

        yield StatusBadge(
            self.capability_state,
            classes="row-status",
        )

        yield Static(
            self.reason or "",
            classes="row-detail",
        )
