"""Periodic collector scheduler for homelabd."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable

from homelabctl.backend.collectors import Collector
from homelabctl.backend.state_cache import StateCache


LOGGER = logging.getLogger("homelabctl.backend.scheduler")


class CollectorScheduler:
    def __init__(
        self,
        *,
        cache: StateCache,
        collectors: Iterable[Collector],
        interval_seconds: float = 10.0,
    ) -> None:
        self.cache = cache
        self.collectors = list(collectors)
        self.interval_seconds = interval_seconds
        self._stop_event = asyncio.Event()

    async def collect_once(self) -> None:
        for collector in self.collectors:
            try:
                result = await asyncio.to_thread(
                    collector.collect
                )
            except Exception:
                LOGGER.exception(
                    "Collector failed: %s",
                    collector.name,
                )
                continue

            for state in result.modules:
                self.cache.update_module(state)

            for capability in result.capabilities:
                self.cache.update_capability(capability)

    async def run(self) -> None:
        while not self._stop_event.is_set():
            await self.collect_once()

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.interval_seconds,
                )
            except TimeoutError:
                pass

    def stop(self) -> None:
        self._stop_event.set()
