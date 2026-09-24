"""Structured privileged apply transactions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class ActionType(str, Enum):
    WRITE_FILE = "write_file"
    REMOVE_FILE = "remove_file"
    RUN_COMMAND = "run_command"
    SYSTEMCTL = "systemctl"


@dataclass(slots=True)
class ApplyAction:
    action_type: ActionType
    description: str
    target: str | None = None
    content: str | None = None
    argv: list[str] = field(default_factory=list)
    mode: int | None = None
    backup: bool = True


@dataclass(slots=True)
class ApplyTransaction:
    id: str
    feature: str
    actions: list[ApplyAction] = field(default_factory=list)


def new_transaction(
    feature: str,
    actions: list[ApplyAction],
) -> ApplyTransaction:
    return ApplyTransaction(
        id=uuid4().hex,
        feature=feature,
        actions=actions,
    )


def transaction_to_dict(
    transaction: ApplyTransaction,
) -> dict[str, Any]:
    result = asdict(transaction)

    for action in result["actions"]:
        action["action_type"] = action["action_type"].value

    return result


def transaction_from_dict(
    data: dict[str, Any],
) -> ApplyTransaction:
    if not isinstance(data, dict):
        raise ValueError("Transaction must be an object.")

    transaction_id = data.get("id")
    feature = data.get("feature")
    raw_actions = data.get("actions")

    if not isinstance(transaction_id, str) or not transaction_id:
        raise ValueError("Transaction ID is missing.")

    if not isinstance(feature, str) or not feature:
        raise ValueError("Transaction feature is missing.")

    if not isinstance(raw_actions, list):
        raise ValueError("Transaction actions must be a list.")

    actions: list[ApplyAction] = []

    for raw in raw_actions:
        if not isinstance(raw, dict):
            raise ValueError("Invalid transaction action.")

        actions.append(
            ApplyAction(
                action_type=ActionType(
                    raw["action_type"]
                ),
                description=str(
                    raw.get("description", "")
                ),
                target=raw.get("target"),
                content=raw.get("content"),
                argv=list(raw.get("argv", [])),
                mode=raw.get("mode"),
                backup=bool(
                    raw.get("backup", True)
                ),
            )
        )

    return ApplyTransaction(
        id=transaction_id,
        feature=feature,
        actions=actions,
    )
