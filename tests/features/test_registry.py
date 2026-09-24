from homelabctl.features.registry import (
    FEATURES,
)


def test_features_are_optional_by_default():
    assert FEATURES

    for feature in FEATURES.values():
        assert (
            feature.default_selected
            is False
        )


def test_runtime_services_are_explicit():
    assert (
        FEATURES[
            "power_profile"
        ].installs_runtime_service
        is True
    )

    assert (
        FEATURES[
            "power_guardian"
        ].installs_runtime_service
        is True
    )
