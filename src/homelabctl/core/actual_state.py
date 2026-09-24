"""Actual system-state snapshot containers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homelabctl.core.models import ModuleActualState, StateValue, Status


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class ActualStateStore:
    """Holds the latest observed state reported by collectors."""

    def __init__(self) -> None:
        self._modules: dict[str, ModuleActualState] = {}

    def update(self, state: ModuleActualState) -> None:
        self._modules[state.module] = state

    def get_module(self, module: str) -> ModuleActualState | None:
        return self._modules.get(module)

    def get_value(
        self,
        module: str,
        key: str,
        default: Any = None,
    ) -> Any:
        state = self.get_module(module)

        if state is None:
            return default

        return state.get(key, default)

    def modules(self) -> list[ModuleActualState]:
        return list(self._modules.values())

    def clear(self) -> None:
        self._modules.clear()


def make_actual_state(
    module: str,
    *,
    status: Status = Status.UNKNOWN,
    summary: str = "",
    values: dict[str, Any] | None = None,
    sources: dict[str, str] | None = None,
) -> ModuleActualState:
    """Convenience helper for collectors."""

    sources = sources or {}
    state_values: dict[str, StateValue] = {}

    for key, value in (values or {}).items():
        state_values[key] = StateValue(
            key=key,
            value=value,
            source=sources.get(key),
        )

    return ModuleActualState(
        module=module,
        collected_at=utc_now_iso(),
        status=status,
        summary=summary,
        values=state_values,
    )
