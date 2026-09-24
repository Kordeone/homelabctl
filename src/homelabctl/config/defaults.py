"""Default HomeLabCTL configuration."""

from __future__ import annotations

from pathlib import Path

from homelabctl.config.schema import (
    AppConfig,
    AuditConfig,
    BackendConfig,
    UIConfig,
)


DEFAULT_USER_CONFIG_PATH = (
    Path.home()
    / ".config"
    / "homelabctl"
    / "config.toml"
)

DEFAULT_SYSTEM_CONFIG_PATH = Path(
    "/etc/homelabctl/config.toml"
)


def default_config() -> AppConfig:
    return AppConfig(
        backend=BackendConfig(
            socket_path=Path(
                "/run/homelabd/homelabd.sock"
            ),
            connect_timeout_seconds=2.0,
            request_timeout_seconds=5.0,
        ),
        audit=AuditConfig(
            enabled=True,
            path=(
                Path.home()
                / ".local/state/homelabctl/audit.jsonl"
            ),
        ),
        ui=UIConfig(
            refresh_interval_seconds=2.0,
        ),
    )
