"""Compact keyboard-navigable feature entry."""

from __future__ import annotations

from textual.binding import Binding
from textual.message import Message
from textual.widgets import Static


class FeatureRow(
    Static,
    can_focus=True,
):
    """One-line feature navigation row."""

    BINDINGS = [
        Binding(
            "enter",
            "activate",
            "Open",
            show=False,
        ),
    ]

    class Activated(Message):
        def __init__(
            self,
            feature_key: str,
        ) -> None:
            super().__init__()
            self.feature_key = feature_key

    def __init__(
        self,
        *,
        feature_key: str,
        title: str,
        status: str = "--",
        enabled: bool = False,
        id: str | None = None,
    ) -> None:
        super().__init__(
            "",
            id=id,
            classes="feature-row",
            markup=True,
        )

        self.feature_key = feature_key
        self.title_text = title
        self.feature_enabled = enabled

        self.set_state(
            status=status,
            enabled=enabled,
        )

    def set_state(
        self,
        *,
        status: str,
        enabled: bool,
    ) -> None:
        self.feature_enabled = enabled

        self.set_class(
            enabled,
            "feature-ready",
        )

        self.set_class(
            not enabled,
            "feature-unavailable",
        )

        normalized = status.upper()

        if normalized in {
            "READY",
            "PASS",
        }:
            color = "green"

        elif normalized in {
            "NEXT",
            "AVAIL",
            "WARN",
        }:
            color = "yellow"

        else:
            color = "dim"

        title = self.title_text[:18]

        self.update(
            (
                f"[b]{title:<18}[/b] "
                f"[{color}]"
                f"{normalized:>6}"
                f"[/{color}]"
            )
        )

    def action_activate(
        self,
    ) -> None:
        if not self.feature_enabled:
            return

        self.post_message(
            self.Activated(
                self.feature_key
            )
        )

    def on_click(
        self,
    ) -> None:
        self.focus()
