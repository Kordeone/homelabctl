"""In-memory state cache maintained by the read-only backend."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from homelabctl.core.models import (
    CapabilityResult,
    ModuleActualState,
    model_to_dict,
)
from homelabctl.utils.time import utc_now_iso
from homelabctl.utils.version import (
    package_version,
    protocol_version,
)


@dataclass(slots=True)
class BackendSnapshot:
    generated_at: str
    backend_version: str
    protocol_version: int
    modules: dict[str, ModuleActualState] = field(
        default_factory=dict
    )
    capabilities: dict[str, CapabilityResult] = field(
        default_factory=dict
    )


class StateCache:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._modules: dict[str, ModuleActualState] = {}
        self._capabilities: dict[str, CapabilityResult] = {}

    def update_module(
        self,
        state: ModuleActualState,
    ) -> None:
        with self._lock:
            self._modules[state.module] = state

    def update_capability(
        self,
        capability: CapabilityResult,
    ) -> None:
        with self._lock:
            self._capabilities[capability.key] = capability

    def get_module(
        self,
        module: str,
    ) -> ModuleActualState | None:
        with self._lock:
            return self._modules.get(module)

    def snapshot(self) -> BackendSnapshot:
        with self._lock:
            return BackendSnapshot(
                generated_at=utc_now_iso(),
                backend_version=package_version(),
                protocol_version=protocol_version(),
                modules=dict(self._modules),
                capabilities=dict(self._capabilities),
            )

    def snapshot_dict(self) -> dict:
        return model_to_dict(self.snapshot())
