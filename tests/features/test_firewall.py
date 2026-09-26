import pytest

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
            "trusted_ipv4_cidrs": sorted(
                settings.trusted_ipv4_cidrs
            ),
            "allowed_tcp_ports": sorted(
                settings.allowed_tcp_ports
            ),
            "allowed_udp_ports": sorted(
                settings.allowed_udp_ports
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



def test_firewall_advanced_policy_sets():
    settings = FirewallSettings(
        management_interface="mgmt0",
        management_ipv4_cidr="192.0.2.0/24",
        ssh_port=2222,
        trusted_ipv4_cidrs=(
            "198.51.100.0/24",
            "203.0.113.0/24",
        ),
        allowed_tcp_ports=(
            80,
            443,
        ),
        allowed_udp_ports=(
            53,
        ),
    )

    output = render_config(
        settings
    )

    assert (
        "set homelabctl_trusted_ipv4"
        in output
    )

    assert (
        "elements = { 192.0.2.0/24, "
        "198.51.100.0/24, "
        "203.0.113.0/24 }"
        in output
    )

    assert (
        "set homelabctl_allowed_tcp_ports"
        in output
    )

    assert (
        "elements = { 80, 443 }"
        in output
    )

    assert (
        "set homelabctl_allowed_udp_ports"
        in output
    )

    assert (
        "elements = { 53 }"
        in output
    )

    assert (
        'iifname "mgmt0" '
        "ip saddr @homelabctl_trusted_ipv4 "
        "tcp dport @homelabctl_allowed_tcp_ports "
        "ct state new accept"
        in output
    )

    assert (
        'iifname "mgmt0" '
        "ip saddr @homelabctl_trusted_ipv4 "
        "udp dport @homelabctl_allowed_udp_ports "
        "ct state new accept"
        in output
    )


def test_firewall_rejects_invalid_trusted_networks():
    invalid_sets = (
        (
            "2001:db8::/64",
        ),
        (
            "198.51.100.10/24",
        ),
        (
            "192.0.2.128/25",
        ),
        (
            "198.51.100.0/24",
            "198.51.100.128/25",
        ),
    )

    for trusted in invalid_sets:
        settings = FirewallSettings(
            management_interface="mgmt0",
            management_ipv4_cidr=(
                "192.0.2.0/24"
            ),
            trusted_ipv4_cidrs=trusted,
        )

        with pytest.raises(
            ValueError
        ):
            settings.validate()


def test_firewall_rejects_invalid_allowed_ports():
    invalid_ports = (
        (
            (0,),
            (),
        ),
        (
            (65536,),
            (),
        ),
        (
            (80, 80),
            (),
        ),
        (
            (),
            (53, 53),
        ),
        (
            (True,),
            (),
        ),
    )

    for tcp_ports, udp_ports in invalid_ports:
        settings = FirewallSettings(
            management_interface="mgmt0",
            management_ipv4_cidr=(
                "192.0.2.0/24"
            ),
            allowed_tcp_ports=tcp_ports,
            allowed_udp_ports=udp_ports,
        )

        with pytest.raises(
            ValueError
        ):
            settings.validate()



def test_advanced_policy_verification_passes():
    settings = FirewallSettings(
        management_interface="mgmt0",
        management_ipv4_cidr=(
            "192.0.2.0/24"
        ),
        ssh_port=2222,
        trusted_ipv4_cidrs=(
            "198.51.100.0/24",
        ),
        allowed_tcp_ports=(
            80,
            443,
        ),
        allowed_udp_ports=(
            53,
        ),
    )

    report = verify(
        _actual_for(
            settings
        ),
        settings,
    )

    assert report.passed is True


def test_advanced_policy_verification_detects_drift():
    settings = FirewallSettings(
        management_interface="mgmt0",
        management_ipv4_cidr=(
            "192.0.2.0/24"
        ),
        trusted_ipv4_cidrs=(
            "198.51.100.0/24",
        ),
        allowed_tcp_ports=(
            80,
            443,
        ),
    )

    actual = _actual_for(
        settings
    )

    actual.values[
        "allowed_tcp_ports"
    ].value = [
        80
    ]

    report = verify(
        actual,
        settings,
    )

    assert report.passed is False
