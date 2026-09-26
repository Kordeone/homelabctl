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


from homelabctl.core.actual_state import (
    make_actual_state,
)
from homelabctl.core.models import Status
from homelabctl.features.firewall.inspect import (
    evaluate,
)
from homelabctl.features.firewall.verify import (
    verify,
)


def _actual_for(
    settings: FirewallSettings,
):
    return make_actual_state(
        "firewall",
        status=Status.PASS,
        summary="test",
        values={
            "service_active": "active",
            "service_enabled": "enabled",
            "ruleset_present": True,
            "inet_filter_table": True,
            "input_policy_drop": True,
            "forward_policy_drop": True,
            "management_interface": (
                settings.management_interface
            ),
            "management_ipv4_cidr": (
                settings.management_ipv4_cidr
            ),
            "ssh_port": (
                settings.ssh_port
            ),
            "allow_dhcp_client": (
                settings.allow_dhcp_client
            ),
            "allow_ipv4_icmp": (
                settings.allow_ipv4_icmp
            ),
            "allow_ipv6_icmp": (
                settings.allow_ipv6_icmp
            ),
        },
    )


def test_config_aware_firewall_verify_passes():
    settings = FirewallSettings(
        management_interface="mgmt0",
        management_ipv4_cidr=(
            "192.0.2.0/24"
        ),
        ssh_port=2222,
        allow_dhcp_client=False,
        allow_ipv4_icmp=True,
        allow_ipv6_icmp=False,
    )

    actual = _actual_for(
        settings
    )

    assert (
        evaluate(
            actual,
            settings,
        )
        == Status.PASS
    )

    report = verify(
        actual,
        settings,
    )

    assert report.passed is True


def test_config_aware_firewall_detects_drift():
    settings = FirewallSettings(
        management_interface="mgmt0",
        management_ipv4_cidr=(
            "192.0.2.0/24"
        ),
        ssh_port=2222,
    )

    actual = _actual_for(
        settings
    )

    actual.values[
        "ssh_port"
    ].value = 22

    report = verify(
        actual,
        settings,
    )

    assert report.passed is False
