"""Desired-state versus actual-state comparison."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homelabctl.core.models import (
    DriftItem,
    DriftReport,
    ModuleActualState,
    ModuleDesiredState,
    Status,
)

Comparator = Callable[[Any, Any], bool]


def default_comparator(desired: Any, actual: Any) -> bool:
    return desired == actual


def compare_module_state(
    desired: ModuleDesiredState,
    actual: ModuleActualState | None,
    *,
    comparators: dict[str, Comparator] | None = None,
) -> DriftReport:
    """Compare desired settings with the latest observed actual state."""

    comparators = comparators or {}
    items: list[DriftItem] = []

    if actual is None:
        for setting in desired.settings.values():
            items.append(
                DriftItem(
                    key=setting.key,
                    desired=setting.value,
                    actual=None,
                    matches=False,
                    reason="Actual state has not been collected.",
                )
            )

        return DriftReport(
            module=desired.module,
            status=Status.UNKNOWN,
            items=items,
        )

    for setting in desired.settings.values():
        actual_item = actual.values.get(setting.key)

        if actual_item is None:
            items.append(
                DriftItem(
                    key=setting.key,
                    desired=setting.value,
                    actual=None,
                    matches=False,
                    reason="Setting was not found in actual state.",
                )
            )
            continue

        if not actual_item.readable:
            items.append(
                DriftItem(
                    key=setting.key,
                    desired=setting.value,
                    actual=None,
                    matches=False,
                    reason=actual_item.error or "Setting could not be read.",
                )
            )
            continue

        comparator = comparators.get(
            setting.key,
            default_comparator,
        )

        matches = comparator(
            setting.value,
            actual_item.value,
        )

        items.append(
            DriftItem(
                key=setting.key,
                desired=setting.value,
                actual=actual_item.value,
                matches=matches,
                reason=None if matches else "Actual value differs from desired value.",
            )
        )

    if not items:
        status = Status.NOT_CONFIGURED
    elif any(not item.matches for item in items):
        status = Status.DRIFT
    else:
        status = Status.PASS

    return DriftReport(
        module=desired.module,
        status=status,
        items=items,
    )
