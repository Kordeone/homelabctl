from homelabctl.backend.collectors.firewall import (
    _parse_managed_policy,
)


RULESET = """
table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
        iifname "lo" accept
        ct state invalid drop
        ct state established,related accept
        iifname "mgmt0" ip saddr 192.0.2.0/24 tcp dport 2222 ct state new accept
        iifname "mgmt0" udp sport 67 udp dport 68 accept
        meta l4proto icmp accept
        meta l4proto ipv6-icmp accept
    }

    chain forward {
        type filter hook forward priority filter; policy drop;
    }

    chain output {
        type filter hook output priority filter; policy accept;
    }
}
"""


def test_parse_managed_firewall_policy():
    values = _parse_managed_policy(
        RULESET
    )

    assert (
        values["management_interface"]
        == "mgmt0"
    )

    assert (
        values["management_ipv4_cidr"]
        == "192.0.2.0/24"
    )

    assert values[
        "ssh_port"
    ] == 2222

    assert values[
        "allow_dhcp_client"
    ] is True

    assert values[
        "allow_ipv4_icmp"
    ] is True

    assert values[
        "allow_ipv6_icmp"
    ] is True


def test_parse_optional_rules_disabled():
    ruleset = """
table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
        iifname "mgmt0" ip saddr 198.51.100.0/24 tcp dport 22 ct state new accept
    }
}
"""

    values = _parse_managed_policy(
        ruleset
    )

    assert values[
        "allow_dhcp_client"
    ] is False

    assert values[
        "allow_ipv4_icmp"
    ] is False

    assert values[
        "allow_ipv6_icmp"
    ] is False


def test_parse_missing_management_rule():
    values = _parse_managed_policy(
        "table inet filter {}\n"
    )

    assert values[
        "management_interface"
    ] is None

    assert values[
        "management_ipv4_cidr"
    ] is None

    assert values[
        "ssh_port"
    ] is None

    assert values[
        "allow_dhcp_client"
    ] is None
