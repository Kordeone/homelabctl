"""Local protocol shared by homelabd and homelabctl."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from homelabctl.core.errors import BackendError
from homelabctl.utils.version import PROTOCOL_VERSION


@dataclass(slots=True)
class Request:
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    protocol_version: int = PROTOCOL_VERSION


@dataclass(slots=True)
class Response:
    ok: bool
    data: Any = None
    error: str | None = None
    protocol_version: int = PROTOCOL_VERSION


def encode_message(value: Request | Response) -> bytes:
    if isinstance(value, Request):
        data = {
            "type": "request",
            "protocol_version": value.protocol_version,
            "action": value.action,
            "payload": value.payload,
        }
    else:
        data = {
            "type": "response",
            "protocol_version": value.protocol_version,
            "ok": value.ok,
            "data": value.data,
            "error": value.error,
        }

    return (
        json.dumps(
            data,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def decode_request(raw: bytes) -> Request:
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BackendError("Invalid backend request.") from exc

    if not isinstance(data, dict):
        raise BackendError("Request must be a JSON object.")

    if data.get("type") != "request":
        raise BackendError("Expected request message.")

    version = data.get("protocol_version")

    if version != PROTOCOL_VERSION:
        raise BackendError(
            f"Protocol mismatch: received {version}, "
            f"expected {PROTOCOL_VERSION}."
        )

    action = data.get("action")

    if not isinstance(action, str) or not action:
        raise BackendError("Request action is missing.")

    payload = data.get("payload", {})

    if not isinstance(payload, dict):
        raise BackendError("Request payload must be an object.")

    return Request(
        action=action,
        payload=payload,
        protocol_version=version,
    )


def decode_response(raw: bytes) -> Response:
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BackendError("Invalid backend response.") from exc

    if not isinstance(data, dict):
        raise BackendError("Response must be a JSON object.")

    if data.get("type") != "response":
        raise BackendError("Expected response message.")

    version = data.get("protocol_version")

    if version != PROTOCOL_VERSION:
        raise BackendError(
            f"Protocol mismatch: received {version}, "
            f"expected {PROTOCOL_VERSION}."
        )

    return Response(
        ok=bool(data.get("ok")),
        data=data.get("data"),
        error=data.get("error"),
        protocol_version=version,
    )
