"""Generic post-change verification helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homelabctl.core.models import (
    ModuleActualState,
    ModuleDesiredState,
    Status,
    VerificationCheck,
    VerificationReport,
)

Comparator = Callable[[Any, Any], bool]


def verify_module(
    desired: ModuleDesiredState,
    actual: ModuleActualState | None,
    *,
    comparators: dict[str, Comparator] | None = None,
) -> VerificationReport:
    comparators = comparators or {}
    checks: list[VerificationCheck] = []

    if actual is None:
        return VerificationReport(
            feature=desired.module,
            status=Status.ERROR,
            checks=[
                VerificationCheck(
                    key="actual_state",
                    expected="available",
                    actual=None,
                    passed=False,
                    message="No actual state was available for verification.",
                )
            ],
        )

    for setting in desired.settings.values():
        actual_item = actual.values.get(setting.key)

        if actual_item is None:
            checks.append(
                VerificationCheck(
                    key=setting.key,
                    expected=setting.value,
                    actual=None,
                    passed=False,
                    message="Setting was not found.",
                )
            )
            continue

        if not actual_item.readable:
            checks.append(
                VerificationCheck(
                    key=setting.key,
                    expected=setting.value,
                    actual=None,
                    passed=False,
                    message=actual_item.error or "Setting could not be read.",
                )
            )
            continue

        comparator = comparators.get(
            setting.key,
            lambda expected, observed: expected == observed,
        )

        passed = comparator(
            setting.value,
            actual_item.value,
        )

        checks.append(
            VerificationCheck(
                key=setting.key,
                expected=setting.value,
                actual=actual_item.value,
                passed=passed,
                message="Match." if passed else "Observed value does not match expected value.",
            )
        )

    if not checks:
        status = Status.NOT_CONFIGURED
    elif all(check.passed for check in checks):
        status = Status.PASS
    else:
        status = Status.FAIL

    return VerificationReport(
        feature=desired.module,
        status=status,
        checks=checks,
    )
