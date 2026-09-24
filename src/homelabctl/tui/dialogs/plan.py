"""Change-plan preview dialog."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from homelabctl.core.models import ChangePlan


class PlanDialog(ModalScreen[bool]):
    def __init__(
        self,
        plan: ChangePlan,
    ) -> None:
        super().__init__()
        self.plan = plan

    def compose(self) -> ComposeResult:
        with Container(classes="dialog"):
            yield Label(
                self.plan.title,
                classes="dialog-title",
            )

            yield Static(
                self.plan.summary,
                classes="dialog-summary",
            )

            yield Static(
                (
                    f"Risk: {self.plan.risk.value.upper()}   "
                    f"Root required: "
                    f"{'YES' if self.plan.requires_root else 'NO'}   "
                    f"Reboot required: "
                    f"{'YES' if self.plan.requires_reboot else 'NO'}"
                ),
                classes="dialog-meta",
            )

            with VerticalScroll(
                classes="dialog-content"
            ):
                yield Static(
                    self._render_plan()
                )

            yield Button(
                "Continue",
                id="plan-continue",
                variant="primary",
            )

            yield Button(
                "Cancel",
                id="plan-cancel",
            )

    def _render_plan(self) -> str:
        lines: list[str] = []

        if self.plan.warnings:
            lines.append("WARNINGS")
            lines.append("--------")

            for warning in self.plan.warnings:
                lines.append(
                    f"• {warning}"
                )

            lines.append("")

        lines.append("CHANGES")
        lines.append("-------")

        if not self.plan.steps:
            lines.append(
                "No changes are required."
            )

        for index, step in enumerate(
            self.plan.steps,
            start=1,
        ):
            lines.append(
                f"{index}. {step.description}"
            )

            if step.target:
                lines.append(
                    f"   Target: {step.target}"
                )

            if step.command_preview:
                lines.append(
                    f"   Command: {step.command_preview}"
                )

            lines.append(
                "   Root: "
                + (
                    "yes"
                    if step.requires_root
                    else "no"
                )
            )

            lines.append(
                "   Reversible: "
                + (
                    "yes"
                    if step.reversible
                    else "no"
                )
            )

            lines.append("")

        return "\n".join(lines)

    def on_button_pressed(
        self,
        event: Button.Pressed,
    ) -> None:
        if event.button.id == "plan-continue":
            self.dismiss(True)

        elif event.button.id == "plan-cancel":
            self.dismiss(False)
