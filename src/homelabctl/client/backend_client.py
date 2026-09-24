"""Client for the local read-only homelabd Unix socket API."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from homelabctl.backend.protocol import (
    Request,
    decode_response,
    encode_message,
)
from homelabctl.core.errors import BackendError
from homelabctl.utils.paths import backend_socket_path


MAX_RESPONSE_BYTES = 1024 * 1024


class BackendClient:
    """Async client used by the CLI and TUI to query homelabd."""

    def __init__(
        self,
        socket_path: Path | None = None,
        *,
        connect_timeout: float = 2.0,
        request_timeout: float = 5.0,
    ) -> None:
        self.socket_path = (
            socket_path
            if socket_path is not None
            else backend_socket_path()
        )
        self.connect_timeout = connect_timeout
        self.request_timeout = request_timeout

    async def request(
        self,
        action: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        if not action:
            raise BackendError(
                "Backend action cannot be empty."
            )

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(
                    str(self.socket_path)
                ),
                timeout=self.connect_timeout,
            )
        except FileNotFoundError as exc:
            raise BackendError(
                f"homelabd socket not found: "
                f"{self.socket_path}"
            ) from exc
        except PermissionError as exc:
            raise BackendError(
                f"Permission denied accessing homelabd socket: "
                f"{self.socket_path}"
            ) from exc
        except TimeoutError as exc:
            raise BackendError(
                "Timed out connecting to homelabd."
            ) from exc
        except OSError as exc:
            raise BackendError(
                f"Unable to connect to homelabd: {exc}"
            ) from exc

        try:
            request = Request(
                action=action,
                payload=dict(payload or {}),
            )

            writer.write(
                encode_message(request)
            )

            await writer.drain()

            raw = await asyncio.wait_for(
                reader.readline(),
                timeout=self.request_timeout,
            )

            if not raw:
                raise BackendError(
                    "homelabd closed the connection "
                    "without a response."
                )

            if len(raw) > MAX_RESPONSE_BYTES:
                raise BackendError(
                    "homelabd response exceeded "
                    "the maximum allowed size."
                )

            response = decode_response(raw)

            if not response.ok:
                raise BackendError(
                    response.error
                    or "homelabd returned an unknown error."
                )

            return response.data

        except TimeoutError as exc:
            raise BackendError(
                "Timed out waiting for homelabd."
            ) from exc

        finally:
            writer.close()

            try:
                await writer.wait_closed()
            except ConnectionError:
                pass

    async def ping(self) -> dict[str, Any]:
        data = await self.request("ping")

        if not isinstance(data, dict):
            raise BackendError(
                "Invalid ping response from homelabd."
            )

        return data

    async def snapshot(self) -> dict[str, Any]:
        data = await self.request("snapshot")

        if not isinstance(data, dict):
            raise BackendError(
                "Invalid snapshot response from homelabd."
            )

        return data

    async def get_module(
        self,
        module: str,
    ) -> dict[str, Any]:
        data = await self.request(
            "module.get",
            {
                "module": module,
            },
        )

        if not isinstance(data, dict):
            raise BackendError(
                f"Invalid state returned for module "
                f"{module!r}."
            )

        return data

    async def available(self) -> bool:
        try:
            await self.ping()
        except BackendError:
            return False

        return True


def request_sync(
    action: str,
    payload: dict[str, Any] | None = None,
    *,
    socket_path: Path | None = None,
    connect_timeout: float = 2.0,
    request_timeout: float = 5.0,
) -> Any:
    """Synchronous wrapper for non-async CLI operations."""

    client = BackendClient(
        socket_path=socket_path,
        connect_timeout=connect_timeout,
        request_timeout=request_timeout,
    )

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            client.request(
                action,
                payload,
            )
        )

    raise BackendError(
        "request_sync() cannot be used from "
        "an active asyncio event loop."
    )
