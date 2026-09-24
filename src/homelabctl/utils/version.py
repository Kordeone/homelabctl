"""Version helpers."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


PACKAGE_NAME = "homelabctl"

PROTOCOL_VERSION = 1


def package_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "0.1.0"


def protocol_version() -> int:
    return PROTOCOL_VERSION
