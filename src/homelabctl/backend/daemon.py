"""homelabd read-only background service."""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
from collections.abc import Sequence
from pathlib import Path

from homelabctl.backend.collectors import (
    default_collectors,
)
from homelabctl.backend.scheduler import (
    CollectorScheduler,
)
from homelabctl.backend.server import BackendServer
from homelabctl.backend.state_cache import StateCache
from homelabctl.utils.logging import configure_logging


LOGGER = logging.getLogger("homelabctl.backend.daemon")


async def run_daemon(
    *,
    socket_path: Path,
    interval_seconds: float,
) -> None:
    cache = StateCache()

    scheduler = CollectorScheduler(
        cache=cache,
        collectors=default_collectors(),
        interval_seconds=interval_seconds,
    )

    server = BackendServer(
        socket_path=socket_path,
        cache=cache,
    )

    await scheduler.collect_once()
    await server.start()

    scheduler_task = asyncio.create_task(
        scheduler.run(),
        name="collector-scheduler",
    )

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def request_stop() -> None:
        stop_event.set()

    for sig in (
        signal.SIGTERM,
        signal.SIGINT,
    ):
        try:
            loop.add_signal_handler(
                sig,
                request_stop,
            )
        except NotImplementedError:
            pass

    LOGGER.info("homelabd started in read-only mode.")

    await stop_event.wait()

    LOGGER.info("homelabd stopping.")

    scheduler.stop()
    await server.stop()

    await scheduler_task


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="homelabd",
        description=(
            "Read-only background system-state service "
            "for HomeLabCTL."
        ),
    )

    parser.add_argument(
        "--socket",
        type=Path,
        default=Path(
            "/run/homelabd/homelabd.sock"
        ),
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=10.0,
        help="Collector refresh interval in seconds.",
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = build_parser().parse_args(argv)

    if args.interval <= 0:
        raise SystemExit(
            "--interval must be greater than zero."
        )

    configure_logging()

    try:
        asyncio.run(
            run_daemon(
                socket_path=args.socket,
                interval_seconds=args.interval,
            )
        )
    except KeyboardInterrupt:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
