from homelabctl.features.firewall.plan import (
    render_config,
)
from homelabctl.features.firewall.schema import (
    FirewallSettings,
)


def test_firewall_render():
    settings = FirewallSettings(
        management_interface="mgmt0",
        management_ipv4_cidr="192.0.2.0/24",
    )

    output = render_config(settings)

    assert "table inet filter" in output
    assert "policy drop" in output
    assert 'iifname "mgmt0"' in output
    assert "192.0.2.0/24" in output
    assert "tcp dport 22" in output
