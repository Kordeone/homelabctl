"""TOML configuration loading."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from homelabctl.config.defaults import (
    DEFAULT_SYSTEM_CONFIG_PATH,
    DEFAULT_USER_CONFIG_PATH,
    default_config,
)
from homelabctl.config.schema import AppConfig
from homelabctl.core.errors import ValidationError


def _load_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except FileNotFoundError:
        return {}
    except PermissionError as exc:
        raise ValidationError(
            f"Cannot read configuration file: {path}"
        ) from exc
    except tomllib.TOMLDecodeError as exc:
        raise ValidationError(
            f"Invalid TOML configuration: {path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ValidationError(
            f"Configuration root must be a table: {path}"
        )

    return data


def _merge(
    base: dict[str, Any],
    override: dict[str, Any],
) -> dict[str, Any]:
    result = dict(base)

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _merge(
                result[key],
                value,
            )
        else:
            result[key] = value

    return result


def _defaults_as_dict() -> dict[str, Any]:
    config = default_config()

    return {
        "backend": {
            "socket_path": str(
                config.backend.socket_path
            ),
            "connect_timeout_seconds":
                config.backend.connect_timeout_seconds,
            "request_timeout_seconds":
                config.backend.request_timeout_seconds,
        },
        "audit": {
            "enabled": config.audit.enabled,
            "path": str(config.audit.path),
        },
        "ui": {
            "refresh_interval_seconds":
                config.ui.refresh_interval_seconds,
        },
    }


def _positive_float(
    value: Any,
    *,
    name: str,
) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            f"{name} must be a number."
        ) from exc

    if result <= 0:
        raise ValidationError(
            f"{name} must be greater than zero."
        )

    return result


def _build_config(
    data: dict[str, Any],
) -> AppConfig:
    config = default_config()

    backend = data.get("backend", {})
    audit = data.get("audit", {})
    ui = data.get("ui", {})

    if not isinstance(backend, dict):
        raise ValidationError(
            "[backend] must be a TOML table."
        )

    if not isinstance(audit, dict):
        raise ValidationError(
            "[audit] must be a TOML table."
        )

    if not isinstance(ui, dict):
        raise ValidationError(
            "[ui] must be a TOML table."
        )

    if "socket_path" in backend:
        config.backend.socket_path = Path(
            str(backend["socket_path"])
        )

    if "connect_timeout_seconds" in backend:
        config.backend.connect_timeout_seconds = (
            _positive_float(
                backend["connect_timeout_seconds"],
                name="backend.connect_timeout_seconds",
            )
        )

    if "request_timeout_seconds" in backend:
        config.backend.request_timeout_seconds = (
            _positive_float(
                backend["request_timeout_seconds"],
                name="backend.request_timeout_seconds",
            )
        )

    if "enabled" in audit:
        if not isinstance(audit["enabled"], bool):
            raise ValidationError(
                "audit.enabled must be true or false."
            )

        config.audit.enabled = audit["enabled"]

    if "path" in audit:
        config.audit.path = Path(
            str(audit["path"])
        ).expanduser()

    if "refresh_interval_seconds" in ui:
        config.ui.refresh_interval_seconds = (
            _positive_float(
                ui["refresh_interval_seconds"],
                name="ui.refresh_interval_seconds",
            )
        )

    return config


def load_config(
    *,
    system_path: Path = DEFAULT_SYSTEM_CONFIG_PATH,
    user_path: Path = DEFAULT_USER_CONFIG_PATH,
) -> AppConfig:
    """Load defaults, then system config, then user config."""

    merged = _defaults_as_dict()

    system_data = _load_toml(system_path)
    merged = _merge(
        merged,
        system_data,
    )

    user_data = _load_toml(user_path)
    merged = _merge(
        merged,
        user_data,
    )

    return _build_config(merged)
