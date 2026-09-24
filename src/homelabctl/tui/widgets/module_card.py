"""Dashboard module card."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button, Label, Static

from homelabctl.tui.widgets.status_badge import (
    StatusBadge,
)


class ModuleCard(Container):
    """Small dashboard card representing one module."""

    def __init__(
        self,
        *,
        module: str,
        title: str,
        status: str = "unknown",
        summary: str = "",
        screen: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            classes="module-card",
        )

        self.module_key = module
        self.title_text = title
        self.status_value = status
        self.summary_text = summary

        # Do not use `self.screen`.
        # Textual Widget already owns that property.
        self.target_screen = screen

    def compose(self) -> ComposeResult:
        yield Label(
            self.title_text,
            classes="module-card-title",
        )

        yield StatusBadge(
            self.status_value,
            classes="module-card-status",
        )

        yield Static(
            self.summary_text,
            classes="module-card-summary",
        )

        if self.target_screen:
            yield Button(
                "Open",
                id=f"open-{self.module_key}",
                classes="module-card-open",
            )

    def update_state(
        self,
        *,
        status: str,
        summary: str | None = None,
    ) -> None:
        self.status_value = status

        self.query_one(
            ".module-card-status",
            StatusBadge,
        ).set_status(status)

        if summary is not None:
            self.summary_text = summary

            self.query_one(
                ".module-card-summary",
                Static,
            ).update(summary)
