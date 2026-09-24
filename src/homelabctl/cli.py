"""HomeLabCTL command-line entry point."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from homelabctl import __version__
from homelabctl.client import request_sync
from homelabctl.core.errors import BackendError


def run_tui() -> int:
    from homelabctl.tui.app import HomeLabApp

    HomeLabApp().run()
    return 0


def show_backend_status() -> int:
    try:
        data = request_sync("ping")
    except BackendError as exc:
        print(
            f"homelabd unavailable: {exc}"
        )
        return 1

    print(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )
    )

    return 0


def show_snapshot() -> int:
    try:
        data = request_sync("snapshot")
    except BackendError as exc:
        print(
            f"Unable to read backend snapshot: {exc}"
        )
        return 1

    print(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )
    )

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="homelabctl",
        description=(
            "Home lab inspection, configuration "
            "and management interface."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        metavar="COMMAND",
    )

    subparsers.add_parser(
        "tui",
        help="Open the interactive TUI.",
    )

    subparsers.add_parser(
        "status",
        help="Show homelabd connection status.",
    )

    subparsers.add_parser(
        "snapshot",
        help="Print the current backend snapshot.",
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        return run_tui()

    if args.command == "tui":
        return run_tui()

    if args.command == "status":
        return show_backend_status()

    if args.command == "snapshot":
        return show_snapshot()

    parser.error(
        f"Unknown command: {args.command}"
    )

    return 2
