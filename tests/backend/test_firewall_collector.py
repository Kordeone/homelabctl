from homelabctl.backend.collectors.firewall import (
    _parse_managed_policy,
)


LEGACY_RULESET = """
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
}
"""


ADVANCED_RULESET = """
table inet filter {
    set homelabctl_trusted_ipv4 {
        type ipv4_addr
        flags interval
        elements = { 192.0.2.0/24, 203.0.113.0/24, 198.51.100.0/24 }
    }

    set homelabctl_allowed_tcp_ports {
        type inet_service
        elements = { 443, 80 }
    }

    set homelabctl_allowed_udp_ports {
        type inet_service
        elements = { 5353, 53 }
    }

    chain input {
        type filter hook input priority filter; policy drop;

        iifname "mgmt0" ip saddr 192.0.2.0/24 tcp dport 2222 ct state new accept
        iifname "mgmt0" udp sport 67 udp dport 68 accept

        meta l4proto icmp accept
        meta l4proto ipv6-icmp accept

        iifname "mgmt0" ip saddr @homelabctl_trusted_ipv4 tcp dport @homelabctl_allowed_tcp_ports ct state new accept
        iifname "mgmt0" ip saddr @homelabctl_trusted_ipv4 udp dport @homelabctl_allowed_udp_ports ct state new accept
    }

    chain forward {
        type filter hook forward priority filter; policy drop;
    }
}
"""


def test_parse_managed_firewall_policy():
    values = _parse_managed_policy(
        LEGACY_RULESET
    )

    assert (
        values["management_interface"]
        == "mgmt0"
    )

    assert (
        values["management_ipv4_cidr"]
        == "192.0.2.0/24"
    )

    assert values["ssh_port"] == 2222

    assert (
        values["allow_dhcp_client"]
        is True
    )

    assert (
        values["allow_ipv4_icmp"]
        is True
    )

    assert (
        values["allow_ipv6_icmp"]
        is True
    )


def test_legacy_policy_has_empty_advanced_policy():
    values = _parse_managed_policy(
        LEGACY_RULESET
    )

    assert (
        values["trusted_ipv4_cidrs"]
        == []
    )

    assert (
        values["allowed_tcp_ports"]
        == []
    )

    assert (
        values["allowed_udp_ports"]
        == []
    )


def test_parse_optional_rules_disabled():
    ruleset = """
table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
        iifname "mgmt0" ip saddr 192.0.2.0/24 tcp dport 2222 ct state new accept
    }
}
"""

    values = _parse_managed_policy(
        ruleset
    )

    assert (
        values["allow_dhcp_client"]
        is False
    )

    assert (
        values["allow_ipv4_icmp"]
        is False
    )

    assert (
        values["allow_ipv6_icmp"]
        is False
    )


def test_parse_missing_management_rule():
    values = _parse_managed_policy(
        """
table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
    }
}
"""
    )

    assert (
        values["management_interface"]
        is None
    )

    assert (
        values["management_ipv4_cidr"]
        is None
    )

    assert (
        values["ssh_port"]
        is None
    )

    assert (
        values["allow_dhcp_client"]
        is None
    )


def test_parse_advanced_policy_sets():
    values = _parse_managed_policy(
        ADVANCED_RULESET
    )

    assert (
        values["trusted_ipv4_cidrs"]
        == [
            "198.51.100.0/24",
            "203.0.113.0/24",
        ]
    )

    assert (
        values["allowed_tcp_ports"]
        == [
            80,
            443,
        ]
    )

    assert (
        values["allowed_udp_ports"]
        == [
            53,
            5353,
        ]
    )


def test_advanced_port_set_requires_accept_rule():
    ruleset = ADVANCED_RULESET.replace(
        (
            'iifname "mgmt0" '
            "ip saddr @homelabctl_trusted_ipv4 "
            "tcp dport "
            "@homelabctl_allowed_tcp_ports "
            "ct state new accept"
        ),
        "",
    )

    values = _parse_managed_policy(
        ruleset
    )

    assert (
        values["allowed_tcp_ports"]
        is None
    )
