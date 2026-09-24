"""Shared keyboard-navigation primitives for HomeLabCTL.

Design rules:

1. Feature screens declare an ENTRY_ID.
2. Feature screens declare directional relationships in NAVIGATION.
3. The shared shell performs movement.
4. Widget-specific interaction remains inside the widget.
5. Select controls open with Space only.
6. DataTable keeps its own arrow navigation.

Future feature pages should inherit NavigableView instead of
implementing their own arrow-key systems.
"""

from __future__ import annotations

from typing import Any

from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Select


# Special navigation target understood by the shared shell.
SIDEBAR_TARGET = "@sidebar"


class SpaceSelect(Select):
    """Select which opens only with Space while collapsed.

    Standard Textual Select binds:
        Enter / Down / Space / Up

    HomeLabCTL intentionally uses:
        Space -> open menu
        Arrow keys -> global component navigation

    Once the Select overlay owns focus, its option list may use
    arrow keys normally.
    """

    BINDINGS = [
        Binding(
            "space",
            "show_overlay",
            "Open",
            show=False,
        ),
    ]


class NavigableView(Widget):
    """Base class for feature content with declarative navigation."""

    ENTRY_ID: str | None = None

    # Example:
    #
    # NAVIGATION = {
    #     "button-a": {
    #         "right": "button-b",
    #         "left": SIDEBAR_TARGET,
    #     },
    # }
    NAVIGATION: dict[
        str,
        dict[str, str],
    ] = {}

    def focus_entry(self) -> bool:
        """Focus the feature's declared entry widget."""

        if not self.ENTRY_ID:
            return False

        return self.focus_target(
            self.ENTRY_ID
        )

    def focus_target(
        self,
        target_id: str,
    ) -> bool:
        """Focus a widget by id inside this feature."""

        try:
            widget = self.query_one(
                f"#{target_id}"
            )

        except Exception:
            return False

        if getattr(
            widget,
            "disabled",
            False,
        ):
            return False

        try:
            widget.focus()

        except Exception:
            return False

        return True

    def navigation_target(
        self,
        focused: Any,
        direction: str,
    ) -> str | None:
        """Return target id for a directional move."""

        focused_id = getattr(
            focused,
            "id",
            None,
        )

        if not focused_id:
            return None

        node = self.NAVIGATION.get(
            focused_id
        )

        if not node:
            return None

        return node.get(
            direction
        )
