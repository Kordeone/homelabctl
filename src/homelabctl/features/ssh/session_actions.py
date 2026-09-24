"""Privileged SSH session actions."""

from __future__ import annotations

import re

from homelabctl.apply.transaction import (
    ActionType,
    ApplyAction,
    ApplyTransaction,
    new_transaction,
)


SESSION_ID_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$"
)


def validate_session_id(
    session_id: str,
) -> str:
    value = session_id.strip()

    if not value:
        raise ValueError(
            "SSH session ID is required."
        )

    if not SESSION_ID_RE.fullmatch(
        value
    ):
        raise ValueError(
            "Invalid SSH session ID."
        )

    return value


def build_disconnect_session_transaction(
    session_id: str,
) -> ApplyTransaction:
    session_id = validate_session_id(
        session_id
    )

    return new_transaction(
        feature="ssh",
        actions=[
            ApplyAction(
                action_type=ActionType.RUN_COMMAND,
                description=(
                    "Disconnect selected SSH session."
                ),
                argv=[
                    "/usr/bin/loginctl",
                    "terminate-session",
                    session_id,
                ],
                backup=False,
            ),
        ],
    )
