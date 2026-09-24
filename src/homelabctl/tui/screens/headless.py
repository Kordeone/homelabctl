"""Headless and sleep-policy feature content."""

from __future__ import annotations

from typing import Any

from rich.text import Text

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import (
    Container,
    Grid,
    Horizontal,
    Vertical,
    VerticalScroll,
)
from textual.widgets import (
    Button,
    ContentSwitcher,
    Input,
    Static,
)

from homelabctl.apply.sudo import (
    run_privileged_transaction,
)
from homelabctl.core.actual_state import (
    make_actual_state,
)
from homelabctl.core.models import (
    ModuleActualState,
    Status,
)
from homelabctl.features.headless.apply import (
    build_apply_transaction,
)
from homelabctl.features.headless.plan import (
    LOGIND_DROP_IN,
    build_headless_plan,
    render_logind_config,
)
from homelabctl.features.headless.schema import (
    HeadlessSettings,
)
from homelabctl.features.headless.verify import (
    verify,
)
from homelabctl.system.runtime_defaults import (
    current_user,
)
from homelabctl.tui.dialogs.final_confirm import (
    FinalConfirmDialog,
)
from homelabctl.tui.dialogs.plan import (
    PlanDialog,
)
from homelabctl.tui.navigation import (
    NavigableView,
    SIDEBAR_TARGET,
    SpaceSelect,
)


SYSTEM_EVENT_OPTIONS = (
    ("Ignore", "ignore"),
    ("Power off", "poweroff"),
    ("Reboot", "reboot"),
    ("Suspend", "suspend"),
    ("Hibernate", "hibernate"),
    ("Hybrid sleep", "hybrid-sleep"),
    (
        "Suspend then hibernate",
        "suspend-then-hibernate",
    ),
    ("Automatic sleep", "sleep"),
    ("Lock sessions", "lock"),
)

IDLE_ACTION_OPTIONS = (
    ("Ignore", "ignore"),
    ("Power off", "poweroff"),
    ("Suspend", "suspend"),
    ("Hibernate", "hibernate"),
    ("Hybrid sleep", "hybrid-sleep"),
    (
        "Suspend then hibernate",
        "suspend-then-hibernate",
    ),
    ("Automatic sleep", "sleep"),
    ("Lock sessions", "lock"),
)

DESKTOP_POWER_OPTIONS = (
    ("Do nothing", "nothing"),
    ("Blank screen", "blank"),
    ("Suspend", "suspend"),
    ("Hibernate", "hibernate"),
    ("Shut down", "shutdown"),
    ("Interactive", "interactive"),
    ("Log out", "logout"),
)

SYSTEM_EVENT_VALUES = frozenset(
    value
    for _label, value in SYSTEM_EVENT_OPTIONS
)

IDLE_ACTION_VALUES = frozenset(
    value
    for _label, value in IDLE_ACTION_OPTIONS
)

DESKTOP_POWER_VALUES = frozenset(
    value
    for _label, value in DESKTOP_POWER_OPTIONS
)


class HeadlessView(NavigableView):
    """Headless configuration inside the shared shell."""

    BINDINGS = [
        Binding(
            "ctrl+1",
            "show_configure",
            "Configure",
            show=False,
        ),
        Binding(
            "ctrl+2",
            "show_inspect",
            "Inspect",
            show=False,
        ),
    ]

    ENTRY_ID = "headless-tab-configure"

    NAVIGATION = {
        "headless-tab-configure": {
            "left": SIDEBAR_TARGET,
            "right": "headless-tab-inspect",
        },
        "headless-tab-inspect": {
            "left": "headless-tab-configure",
        },

        "headless-lid-battery": {
            "up": "headless-tab-configure",
            "down": "headless-lid-ac",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },
        "headless-lid-ac": {
            "up": "headless-lid-battery",
            "down": "headless-lid-docked",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },
        "headless-lid-docked": {
            "up": "headless-lid-ac",
            "down": "headless-power-short",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },
        "headless-power-short": {
            "up": "headless-lid-docked",
            "down": "headless-power-long",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },
        "headless-power-long": {
            "up": "headless-power-short",
            "down": "headless-idle-action",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },
        "headless-idle-action": {
            "up": "headless-power-long",
            "down": "headless-idle-timeout",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },
        "headless-idle-timeout": {
            "up": "headless-idle-action",
            "down": "headless-desktop-user",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },

        "headless-desktop-user": {
            "up": "headless-idle-timeout",
            "down": "headless-user-ac-action",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },
        "headless-user-ac-action": {
            "up": "headless-desktop-user",
            "down": "headless-user-ac-timeout",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },
        "headless-user-ac-timeout": {
            "up": "headless-user-ac-action",
            "down": "headless-user-battery-action",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },
        "headless-user-battery-action": {
            "up": "headless-user-ac-timeout",
            "down": "headless-user-battery-timeout",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },
        "headless-user-battery-timeout": {
            "up": "headless-user-battery-action",
            "down": "headless-gdm-ac-action",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },

        "headless-gdm-ac-action": {
            "up": "headless-user-battery-timeout",
            "down": "headless-gdm-ac-timeout",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },
        "headless-gdm-ac-timeout": {
            "up": "headless-gdm-ac-action",
            "down": "headless-gdm-battery-action",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },
        "headless-gdm-battery-action": {
            "up": "headless-gdm-ac-timeout",
            "down": "headless-gdm-battery-timeout",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },
        "headless-gdm-battery-timeout": {
            "up": "headless-gdm-battery-action",
            "left": SIDEBAR_TARGET,
            "right": "headless-preset",
        },

        "headless-preset": {
            "left": "headless-lid-battery",
            "up": "headless-tab-configure",
            "down": "headless-action-preview",
        },
        "headless-action-preview": {
            "left": "headless-gdm-battery-timeout",
            "right": "headless-apply",
            "up": "headless-preset",
            "down": "headless-verify",
        },
        "headless-apply": {
            "left": "headless-action-preview",
            "up": "headless-preset",
            "down": "headless-reset",
        },
        "headless-verify": {
            "left": "headless-gdm-battery-timeout",
            "right": "headless-reset",
            "up": "headless-action-preview",
        },
        "headless-reset": {
            "left": "headless-verify",
            "up": "headless-apply",
        },

        "headless-inspect-verification": {
            "up": "headless-tab-inspect",
            "left": SIDEBAR_TARGET,
            "right": "headless-inspect-power",
        },
        "headless-inspect-power": {
            "up": "headless-tab-inspect",
            "left": "headless-inspect-verification",
        },
    }

    def __init__(self) -> None:
        super().__init__(
            id="headless-view"
        )

        self._page = "configure"

        self._headless_module: dict[str, Any] = {}
        self._power_module: dict[str, Any] = {}

        self._pending_apply: Any | None = None
        self._draft_initialized = False

    # ========================================================
    # COMPOSE
    # ========================================================

    def compose(self) -> ComposeResult:
        with Vertical(
            id="headless-content"
        ):
            with Horizontal(
                id="headless-feature-header"
            ):
                with Vertical(
                    id="headless-feature-heading"
                ):
                    yield Static(
                        "Headless & Power",
                        id="headless-title",
                    )

                    yield Static(
                        (
                            "Configure lid, power-button, idle, "
                            "desktop-session, and login-screen "
                            "power behavior."
                        ),
                        id="headless-description",
                    )

                yield Static(
                    "Status: [yellow]CHECKING[/yellow]",
                    id="headless-status",
                    markup=True,
                )

            with Horizontal(
                id="headless-page-selector"
            ):
                yield Button(
                    "1  Configure",
                    id="headless-tab-configure",
                    classes=(
                        "headless-page-tab "
                        "active-page-tab"
                    ),
                )

                yield Button(
                    "2  Inspect",
                    id="headless-tab-inspect",
                    classes="headless-page-tab",
                )

                yield Static(
                    f"Managed file: {LOGIND_DROP_IN}",
                    id="headless-managed-file-label",
                )

            with ContentSwitcher(
                initial="headless-page-configure",
                id="headless-page-switcher",
            ):
                with VerticalScroll(
                    id="headless-page-configure"
                ):
                    with Grid(
                        id="headless-configure-grid"
                    ):
                        with Container(
                            id="headless-current-panel",
                            classes=(
                                "headless-box "
                                "headless-page-panel"
                            ),
                        ):
                            yield Static(
                                "Current State (live)",
                                classes="headless-box-title",
                            )

                            yield Static(
                                "Waiting for backend snapshot...",
                                id="headless-current-content",
                                classes="headless-box-body",
                                markup=True,
                            )

                        with Container(
                            id="headless-config-panel",
                            classes=(
                                "headless-box "
                                "headless-page-panel"
                            ),
                        ):
                            yield Static(
                                "Desired Power Policy",
                                classes="headless-box-title",
                            )

                            with VerticalScroll(
                                id="headless-config-scroll"
                            ):
                                yield Static(
                                    "System Events",
                                    classes="headless-section-title",
                                )

                                with Grid(
                                    id="headless-system-grid"
                                ):
                                    yield Static(
                                        "Lid close — battery",
                                        classes="headless-field-label",
                                    )
                                    yield SpaceSelect(
                                        SYSTEM_EVENT_OPTIONS,
                                        value="ignore",
                                        allow_blank=False,
                                        id="headless-lid-battery",
                                        classes="headless-field-control",
                                    )

                                    yield Static(
                                        "Lid close — AC",
                                        classes="headless-field-label",
                                    )
                                    yield SpaceSelect(
                                        SYSTEM_EVENT_OPTIONS,
                                        value="ignore",
                                        allow_blank=False,
                                        id="headless-lid-ac",
                                        classes="headless-field-control",
                                    )

                                    yield Static(
                                        "Lid close — docked",
                                        classes="headless-field-label",
                                    )
                                    yield SpaceSelect(
                                        SYSTEM_EVENT_OPTIONS,
                                        value="ignore",
                                        allow_blank=False,
                                        id="headless-lid-docked",
                                        classes="headless-field-control",
                                    )

                                    yield Static(
                                        "Power button",
                                        classes="headless-field-label",
                                    )
                                    yield SpaceSelect(
                                        SYSTEM_EVENT_OPTIONS,
                                        value="poweroff",
                                        allow_blank=False,
                                        id="headless-power-short",
                                        classes="headless-field-control",
                                    )

                                    yield Static(
                                        "Power long press",
                                        classes="headless-field-label",
                                    )
                                    yield SpaceSelect(
                                        SYSTEM_EVENT_OPTIONS,
                                        value="ignore",
                                        allow_blank=False,
                                        id="headless-power-long",
                                        classes="headless-field-control",
                                    )

                                    yield Static(
                                        "Idle action",
                                        classes="headless-field-label",
                                    )
                                    yield SpaceSelect(
                                        IDLE_ACTION_OPTIONS,
                                        value="ignore",
                                        allow_blank=False,
                                        id="headless-idle-action",
                                        classes="headless-field-control",
                                    )

                                    yield Static(
                                        "Idle delay (seconds)",
                                        classes="headless-field-label",
                                    )
                                    yield Input(
                                        value="1800",
                                        type="integer",
                                        id="headless-idle-timeout",
                                        classes="headless-field-control",
                                    )

                                yield Static(
                                    "Desktop Session",
                                    classes="headless-section-title",
                                )

                                with Grid(
                                    id="headless-desktop-grid"
                                ):
                                    yield Static(
                                        "Desktop user",
                                        classes="headless-field-label",
                                    )
                                    yield Input(
                                        value=current_user(),
                                        placeholder="server-user",
                                        id="headless-desktop-user",
                                        classes="headless-field-control",
                                    )

                                    yield Static(
                                        "AC idle action",
                                        classes="headless-field-label",
                                    )
                                    yield SpaceSelect(
                                        DESKTOP_POWER_OPTIONS,
                                        value="nothing",
                                        allow_blank=False,
                                        id="headless-user-ac-action",
                                        classes="headless-field-control",
                                    )

                                    yield Static(
                                        "AC timeout (seconds)",
                                        classes="headless-field-label",
                                    )
                                    yield Input(
                                        value="900",
                                        type="integer",
                                        id="headless-user-ac-timeout",
                                        classes="headless-field-control",
                                    )

                                    yield Static(
                                        "Battery idle action",
                                        classes="headless-field-label",
                                    )
                                    yield SpaceSelect(
                                        DESKTOP_POWER_OPTIONS,
                                        value="nothing",
                                        allow_blank=False,
                                        id="headless-user-battery-action",
                                        classes="headless-field-control",
                                    )

                                    yield Static(
                                        "Battery timeout (seconds)",
                                        classes="headless-field-label",
                                    )
                                    yield Input(
                                        value="900",
                                        type="integer",
                                        id="headless-user-battery-timeout",
                                        classes="headless-field-control",
                                    )

                                yield Static(
                                    "Login Screen (GDM)",
                                    classes="headless-section-title",
                                )

                                with Grid(
                                    id="headless-gdm-grid"
                                ):
                                    yield Static(
                                        "AC idle action",
                                        classes="headless-field-label",
                                    )
                                    yield SpaceSelect(
                                        DESKTOP_POWER_OPTIONS,
                                        value="nothing",
                                        allow_blank=False,
                                        id="headless-gdm-ac-action",
                                        classes="headless-field-control",
                                    )

                                    yield Static(
                                        "AC timeout (seconds)",
                                        classes="headless-field-label",
                                    )
                                    yield Input(
                                        value="0",
                                        type="integer",
                                        id="headless-gdm-ac-timeout",
                                        classes="headless-field-control",
                                    )

                                    yield Static(
                                        "Battery idle action",
                                        classes="headless-field-label",
                                    )
                                    yield SpaceSelect(
                                        DESKTOP_POWER_OPTIONS,
                                        value="nothing",
                                        allow_blank=False,
                                        id="headless-gdm-battery-action",
                                        classes="headless-field-control",
                                    )

                                    yield Static(
                                        "Battery timeout (seconds)",
                                        classes="headless-field-label",
                                    )
                                    yield Input(
                                        value="0",
                                        type="integer",
                                        id="headless-gdm-battery-timeout",
                                        classes="headless-field-control",
                                    )

                        with Container(
                            id="headless-actions-panel",
                            classes=(
                                "headless-box "
                                "headless-page-panel"
                            ),
                        ):
                            yield Static(
                                "Actions & Preview",
                                classes="headless-box-title",
                            )

                            yield Button(
                                "Load Headless Preset",
                                id="headless-preset",
                            )

                            with Grid(
                                id="headless-actions-grid"
                            ):
                                yield Button(
                                    "Preview",
                                    id="headless-action-preview",
                                )

                                yield Button(
                                    "Apply",
                                    id="headless-apply",
                                    disabled=True,
                                )

                                yield Button(
                                    "Verify",
                                    id="headless-verify",
                                )

                                yield Button(
                                    "Reset to Live",
                                    id="headless-reset",
                                )

                            with VerticalScroll(
                                id="headless-preview-scroll"
                            ):
                                yield Static(
                                    (
                                        "[dim]"
                                        "Press Preview to render the "
                                        "managed configuration."
                                        "[/dim]"
                                    ),
                                    id="headless-preview-content",
                                    markup=True,
                                )

                with VerticalScroll(
                    id="headless-page-inspect"
                ):
                    with Grid(
                        id="headless-inspect-grid"
                    ):
                        with Container(
                            id="headless-verification-panel",
                            classes="headless-box",
                        ):
                            yield Static(
                                "Verification",
                                classes="headless-box-title",
                            )

                            yield Static(
                                "Waiting for backend snapshot...",
                                id=(
                                    "headless-inspect-verification"
                                ),
                                classes="headless-box-body",
                                markup=True,
                            )

                        with Container(
                            id="headless-power-panel",
                            classes="headless-box",
                        ):
                            yield Static(
                                "Power State",
                                classes="headless-box-title",
                            )

                            yield Static(
                                "Waiting for power snapshot...",
                                id="headless-inspect-power",
                                classes="headless-box-body",
                                markup=True,
                            )

    # ========================================================
    # NAVIGATION / PAGE SWITCHING
    # ========================================================

    def focus_entry(self) -> bool:
        return self.focus_target(
            "headless-tab-configure"
        )

    def navigation_target(
        self,
        focused,
        direction: str,
    ) -> str | None:
        focused_id = getattr(
            focused,
            "id",
            None,
        )

        if (
            focused_id
            == "headless-tab-configure"
            and direction == "down"
        ):
            if self._page == "configure":
                return "headless-desktop-user"

            return "headless-inspect-verification"

        if (
            focused_id
            == "headless-tab-inspect"
            and direction == "down"
        ):
            if self._page == "inspect":
                return "headless-inspect-verification"

            return "headless-desktop-user"

        return super().navigation_target(
            focused,
            direction,
        )

    def action_show_configure(self) -> None:
        self._show_page(
            "configure"
        )

    def action_show_inspect(self) -> None:
        self._show_page(
            "inspect"
        )

    def _show_page(
        self,
        page: str,
    ) -> None:
        switcher = self.query_one(
            "#headless-page-switcher",
            ContentSwitcher,
        )

        configure = self.query_one(
            "#headless-tab-configure",
            Button,
        )

        inspect = self.query_one(
            "#headless-tab-inspect",
            Button,
        )

        if page == "inspect":
            switcher.current = (
                "headless-page-inspect"
            )

            configure.remove_class(
                "active-page-tab"
            )

            inspect.add_class(
                "active-page-tab"
            )

            self._page = "inspect"

        else:
            switcher.current = (
                "headless-page-configure"
            )

            inspect.remove_class(
                "active-page-tab"
            )

            configure.add_class(
                "active-page-tab"
            )

            self._page = "configure"

    # ========================================================
    # SNAPSHOT
    # ========================================================

    @staticmethod
    def _value(
        values: dict[str, Any],
        key: str,
        default: Any = None,
    ) -> Any:
        item = values.get(
            key
        )

        if isinstance(
            item,
            dict,
        ) and "value" in item:
            return item.get(
                "value",
                default,
            )

        if item is None:
            return default

        return item

    @classmethod
    def _actual_state_from_module(
        cls,
        module: dict[str, Any],
    ) -> ModuleActualState:
        raw_values = module.get(
            "values",
            {},
        )

        if not isinstance(
            raw_values,
            dict,
        ):
            raw_values = {}

        values = {
            key: cls._value(
                raw_values,
                key,
            )
            for key in raw_values
        }

        raw_status = str(
            module.get(
                "status",
                "unknown",
            )
        )

        try:
            status = Status(
                raw_status
            )
        except ValueError:
            status = Status.UNKNOWN

        return make_actual_state(
            "headless",
            status=status,
            summary=str(
                module.get(
                    "summary",
                    "",
                )
            ),
            values=values,
        )

    def update_snapshot(
        self,
        ping: dict[str, Any],
        snapshot: dict[str, Any],
        online: bool,
    ) -> None:
        if not online:
            self._headless_module = {}
            self._power_module = {}

            self.query_one(
                "#headless-status",
                Static,
            ).update(
                "Status: [red]OFFLINE[/red]"
            )

            self.query_one(
                "#headless-current-content",
                Static,
            ).update(
                "[red]Backend unavailable.[/red]"
            )

            self.query_one(
                "#headless-inspect-verification",
                Static,
            ).update(
                "[red]Backend unavailable.[/red]"
            )

            self.query_one(
                "#headless-inspect-power",
                Static,
            ).update(
                "[red]Backend unavailable.[/red]"
            )

            self.query_one(
                "#headless-verify",
                Button,
            ).disabled = True

            return

        modules = snapshot.get(
            "modules",
            {},
        )

        if not isinstance(
            modules,
            dict,
        ):
            modules = {}

        headless = modules.get(
            "headless",
            {},
        )

        power = modules.get(
            "power",
            {},
        )

        if not isinstance(
            headless,
            dict,
        ):
            headless = {}

        if not isinstance(
            power,
            dict,
        ):
            power = {}

        self._headless_module = headless
        self._power_module = power

        status = str(
            headless.get(
                "status",
                "unknown",
            )
        ).lower()

        status_markup = {
            "pass": "[green]PASS[/green]",
            "warning": "[yellow]WARNING[/yellow]",
            "drift": "[yellow]DRIFT[/yellow]",
            "fail": "[red]FAIL[/red]",
            "error": "[red]ERROR[/red]",
        }.get(
            status,
            "[yellow]UNKNOWN[/yellow]",
        )

        self.query_one(
            "#headless-status",
            Static,
        ).update(
            f"Status: {status_markup}"
        )

        self.query_one(
            "#headless-verify",
            Button,
        ).disabled = not bool(
            headless
        )

        self._render_current_state()
        self._render_power_state()

        if not self._draft_initialized:
            self._load_live_state_into_form()
            self._draft_initialized = True
        else:
            self._adopt_detected_user()

        self._render_verification()

    def _adopt_detected_user(
        self,
    ) -> None:
        if not self._headless_module:
            return

        values = self._headless_module.get(
            "values",
            {},
        )

        if not isinstance(
            values,
            dict,
        ):
            return

        users = self._value(
            values,
            "desktop_users",
            {},
        )

        if not isinstance(
            users,
            dict,
        ) or not users:
            return

        input_widget = self.query_one(
            "#headless-desktop-user",
            Input,
        )

        current = input_widget.value.strip()

        if (
            not current
            or current not in users
        ):
            input_widget.value = sorted(
                users
            )[0]

    # ========================================================
    # RENDER
    # ========================================================

    def _render_current_state(
        self,
    ) -> None:
        target = self.query_one(
            "#headless-current-content",
            Static,
        )

        if not self._headless_module:
            target.update(
                "[yellow]No Headless state available.[/yellow]"
            )
            return

        values = self._headless_module.get(
            "values",
            {},
        )

        if not isinstance(
            values,
            dict,
        ):
            values = {}

        users = self._value(
            values,
            "desktop_users",
            {},
        )

        lines = [
            "[b]System events[/b]",
            (
                "Lid / battery ......... "
                f"{self._value(values, 'lid_switch', '—')}"
            ),
            (
                "Lid / AC .............. "
                f"{self._value(values, 'lid_switch_external_power', '—')}"
            ),
            (
                "Lid / docked .......... "
                f"{self._value(values, 'lid_switch_docked', '—')}"
            ),
            (
                "Power button .......... "
                f"{self._value(values, 'power_key', '—')}"
            ),
            (
                "Power long press ...... "
                f"{self._value(values, 'power_key_long_press', '—')}"
            ),
            (
                "Idle .................. "
                f"{self._value(values, 'idle_action', '—')}"
                " / "
                f"{self._value(values, 'idle_action_sec', '—')}s"
            ),
            "",
            "[b]Login screen (GDM)[/b]",
            (
                "AC .................... "
                f"{self._value(values, 'gdm_sleep_inactive_ac_type', '—')}"
                " / "
                f"{self._value(values, 'gdm_sleep_inactive_ac_timeout', '—')}s"
            ),
            (
                "Battery ............... "
                f"{self._value(values, 'gdm_sleep_inactive_battery_type', '—')}"
                " / "
                f"{self._value(values, 'gdm_sleep_inactive_battery_timeout', '—')}s"
            ),
        ]

        if isinstance(
            users,
            dict,
        ) and users:
            lines.append("")
            lines.append(
                "[b]Desktop sessions[/b]"
            )

            for username in sorted(
                users
            ):
                settings = users.get(
                    username,
                    {},
                )

                if not isinstance(
                    settings,
                    dict,
                ):
                    continue

                lines.append(
                    (
                        f"{username} AC ............. "
                        f"{settings.get('sleep_inactive_ac_type', '—')}"
                        " / "
                        f"{settings.get('sleep_inactive_ac_timeout', '—')}s"
                    )
                )

                lines.append(
                    (
                        f"{username} battery ....... "
                        f"{settings.get('sleep_inactive_battery_type', '—')}"
                        " / "
                        f"{settings.get('sleep_inactive_battery_timeout', '—')}s"
                    )
                )

        target.update(
            "\n".join(
                lines
            )
        )

    def _render_verification(
        self,
    ) -> None:
        target = self.query_one(
            "#headless-inspect-verification",
            Static,
        )

        if not self._headless_module:
            target.update(
                "[yellow]No Headless state available.[/yellow]"
            )
            return

        try:
            settings = (
                self._build_settings_from_form()
            )

            actual = (
                self._actual_state_from_module(
                    self._headless_module
                )
            )

            report = verify(
                actual,
                settings,
            )

        except (
            ValueError,
            TypeError,
        ) as exc:
            target.update(
                (
                    "[red]Invalid desired profile[/red]\n\n"
                    f"{exc}"
                )
            )
            return

        text = Text()

        if report.passed:
            text.append(
                "PASS",
                style="bold green",
            )
            text.append(
                "  Desired headless profile matches live state."
            )

        else:
            text.append(
                "DRIFT",
                style="bold yellow",
            )
            text.append(
                "  Live state differs from the desired profile."
            )

        text.append(
            "\n\n"
        )

        for check in report.checks:
            if check.passed:
                marker = "PASS"
                style = "green"
            else:
                marker = "FAIL"
                style = "red"

            text.append(
                f"{marker:<5}",
                style=style,
            )

            text.append(
                (
                    f" {check.key}\n"
                    f"      expected: {check.expected}\n"
                    f"      actual:   {check.actual}\n"
                )
            )

        target.update(
            text
        )

    def _render_power_state(
        self,
    ) -> None:
        target = self.query_one(
            "#headless-inspect-power",
            Static,
        )

        if not self._power_module:
            target.update(
                "[yellow]No Power state available.[/yellow]"
            )
            return

        values = self._power_module.get(
            "values",
            {},
        )

        if not isinstance(
            values,
            dict,
        ):
            values = {}

        rows = (
            (
                "AC online",
                self._value(
                    values,
                    "ac_online",
                    "—",
                ),
            ),
            (
                "Battery",
                self._value(
                    values,
                    "battery_capacity",
                    "—",
                ),
            ),
            (
                "Battery status",
                self._value(
                    values,
                    "battery_status",
                    "—",
                ),
            ),
            (
                "Power profile",
                self._value(
                    values,
                    "power_profile",
                    "—",
                ),
            ),
            (
                "Memory sleep",
                self._value(
                    values,
                    "active_mem_sleep",
                    "—",
                ),
            ),
            (
                "Deep sleep",
                self._value(
                    values,
                    "deep_sleep_available",
                    "—",
                ),
            ),
            (
                "Suspend",
                self._value(
                    values,
                    "can_suspend",
                    "—",
                ),
            ),
            (
                "Hibernate",
                self._value(
                    values,
                    "can_hibernate",
                    "—",
                ),
            ),
        )

        lines: list[str] = []

        for label, value in rows:
            if label == "Battery" and isinstance(
                value,
                (int, float),
            ):
                displayed = f"{value}%"
            elif isinstance(
                value,
                bool,
            ):
                displayed = (
                    "yes"
                    if value
                    else "no"
                )
            else:
                displayed = str(
                    value
                )

            lines.append(
                f"{label:<20} {displayed}"
            )

        target.update(
            "\n".join(
                lines
            )
        )

    # ========================================================
    # FORM / PREVIEW
    # ========================================================

    def _integer(
        self,
        selector: str,
        label: str,
    ) -> int:
        raw = self.query_one(
            selector,
            Input,
        ).value.strip()

        if not raw:
            raise ValueError(
                f"{label} is required."
            )

        try:
            return int(
                raw
            )
        except ValueError as exc:
            raise ValueError(
                f"{label} must be an integer."
            ) from exc

    def _select_value(
        self,
        selector: str,
        label: str,
    ) -> str:
        value = self.query_one(
            selector,
            SpaceSelect,
        ).value

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                f"{label} is required."
            )

        return value

    def _set_select(
        self,
        selector: str,
        value: object,
        *,
        allowed: frozenset[str],
        fallback: str,
    ) -> None:
        selected = (
            value
            if isinstance(
                value,
                str,
            )
            and value in allowed
            else fallback
        )

        self.query_one(
            selector,
            SpaceSelect,
        ).value = selected

    def _build_settings_from_form(
        self,
    ) -> HeadlessSettings:
        desktop_user = self.query_one(
            "#headless-desktop-user",
            Input,
        ).value.strip()

        settings = HeadlessSettings(
            desktop_user=desktop_user,

            handle_lid_switch=self._select_value(
                "#headless-lid-battery",
                "Lid battery action",
            ),
            handle_lid_switch_external_power=(
                self._select_value(
                    "#headless-lid-ac",
                    "Lid AC action",
                )
            ),
            handle_lid_switch_docked=self._select_value(
                "#headless-lid-docked",
                "Lid docked action",
            ),
            handle_power_key=self._select_value(
                "#headless-power-short",
                "Power button action",
            ),
            handle_power_key_long_press=(
                self._select_value(
                    "#headless-power-long",
                    "Power long-press action",
                )
            ),
            idle_action=self._select_value(
                "#headless-idle-action",
                "Idle action",
            ),
            idle_action_sec=self._integer(
                "#headless-idle-timeout",
                "Idle delay",
            ),

            user_ac_action=self._select_value(
                "#headless-user-ac-action",
                "Desktop AC action",
            ),
            user_ac_timeout=self._integer(
                "#headless-user-ac-timeout",
                "Desktop AC timeout",
            ),
            user_battery_action=self._select_value(
                "#headless-user-battery-action",
                "Desktop battery action",
            ),
            user_battery_timeout=self._integer(
                "#headless-user-battery-timeout",
                "Desktop battery timeout",
            ),

            gdm_ac_action=self._select_value(
                "#headless-gdm-ac-action",
                "GDM AC action",
            ),
            gdm_ac_timeout=self._integer(
                "#headless-gdm-ac-timeout",
                "GDM AC timeout",
            ),
            gdm_battery_action=self._select_value(
                "#headless-gdm-battery-action",
                "GDM battery action",
            ),
            gdm_battery_timeout=self._integer(
                "#headless-gdm-battery-timeout",
                "GDM battery timeout",
            ),
        )

        settings.validate()

        return settings

    def _render_preview(
        self,
    ) -> bool:
        target = self.query_one(
            "#headless-preview-content",
            Static,
        )

        try:
            settings = (
                self._build_settings_from_form()
            )

            rendered = render_logind_config(
                settings
            )

        except (
            ValueError,
            TypeError,
        ) as exc:
            target.update(
                (
                    "[red]Invalid configuration[/red]\n\n"
                    f"{exc}"
                )
            )
            return False

        text = Text()

        text.append(
            LOGIND_DROP_IN,
            style="bold cyan",
        )

        text.append(
            "\n\n"
        )

        text.append(
            rendered
        )

        text.append(
            "\nDesktop session\n",
            style="bold cyan",
        )

        text.append(
            (
                f"  User: {settings.desktop_user}\n"
                f"  AC: {settings.user_ac_action}"
                f" / {settings.user_ac_timeout}s\n"
                f"  Battery: {settings.user_battery_action}"
                f" / {settings.user_battery_timeout}s\n"
            )
        )

        text.append(
            "\nLogin screen (GDM)\n",
            style="bold cyan",
        )

        text.append(
            (
                f"  AC: {settings.gdm_ac_action}"
                f" / {settings.gdm_ac_timeout}s\n"
                f"  Battery: {settings.gdm_battery_action}"
                f" / {settings.gdm_battery_timeout}s"
            )
        )

        target.update(
            text
        )

        return True

    def _load_headless_preset(
        self,
    ) -> None:
        self._set_select(
            "#headless-lid-battery",
            "ignore",
            allowed=SYSTEM_EVENT_VALUES,
            fallback="ignore",
        )
        self._set_select(
            "#headless-lid-ac",
            "ignore",
            allowed=SYSTEM_EVENT_VALUES,
            fallback="ignore",
        )
        self._set_select(
            "#headless-lid-docked",
            "ignore",
            allowed=SYSTEM_EVENT_VALUES,
            fallback="ignore",
        )
        self._set_select(
            "#headless-power-short",
            "poweroff",
            allowed=SYSTEM_EVENT_VALUES,
            fallback="poweroff",
        )
        self._set_select(
            "#headless-power-long",
            "ignore",
            allowed=SYSTEM_EVENT_VALUES,
            fallback="ignore",
        )
        self._set_select(
            "#headless-idle-action",
            "ignore",
            allowed=IDLE_ACTION_VALUES,
            fallback="ignore",
        )

        self.query_one(
            "#headless-idle-timeout",
            Input,
        ).value = "1800"

        self._set_select(
            "#headless-user-ac-action",
            "nothing",
            allowed=DESKTOP_POWER_VALUES,
            fallback="nothing",
        )
        self.query_one(
            "#headless-user-ac-timeout",
            Input,
        ).value = "900"

        self._set_select(
            "#headless-user-battery-action",
            "nothing",
            allowed=DESKTOP_POWER_VALUES,
            fallback="nothing",
        )
        self.query_one(
            "#headless-user-battery-timeout",
            Input,
        ).value = "900"

        self._set_select(
            "#headless-gdm-ac-action",
            "nothing",
            allowed=DESKTOP_POWER_VALUES,
            fallback="nothing",
        )
        self.query_one(
            "#headless-gdm-ac-timeout",
            Input,
        ).value = "0"

        self._set_select(
            "#headless-gdm-battery-action",
            "nothing",
            allowed=DESKTOP_POWER_VALUES,
            fallback="nothing",
        )
        self.query_one(
            "#headless-gdm-battery-timeout",
            Input,
        ).value = "0"

        self.query_one(
            "#headless-apply",
            Button,
        ).disabled = True

        self.query_one(
            "#headless-preview-content",
            Static,
        ).update(
            (
                "[dim]"
                "Headless preset loaded into the draft.\n\n"
                "Nothing has been applied yet. "
                "Press Preview to review it."
                "[/dim]"
            )
        )

        self._render_verification()

    def _load_live_state_into_form(
        self,
    ) -> None:
        if not self._headless_module:
            self._load_headless_preset()
            return

        values = self._headless_module.get(
            "values",
            {},
        )

        if not isinstance(
            values,
            dict,
        ):
            self._load_headless_preset()
            return

        users = self._value(
            values,
            "desktop_users",
            {},
        )

        username = self.query_one(
            "#headless-desktop-user",
            Input,
        ).value.strip()

        if isinstance(
            users,
            dict,
        ) and users:
            if username not in users:
                username = sorted(
                    users
                )[0]

            self.query_one(
                "#headless-desktop-user",
                Input,
            ).value = username

        self._set_select(
            "#headless-lid-battery",
            self._value(
                values,
                "lid_switch",
                "ignore",
            ),
            allowed=SYSTEM_EVENT_VALUES,
            fallback="ignore",
        )

        self._set_select(
            "#headless-lid-ac",
            self._value(
                values,
                "lid_switch_external_power",
                "ignore",
            ),
            allowed=SYSTEM_EVENT_VALUES,
            fallback="ignore",
        )

        self._set_select(
            "#headless-lid-docked",
            self._value(
                values,
                "lid_switch_docked",
                "ignore",
            ),
            allowed=SYSTEM_EVENT_VALUES,
            fallback="ignore",
        )

        self._set_select(
            "#headless-power-short",
            self._value(
                values,
                "power_key",
                "poweroff",
            ),
            allowed=SYSTEM_EVENT_VALUES,
            fallback="poweroff",
        )

        self._set_select(
            "#headless-power-long",
            self._value(
                values,
                "power_key_long_press",
                "ignore",
            ),
            allowed=SYSTEM_EVENT_VALUES,
            fallback="ignore",
        )

        self._set_select(
            "#headless-idle-action",
            self._value(
                values,
                "idle_action",
                "ignore",
            ),
            allowed=IDLE_ACTION_VALUES,
            fallback="ignore",
        )

        self.query_one(
            "#headless-idle-timeout",
            Input,
        ).value = str(
            self._value(
                values,
                "idle_action_sec",
                1800,
            )
        )

        selected_user = {}

        if isinstance(
            users,
            dict,
        ):
            candidate = users.get(
                username,
                {},
            )

            if isinstance(
                candidate,
                dict,
            ):
                selected_user = candidate

        self._set_select(
            "#headless-user-ac-action",
            selected_user.get(
                "sleep_inactive_ac_type",
                "nothing",
            ),
            allowed=DESKTOP_POWER_VALUES,
            fallback="nothing",
        )

        self.query_one(
            "#headless-user-ac-timeout",
            Input,
        ).value = str(
            selected_user.get(
                "sleep_inactive_ac_timeout",
                900,
            )
        )

        self._set_select(
            "#headless-user-battery-action",
            selected_user.get(
                "sleep_inactive_battery_type",
                "nothing",
            ),
            allowed=DESKTOP_POWER_VALUES,
            fallback="nothing",
        )

        self.query_one(
            "#headless-user-battery-timeout",
            Input,
        ).value = str(
            selected_user.get(
                "sleep_inactive_battery_timeout",
                900,
            )
        )

        self._set_select(
            "#headless-gdm-ac-action",
            self._value(
                values,
                "gdm_sleep_inactive_ac_type",
                "nothing",
            ),
            allowed=DESKTOP_POWER_VALUES,
            fallback="nothing",
        )

        self.query_one(
            "#headless-gdm-ac-timeout",
            Input,
        ).value = str(
            self._value(
                values,
                "gdm_sleep_inactive_ac_timeout",
                0,
            )
        )

        self._set_select(
            "#headless-gdm-battery-action",
            self._value(
                values,
                "gdm_sleep_inactive_battery_type",
                "nothing",
            ),
            allowed=DESKTOP_POWER_VALUES,
            fallback="nothing",
        )

        self.query_one(
            "#headless-gdm-battery-timeout",
            Input,
        ).value = str(
            self._value(
                values,
                "gdm_sleep_inactive_battery_timeout",
                0,
            )
        )

        self.query_one(
            "#headless-apply",
            Button,
        ).disabled = True

    def _reset_draft(
        self,
    ) -> None:
        self._load_live_state_into_form()

        self.query_one(
            "#headless-preview-content",
            Static,
        ).update(
            (
                "[dim]"
                "Draft reset to the current live state.\n\n"
                "Press Preview to review the configuration."
                "[/dim]"
            )
        )

        self._render_verification()

    # ========================================================
    # BUTTONS
    # ========================================================

    def on_button_pressed(
        self,
        event: Button.Pressed,
    ) -> None:
        button_id = (
            event.button.id
            or ""
        )

        if button_id == "headless-tab-configure":
            self._show_page(
                "configure"
            )
            return

        if button_id == "headless-tab-inspect":
            self._show_page(
                "inspect"
            )
            return

        if button_id == "headless-preset":
            self._load_headless_preset()

            self.notify(
                "Headless preset loaded into the draft.",
                timeout=3,
            )
            return

        if button_id == "headless-action-preview":
            valid = self._render_preview()

            self.query_one(
                "#headless-apply",
                Button,
            ).disabled = not valid

            self._render_verification()
            return

        if button_id == "headless-apply":
            self._request_apply()
            return

        if button_id == "headless-verify":
            self._render_verification()
            self._render_power_state()

            self._show_page(
                "inspect"
            )

            self.notify(
                "Showing live Headless verification.",
                timeout=3,
            )

            return

        if button_id == "headless-reset":
            self._reset_draft()
            return

    # ========================================================
    # APPLY
    # ========================================================

    def _request_apply(
        self,
    ) -> None:
        if not self._render_preview():
            self.query_one(
                "#headless-apply",
                Button,
            ).disabled = True

            return

        try:
            settings = (
                self._build_settings_from_form()
            )

            actual = (
                self._actual_state_from_module(
                    self._headless_module
                )
                if self._headless_module
                else None
            )

            plan = build_headless_plan(
                actual=actual,
                settings=settings,
            )

            transaction = (
                build_apply_transaction(
                    settings
                )
            )

        except (
            ValueError,
            TypeError,
        ) as exc:
            self.notify(
                (
                    "Invalid Headless configuration: "
                    f"{exc}"
                ),
                severity="error",
                timeout=5,
            )

            return

        self._pending_apply = (
            transaction
        )

        self.app.push_screen(
            PlanDialog(
                plan
            ),
            self._on_plan_reviewed,
        )

    def _on_plan_reviewed(
        self,
        confirmed: bool,
    ) -> None:
        if not confirmed:
            self._pending_apply = None
            return

        self.app.push_screen(
            FinalConfirmDialog(
                title=(
                    "Apply Headless configuration"
                ),
                message=(
                    "HomeLabCTL will apply the selected "
                    "systemd-logind, desktop-session, and GDM "
                    "power policy.\n\n"
                    "Review any action that can suspend, "
                    "hibernate, reboot, or power off the machine."
                ),
            ),
            self._on_final_confirmed,
        )

    def _on_final_confirmed(
        self,
        confirmed: bool,
    ) -> None:
        if not confirmed:
            self._pending_apply = None
            return

        transaction = (
            self._pending_apply
        )

        self._pending_apply = None

        if transaction is None:
            return

        self.query_one(
            "#headless-apply",
            Button,
        ).disabled = True

        try:
            with self.app.suspend():
                return_code = (
                    run_privileged_transaction(
                        transaction
                    )
                )

        except Exception as exc:
            self.notify(
                (
                    "Headless Apply failed: "
                    f"{exc}"
                ),
                severity="error",
                timeout=6,
            )

            return

        if return_code != 0:
            self.notify(
                (
                    "Headless Apply failed. "
                    "Review the current system state."
                ),
                severity="error",
                timeout=6,
            )

            return

        self.notify(
            (
                "Headless configuration applied and "
                "logind reloaded. Refreshing live state..."
            ),
            timeout=5,
        )

        refresh = getattr(
            self.screen,
            "refresh_backend",
            None,
        )

        if callable(
            refresh
        ):
            refresh()



# ============================================================
# LEGACY STANDALONE SCREEN COMPATIBILITY
# ============================================================

from homelabctl.tui.screens.base import ModuleScreen


class HeadlessScreen(ModuleScreen):
    """Legacy standalone Headless inspection screen."""

    MODULE = "headless"
    SCREEN_TITLE = "Headless / Sleep Policy"
