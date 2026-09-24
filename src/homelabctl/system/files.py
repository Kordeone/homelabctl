"""Read-only filesystem helpers."""

from __future__ import annotations

from pathlib import Path


def exists(path: str | Path) -> bool:
    return Path(path).exists()


def is_readable(path: str | Path) -> bool:
    target = Path(path)

    try:
        with target.open("rb"):
            return True
    except (OSError, PermissionError):
        return False


def read_text(
    path: str | Path,
    *,
    default: str | None = None,
) -> str | None:
    try:
        return Path(path).read_text(
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, PermissionError):
        return default


def read_first_line(
    path: str | Path,
    *,
    default: str | None = None,
) -> str | None:
    content = read_text(path)

    if content is None:
        return default

    lines = content.splitlines()

    if not lines:
        return default

    return lines[0].strip()


def read_int(
    path: str | Path,
    *,
    default: int | None = None,
) -> int | None:
    value = read_first_line(path)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def list_directory(path: str | Path) -> list[Path]:
    try:
        return sorted(Path(path).iterdir())
    except (OSError, PermissionError):
        return []
