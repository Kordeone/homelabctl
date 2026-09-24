"""Desired-versus-actual configuration row."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label, Static

from homelabctl.tui.widgets.status_badge import (
    StatusBadge,
)


class DriftRow(Horizontal):
    def __init__(
        self,
        name: str,
        *,
        desired: object,
        actual: object,
        matches: bool,
        reason: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)

        self.setting_name = name
        self.desired = desired
        self.actual = actual
        self.matches = matches
        self.reason = reason

    def compose(self) -> ComposeResult:
        yield Label(
            self.setting_name,
            classes="row-title",
        )

        yield StatusBadge(
            "pass" if self.matches else "drift",
            classes="row-status",
        )

        detail = (
            f"Expected: {self.desired!s}   "
            f"Actual: {self.actual!s}"
        )

        if self.reason:
            detail += f"   {self.reason}"

        yield Static(
            detail,
            classes="row-detail",
        )
