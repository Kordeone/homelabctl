"""Diagnostics screen."""

from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from homelabctl.client import BackendClient
from homelabctl.core.errors import BackendError


class DiagnosticsScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(classes="module-screen"):
            yield Button(
                "Refresh",
                id="diagnostics-refresh",
                variant="primary",
            )

            yield Button(
                "Back",
                id="diagnostics-back",
            )

            yield Static(
                "Loading diagnostics...",
                id="diagnostics-content",
            )

        yield Footer()

    def on_mount(self) -> None:
        self.refresh_data()

    def action_refresh(self) -> None:
        self.refresh_data()

    def on_button_pressed(
        self,
        event: Button.Pressed,
    ) -> None:
        if event.button.id == "diagnostics-back":
            self.app.pop_screen()

        elif event.button.id == "diagnostics-refresh":
            self.refresh_data()

    @work(
        exclusive=True,
        group="diagnostics",
    )
    async def refresh_data(self) -> None:
        try:
            ping = await BackendClient().ping()
            snapshot = await BackendClient().snapshot()

        except BackendError as exc:
            self.query_one(
                "#diagnostics-content",
                Static,
            ).update(
                f"Backend error:\n{exc}"
            )
            return

        modules = snapshot.get(
            "modules",
            {}
        )

        capabilities = snapshot.get(
            "capabilities",
            {}
        )

        lines = [
            "BACKEND",
            "-------",
            f"Service:  {ping.get('service')}",
            f"Version:  {ping.get('backend_version')}",
            f"Protocol: {ping.get('protocol_version')}",
            f"Mode:     {ping.get('mode')}",
            "",
            "MODULES",
            "-------",
        ]

        if isinstance(modules, dict):
            for name in sorted(modules):
                module = modules[name]

                if isinstance(module, dict):
                    status = module.get(
                        "status",
                        "unknown",
                    )
                else:
                    status = "unknown"

                lines.append(
                    f"{name:<20} {status}"
                )

        lines.extend(
            [
                "",
                "CAPABILITIES",
                "------------",
            ]
        )

        if isinstance(capabilities, dict):
            for name in sorted(capabilities):
                capability = capabilities[name]

                if isinstance(capability, dict):
                    state = capability.get(
                        "state",
                        "unknown",
                    )

                    reason = capability.get(
                        "reason"
                    )
                else:
                    state = "unknown"
                    reason = None

                text = (
                    f"{name:<30} {state}"
                )

                if reason:
                    text += f" — {reason}"

                lines.append(text)

        self.query_one(
            "#diagnostics-content",
            Static,
        ).update(
            "\n".join(lines)
        )
