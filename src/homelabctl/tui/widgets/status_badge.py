"""Reusable status badge widget."""

from __future__ import annotations

from textual.widgets import Static


class StatusBadge(Static):
    STATUS_CLASSES = {
        "pass": "status-pass",
        "fail": "status-fail",
        "warning": "status-warning",
        "unknown": "status-unknown",
        "error": "status-error",
        "not_configured": "status-neutral",
        "unavailable": "status-neutral",
        "drift": "status-drift",
        "manual": "status-manual",
    }

    STATUS_LABELS = {
        "pass": "PASS",
        "fail": "FAIL",
        "warning": "WARNING",
        "unknown": "UNKNOWN",
        "error": "ERROR",
        "not_configured": "NOT CONFIGURED",
        "unavailable": "UNAVAILABLE",
        "drift": "DRIFT",
        "manual": "MANUAL",
    }

    def __init__(
        self,
        status: str = "unknown",
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(
            "",
            id=id,
            classes=classes,
        )

        self._status = "unknown"
        self.set_status(status)

    @property
    def status(self) -> str:
        return self._status

    def set_status(
        self,
        status: str,
    ) -> None:
        normalized = str(
            status or "unknown"
        ).lower()

        for css_class in self.STATUS_CLASSES.values():
            self.remove_class(css_class)

        css_class = self.STATUS_CLASSES.get(
            normalized,
            "status-unknown",
        )

        label = self.STATUS_LABELS.get(
            normalized,
            normalized.upper(),
        )

        self._status = normalized

        self.add_class(css_class)
        self.update(label)
