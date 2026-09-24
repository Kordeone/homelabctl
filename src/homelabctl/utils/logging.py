"""Logging configuration."""

from __future__ import annotations

import logging
from logging import Logger


LOGGER_NAME = "homelabctl"


def configure_logging(
    *,
    level: int = logging.INFO,
) -> None:
    logging.basicConfig(
        level=level,
        format=(
            "%(asctime)s "
            "%(levelname)s "
            "%(name)s: "
            "%(message)s"
        ),
    )


def get_logger(name: str | None = None) -> Logger:
    if name:
        return logging.getLogger(
            f"{LOGGER_NAME}.{name}"
        )

    return logging.getLogger(LOGGER_NAME)
