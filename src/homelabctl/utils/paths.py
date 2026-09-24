"""Common HomeLabCTL filesystem paths."""

from __future__ import annotations

from pathlib import Path


def user_config_dir() -> Path:
    return Path.home() / ".config" / "homelabctl"


def user_state_dir() -> Path:
    return Path.home() / ".local" / "state" / "homelabctl"


def user_cache_dir() -> Path:
    return Path.home() / ".cache" / "homelabctl"


def system_config_dir() -> Path:
    return Path("/etc/homelabctl")


def runtime_dir() -> Path:
    return Path("/run/homelabd")


def backend_socket_path() -> Path:
    return runtime_dir() / "homelabd.sock"


def ensure_user_directories() -> None:
    user_config_dir().mkdir(
        parents=True,
        exist_ok=True,
    )

    user_state_dir().mkdir(
        parents=True,
        exist_ok=True,
    )

    user_cache_dir().mkdir(
        parents=True,
        exist_ok=True,
    )
