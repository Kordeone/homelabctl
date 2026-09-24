from pathlib import Path

from homelabctl.config.managed import (
    ManagedState,
    load_managed_state,
    save_managed_state,
    set_feature,
)


def test_managed_state_round_trip(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "managed.json"
    )

    state = ManagedState()

    set_feature(
        state,
        "power_profile",
        enabled=True,
        settings={
            "ac_profile": "balanced",
            "battery_profile": "power-saver",
        },
    )

    save_managed_state(
        state,
        path,
    )

    loaded = load_managed_state(
        path
    )

    feature = loaded.features[
        "power_profile"
    ]

    assert feature.enabled is True

    assert (
        feature.settings[
            "ac_profile"
        ]
        == "balanced"
    )
