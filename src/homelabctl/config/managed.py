"""Persistent user-owned HomeLabCTL feature selection.

This file records user intent only.

It does not prove actual system configuration.
homelabd remains responsible for observing actual state.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1

DEFAULT_MANAGED_STATE_PATH = (
    Path.home()
    / ".config"
    / "homelabctl"
    / "managed.json"
)


@dataclass(slots=True)
class ManagedFeature:
    enabled: bool = False
    settings: dict[str, Any] = field(
        default_factory=dict
    )
    last_transaction_id: str | None = None


@dataclass(slots=True)
class ManagedState:
    schema_version: int = SCHEMA_VERSION

    features: dict[str, ManagedFeature] = field(
        default_factory=dict
    )


def load_managed_state(
    path: Path = DEFAULT_MANAGED_STATE_PATH,
) -> ManagedState:
    if not path.exists():
        return ManagedState()

    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return ManagedState()

    if not isinstance(data, dict):
        return ManagedState()

    if data.get(
        "schema_version"
    ) != SCHEMA_VERSION:
        return ManagedState()

    raw_features = data.get(
        "features",
        {},
    )

    features: dict[
        str,
        ManagedFeature,
    ] = {}

    if isinstance(
        raw_features,
        dict,
    ):
        for key, raw in raw_features.items():
            if not isinstance(
                raw,
                dict,
            ):
                continue

            settings = raw.get(
                "settings",
                {},
            )

            if not isinstance(
                settings,
                dict,
            ):
                settings = {}

            features[str(key)] = ManagedFeature(
                enabled=bool(
                    raw.get(
                        "enabled",
                        False,
                    )
                ),
                settings=settings,
                last_transaction_id=(
                    raw.get(
                        "last_transaction_id"
                    )
                ),
            )

    return ManagedState(
        features=features
    )


def save_managed_state(
    state: ManagedState,
    path: Path = DEFAULT_MANAGED_STATE_PATH,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = json.dumps(
        asdict(state),
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )

    fd, temporary_name = tempfile.mkstemp(
        prefix=".managed-",
        suffix=".json",
        dir=str(path.parent),
    )

    temporary = Path(
        temporary_name
    )

    try:
        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
        ) as handle:
            handle.write(payload)
            handle.write("\n")
            handle.flush()
            os.fsync(
                handle.fileno()
            )

        os.replace(
            temporary,
            path,
        )

    finally:
        if temporary.exists():
            temporary.unlink()


def set_feature(
    state: ManagedState,
    key: str,
    *,
    enabled: bool,
    settings: dict[str, Any] | None = None,
    transaction_id: str | None = None,
) -> None:
    feature = state.features.setdefault(
        key,
        ManagedFeature(),
    )

    feature.enabled = enabled

    if settings is not None:
        feature.settings = dict(
            settings
        )

    if transaction_id is not None:
        feature.last_transaction_id = (
            transaction_id
        )
