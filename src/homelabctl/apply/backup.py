"""Backup support for privileged configuration changes."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path


BACKUP_ROOT = Path(
    "/var/lib/homelabctl/backups"
)


@dataclass(slots=True)
class BackupRecord:
    original: str
    backup: str | None
    existed: bool


def transaction_backup_dir(
    transaction_id: str,
) -> Path:
    return BACKUP_ROOT / transaction_id


def backup_file(
    path: Path,
    *,
    transaction_id: str,
) -> BackupRecord:
    directory = transaction_backup_dir(
        transaction_id
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )

    if not path.exists():
        return BackupRecord(
            original=str(path),
            backup=None,
            existed=False,
        )

    safe_name = (
        str(path)
        .lstrip("/")
        .replace("/", "__")
    )

    destination = directory / safe_name

    shutil.copy2(
        path,
        destination,
    )

    return BackupRecord(
        original=str(path),
        backup=str(destination),
        existed=True,
    )


def write_manifest(
    transaction_id: str,
    records: list[BackupRecord],
) -> Path:
    directory = transaction_backup_dir(
        transaction_id
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )

    manifest = directory / "manifest.json"

    manifest.write_text(
        json.dumps(
            [asdict(record) for record in records],
            indent=2,
        ),
        encoding="utf-8",
    )

    return manifest
