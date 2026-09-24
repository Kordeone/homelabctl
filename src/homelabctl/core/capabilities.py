"""Capability helpers.

Capabilities answer questions such as:

- Is TPM 2 available?
- Is Secure Boot enabled?
- Is hibernation currently possible?
- Can this network adapter operate as an access point?

Capability detection itself is performed by collectors or feature modules.
This module only provides a common container and query API.
"""

from __future__ import annotations

from collections.abc import Iterable

from homelabctl.core.models import CapabilityResult, CapabilityState


class CapabilitySet:
    """Collection of capability results indexed by stable capability key."""

    def __init__(
        self,
        capabilities: Iterable[CapabilityResult] | None = None,
    ) -> None:
        self._items: dict[str, CapabilityResult] = {}

        if capabilities:
            for capability in capabilities:
                self.add(capability)

    def add(self, capability: CapabilityResult) -> None:
        self._items[capability.key] = capability

    def get(self, key: str) -> CapabilityResult | None:
        return self._items.get(key)

    def require(self, key: str) -> CapabilityResult:
        result = self.get(key)

        if result is None:
            return CapabilityResult(
                key=key,
                name=key,
                state=CapabilityState.UNKNOWN,
                reason="Capability has not been evaluated.",
            )

        return result

    def is_available(self, key: str) -> bool:
        result = self.get(key)
        return bool(result and result.available)

    def unavailable(self) -> list[CapabilityResult]:
        return [
            item
            for item in self._items.values()
            if item.state == CapabilityState.UNAVAILABLE
        ]

    def unknown(self) -> list[CapabilityResult]:
        return [
            item
            for item in self._items.values()
            if item.state == CapabilityState.UNKNOWN
        ]

    def all(self) -> list[CapabilityResult]:
        return list(self._items.values())

    def __len__(self) -> int:
        return len(self._items)
