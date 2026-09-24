"""Read-only collector contracts and registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from homelabctl.core.models import (
    CapabilityResult,
    ModuleActualState,
)


@dataclass(slots=True)
class CollectorResult:
    modules: list[ModuleActualState] = field(
        default_factory=list
    )
    capabilities: list[CapabilityResult] = field(
        default_factory=list
    )


class Collector(Protocol):
    name: str

    def collect(self) -> CollectorResult:
        ...


def default_collectors() -> list[Collector]:
    from homelabctl.backend.collectors.encryption import (
        EncryptionCollector,
    )
    from homelabctl.backend.collectors.firewall import (
        FirewallCollector,
    )
    from homelabctl.backend.collectors.file_watch import (
        FileWatchCollector,
    )
    from homelabctl.backend.collectors.headless import (
        HeadlessCollector,
    )
    from homelabctl.backend.collectors.graphics import (
        GraphicsCollector,
    )
    from homelabctl.backend.collectors.network import (
        NetworkCollector,
    )
    from homelabctl.backend.collectors.power import (
        PowerCollector,
    )
    from homelabctl.backend.collectors.security import (
        SecurityCollector,
    )
    from homelabctl.backend.collectors.ssh import (
        SSHCollector,
    )
    from homelabctl.backend.collectors.storage import (
        StorageCollector,
    )
    from homelabctl.backend.collectors.system import (
        SystemCollector,
    )

    return [
        SystemCollector(),
        SSHCollector(),
        FirewallCollector(),
        FileWatchCollector(),
        HeadlessCollector(),
        GraphicsCollector(),
        SecurityCollector(),
        EncryptionCollector(),
        PowerCollector(),
        NetworkCollector(),
        StorageCollector(),
    ]
