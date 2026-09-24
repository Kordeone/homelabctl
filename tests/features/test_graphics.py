from homelabctl.core.models import (
    ModuleActualState,
    StateValue,
    Status,
)
from homelabctl.features.graphics.inspect import (
    assess,
)


def test_graphics_assessment_pass():
    actual = ModuleActualState(
        module="graphics",
        collected_at="test",
        values={
            "nouveau_loaded": StateValue(
                key="nouveau_loaded",
                value=False,
            ),
            "nouveau_blacklisted": StateValue(
                key="nouveau_blacklisted",
                value=True,
            ),
            "i915_loaded": StateValue(
                key="i915_loaded",
                value=True,
            ),
        },
    )

    result = assess(actual)

    assert result.status == Status.PASS
    assert result.nouveau_loaded is False
    assert result.i915_loaded is True
