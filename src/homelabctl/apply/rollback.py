"""Rollback previously backed-up files."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from homelabctl.apply.backup import (
    BackupRecord,
    transaction_backup_dir,
)


def load_backup_manifest(
    transaction_id: str,
) -> list[BackupRecord]:
    manifest = (
        transaction_backup_dir(transaction_id)
        / "manifest.json"
    )

    if not manifest.exists():
        return []

    data = json.loads(
        manifest.read_text(
            encoding="utf-8"
        )
    )

    return [
        BackupRecord(**item)
        for item in data
    ]


def restore_transaction_files(
    transaction_id: str,
) -> list[str]:
    restored: list[str] = []

    for record in reversed(
        load_backup_manifest(transaction_id)
    ):
        original = Path(record.original)

        if record.existed:
            if not record.backup:
                continue

            original.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copy2(
                Path(record.backup),
                original,
            )

            restored.append(
                str(original)
            )

        elif original.exists():
            original.unlink()
            restored.append(
                str(original)
            )

    return restored
