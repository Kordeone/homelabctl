from homelabctl.features.firewall.plan import (
    render_config as render_firewall,
)
from homelabctl.features.firewall.schema import (
    FirewallSettings,
)
from homelabctl.features.headless.plan import (
    render_logind_config,
)
from homelabctl.features.headless.schema import (
    HeadlessSettings,
)
from homelabctl.features.power_guardian.config import (
    PowerGuardianConfig,
)
from homelabctl.features.power_guardian.plan import (
    render_config as render_guardian,
)
from homelabctl.features.ssh.plan import (
    render_config as render_ssh,
)
from homelabctl.features.ssh.schema import (
    SSHSettings,
)


def test_ssh_template():
    rendered = render_ssh(
        SSHSettings()
    )

    assert (
        "PermitRootLogin no"
        in rendered
    )

    assert (
        "PasswordAuthentication no"
        in rendered
    )


def test_firewall_template():
    rendered = render_firewall(
        FirewallSettings(
            management_interface="mgmt0",
            management_ipv4_cidr="192.0.2.0/24",
        )
    )

    assert (
        "table inet filter"
        in rendered
    )

    assert (
        'iifname "mgmt0"'
        in rendered
    )


def test_headless_template():
    rendered = render_logind_config(
        HeadlessSettings(desktop_user="operator")
    )

    assert (
        "HandleLidSwitch=ignore"
        in rendered
    )


def test_guardian_template_boolean():
    rendered = render_guardian(
        PowerGuardianConfig(
            enabled=True
        )
    )

    assert (
        "enabled = true"
        in rendered
    )
