from homelabctl.core.models import (
    ModuleActualState,
    StateValue,
)
from homelabctl.features.encryption.capabilities import (
    detect_capabilities,
)


def test_encryption_capabilities():
    actual = ModuleActualState(
        module="encryption",
        collected_at="test",
        values={
            "luks_present": StateValue(
                key="luks_present",
                value=True,
            ),
            "luks_device_count": StateValue(
                key="luks_device_count",
                value=1,
            ),
            "cryptsetup_available": StateValue(
                key="cryptsetup_available",
                value=True,
            ),
            "clevis_available": StateValue(
                key="clevis_available",
                value=True,
            ),
        },
    )

    result = detect_capabilities(
        actual
    )

    assert result.luks_present is True
    assert result.luks_device_count == 1
    assert result.can_manage_luks is True
    assert result.can_use_clevis is True
