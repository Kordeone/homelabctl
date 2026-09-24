"""Desired-state model.

Desired state represents what the user explicitly wants HomeLabCTL-managed
configuration to look like.

It is not treated as proof of actual system configuration.
"""

from __future__ import annotations

from typing import Any

from homelabctl.core.models import DesiredSetting, ModuleDesiredState


class DesiredStateStore:
    """In-memory collection of desired state for feature modules."""

    def __init__(self) -> None:
        self._modules: dict[str, ModuleDesiredState] = {}

    def set_module(self, state: ModuleDesiredState) -> None:
        self._modules[state.module] = state

    def get_module(self, module: str) -> ModuleDesiredState | None:
        return self._modules.get(module)

    def remove_module(self, module: str) -> None:
        self._modules.pop(module, None)

    def set_value(
        self,
        module: str,
        key: str,
        value: Any,
        *,
        required: bool = True,
        description: str | None = None,
    ) -> None:
        state = self._modules.setdefault(
            module,
            ModuleDesiredState(module=module),
        )

        state.settings[key] = DesiredSetting(
            key=key,
            value=value,
            required=required,
            description=description,
        )

    def get_value(
        self,
        module: str,
        key: str,
        default: Any = None,
    ) -> Any:
        state = self.get_module(module)

        if state is None:
            return default

        setting = state.settings.get(key)

        if setting is None:
            return default

        return setting.value

    def modules(self) -> list[ModuleDesiredState]:
        return list(self._modules.values())

    def clear(self) -> None:
        self._modules.clear()
