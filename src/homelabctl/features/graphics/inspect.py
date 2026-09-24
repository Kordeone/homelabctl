"""Graphics-driver state interpretation."""

from __future__ import annotations

from dataclasses import dataclass

from homelabctl.core.models import (
    ModuleActualState,
    Status,
)


@dataclass(slots=True)
class GraphicsAssessment:
    status: Status
    nouveau_loaded: bool | None
    nouveau_blacklisted: bool | None
    i915_loaded: bool | None


def assess(
    actual: ModuleActualState | None,
) -> GraphicsAssessment:
    if actual is None:
        return GraphicsAssessment(
            status=Status.UNKNOWN,
            nouveau_loaded=None,
            nouveau_blacklisted=None,
            i915_loaded=None,
        )

    nouveau_loaded = actual.get(
        "nouveau_loaded"
    )

    nouveau_blacklisted = actual.get(
        "nouveau_blacklisted"
    )

    i915_loaded = actual.get(
        "i915_loaded"
    )

    if (
        nouveau_loaded is False
        and nouveau_blacklisted is True
    ):
        status = Status.PASS
    else:
        status = Status.WARNING

    return GraphicsAssessment(
        status=status,
        nouveau_loaded=nouveau_loaded,
        nouveau_blacklisted=nouveau_blacklisted,
        i915_loaded=i915_loaded,
    )
