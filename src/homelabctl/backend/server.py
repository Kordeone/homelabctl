"""Read-only Unix socket server used by homelabd."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from homelabctl.backend.protocol import (
    Request,
    Response,
    decode_request,
    encode_message,
)
from homelabctl.backend.state_cache import StateCache
from homelabctl.core.errors import BackendError
from homelabctl.core.models import model_to_dict
from homelabctl.utils.version import (
    package_version,
    protocol_version,
)


LOGGER = logging.getLogger("homelabctl.backend.server")

MAX_REQUEST_BYTES = 64 * 1024


class BackendServer:
    def __init__(
        self,
        *,
        socket_path: Path,
        cache: StateCache,
        socket_mode: int = 0o660,
    ) -> None:
        self.socket_path = socket_path
        self.cache = cache
        self.socket_mode = socket_mode
        self._server: asyncio.AbstractServer | None = None

    async def start(self) -> None:
        self.socket_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self.socket_path.exists():
            self.socket_path.unlink()

        self._server = await asyncio.start_unix_server(
            self._handle_client,
            path=str(self.socket_path),
        )

        os.chmod(
            self.socket_path,
            self.socket_mode,
        )

        LOGGER.info(
            "Backend listening on %s",
            self.socket_path,
        )

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        try:
            self.socket_path.unlink()
        except FileNotFoundError:
            pass

    async def serve_forever(self) -> None:
        if self._server is None:
            raise RuntimeError(
                "Backend server has not been started."
            )

        async with self._server:
            await self._server.serve_forever()

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            raw = await reader.readline()

            if not raw:
                return

            if len(raw) > MAX_REQUEST_BYTES:
                response = Response(
                    ok=False,
                    error="Request exceeds maximum size.",
                )
            else:
                try:
                    request = decode_request(raw)
                    response = self._dispatch(request)
                except BackendError as exc:
                    response = Response(
                        ok=False,
                        error=str(exc),
                    )
                except Exception:
                    LOGGER.exception(
                        "Unhandled backend request error."
                    )
                    response = Response(
                        ok=False,
                        error="Internal backend error.",
                    )

            writer.write(
                encode_message(response)
            )
            await writer.drain()

        finally:
            writer.close()

            try:
                await writer.wait_closed()
            except ConnectionError:
                pass

    def _dispatch(
        self,
        request: Request,
    ) -> Response:
        if request.action == "ping":
            return Response(
                ok=True,
                data={
                    "service": "homelabd",
                    "backend_version": package_version(),
                    "protocol_version": protocol_version(),
                    "mode": "read-only",
                },
            )

        if request.action == "snapshot":
            return Response(
                ok=True,
                data=self.cache.snapshot_dict(),
            )

        if request.action == "module.get":
            module_name = request.payload.get("module")

            if not isinstance(module_name, str):
                return Response(
                    ok=False,
                    error="module.get requires a module name.",
                )

            state = self.cache.get_module(
                module_name
            )

            if state is None:
                return Response(
                    ok=False,
                    error=(
                        f"No state is available for "
                        f"module '{module_name}'."
                    ),
                )

            return Response(
                ok=True,
                data=model_to_dict(state),
            )

        return Response(
            ok=False,
            error=(
                f"Unsupported read-only action: "
                f"{request.action}"
            ),
        )
