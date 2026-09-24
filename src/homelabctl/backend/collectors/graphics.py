"""Graphics and kernel-module state collector."""

from __future__ import annotations

from pathlib import Path

from homelabctl.backend.collectors import CollectorResult
from homelabctl.core.actual_state import make_actual_state
from homelabctl.core.models import Status
from homelabctl.system.files import read_text


NOUVEAU_CONFIG = Path(
    "/etc/modprobe.d/disable-nouveau.conf"
)


class GraphicsCollector:
    name = "graphics"

    def collect(self) -> CollectorResult:
        modules = self._loaded_modules()

        nouveau_loaded = "nouveau" in modules
        i915_loaded = "i915" in modules
        nouveau_blacklisted = (
            self._nouveau_blacklisted()
        )

        state = make_actual_state(
            "graphics",
            status=(
                Status.PASS
                if (
                    not nouveau_loaded
                    and nouveau_blacklisted
                )
                else Status.WARNING
            ),
            summary=(
                "Graphics driver and Nouveau "
                "blacklist state collected."
            ),
            values={
                "nouveau_loaded": nouveau_loaded,
                "nouveau_blacklisted":
                    nouveau_blacklisted,
                "i915_loaded": i915_loaded,
            },
        )

        return CollectorResult(
            modules=[state]
        )

    def _loaded_modules(
        self,
    ) -> set[str]:
        content = read_text(
            "/proc/modules",
            default="",
        ) or ""

        result: set[str] = set()

        for line in content.splitlines():
            fields = line.split()

            if fields:
                result.add(fields[0])

        return result

    def _nouveau_blacklisted(
        self,
    ) -> bool:
        content = read_text(
            NOUVEAU_CONFIG,
            default="",
        ) or ""

        lines = {
            line.strip()
            for line in content.splitlines()
            if line.strip()
            and not line.strip().startswith("#")
        }

        return (
            "blacklist nouveau" in lines
            and "options nouveau modeset=0"
            in lines
        )
