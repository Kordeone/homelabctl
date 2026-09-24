from homelabctl.features.headless.plan import (
    render_logind_config,
)
from homelabctl.features.headless.schema import (
    HeadlessSettings,
)


def test_headless_logind_config():
    output = render_logind_config(
        HeadlessSettings(desktop_user="operator")
    )

    assert "HandleLidSwitch=ignore" in output
    assert (
        "HandleLidSwitchExternalPower=ignore"
        in output
    )
    assert "HandleLidSwitchDocked=ignore" in output
    assert "IdleAction=ignore" in output
