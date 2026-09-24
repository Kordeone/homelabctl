"""Application configuration schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class BackendConfig:
    socket_path: Path = Path("/run/homelabd/homelabd.sock")
    connect_timeout_seconds: float = 2.0
    request_timeout_seconds: float = 5.0


@dataclass(slots=True)
class AuditConfig:
    enabled: bool = True
    path: Path = Path.home() / ".local/state/homelabctl/audit.jsonl"


@dataclass(slots=True)
class UIConfig:
    refresh_interval_seconds: float = 2.0


@dataclass(slots=True)
class AppConfig:
    backend: BackendConfig = field(default_factory=BackendConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    ui: UIConfig = field(default_factory=UIConfig)
