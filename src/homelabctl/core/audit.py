"""Simple JSON-lines audit support.

Audit records describe what HomeLabCTL attempted or observed. This is
application state, not system configuration.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homelabctl.core.models import AuditEvent, model_to_dict


def new_audit_event(
    *,
    category: str,
    action: str,
    result: str,
    message: str = "",
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    return AuditEvent(
        timestamp=datetime.now(UTC).isoformat(),
        category=category,
        action=action,
        result=result,
        message=message,
        metadata=dict(metadata or {}),
    )


class AuditTrail:
    """Append-only JSON-lines audit writer."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, event: AuditEvent) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        serialized = json.dumps(
            model_to_dict(event),
            ensure_ascii=False,
            sort_keys=True,
        )

        with self.path.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(serialized)
            handle.write("\n")
