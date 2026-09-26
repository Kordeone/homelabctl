from pathlib import Path

import pytest

from homelabctl.config.managed import (
    ManagedState,
    load_managed_state,
    save_managed_state,
    set_feature,
)
from homelabctl.features.firewall.rules import (
    FirewallServiceRule,
    compile_allowed_ports,
    load_managed_service_rules,
    new_service_rule,
    save_managed_service_rules,
    service_rules_from_active_ports,
    service_rules_from_payload,
    service_rules_to_payload,
    validate_service_rules,
)


def _rule(
    *,
    rule_id: str,
    name: str,
    protocol: str,
    port: int,
    enabled: bool = True,
) -> FirewallServiceRule:
    return FirewallServiceRule(
        id=rule_id,
        name=name,
        protocol=protocol,
        port=port,
        enabled=enabled,
    )


def test_new_rule_normalizes_user_input():
    rule = new_service_rule(
        name="  HTTPS  ",
        protocol=" TCP ",
        port=443,
    )

    assert len(rule.id) == 32
    assert rule.name == "HTTPS"
    assert rule.protocol == "tcp"
    assert rule.port == 443
    assert rule.enabled is True
    assert rule.source == "trusted"
    assert (
        rule.interface
        == "management"
    )
    assert rule.action == "allow"


@pytest.mark.parametrize(
    (
        "protocol",
        "port",
    ),
    [
        ("icmp", 80),
        ("tcp", 0),
        ("tcp", 65536),
        ("udp", True),
    ],
)
def test_rule_rejects_invalid_endpoint(
    protocol,
    port,
):
    rule = _rule(
        rule_id="a" * 32,
        name="Test",
        protocol=protocol,
        port=port,
    )

    with pytest.raises(
        ValueError
    ):
        rule.validate()


def test_rule_collection_rejects_duplicate_endpoint():
    rules = (
        _rule(
            rule_id="a" * 32,
            name="Web",
            protocol="tcp",
            port=443,
        ),
        _rule(
            rule_id="b" * 32,
            name="Other Web",
            protocol="tcp",
            port=443,
            enabled=False,
        ),
    )

    with pytest.raises(
        ValueError,
        match="protocol and port",
    ):
        validate_service_rules(
            rules
        )


def test_compile_uses_enabled_rules_only():
    rules = (
        _rule(
            rule_id="a" * 32,
            name="HTTPS",
            protocol="tcp",
            port=443,
        ),
        _rule(
            rule_id="b" * 32,
            name="HTTP",
            protocol="tcp",
            port=80,
        ),
        _rule(
            rule_id="c" * 32,
            name="Jellyfin",
            protocol="tcp",
            port=8096,
            enabled=False,
        ),
        _rule(
            rule_id="d" * 32,
            name="DNS",
            protocol="udp",
            port=53,
        ),
    )

    tcp, udp = compile_allowed_ports(
        rules
    )

    assert tcp == (
        80,
        443,
    )

    assert udp == (
        53,
    )


def test_payload_round_trip_preserves_disabled_rule():
    rules = (
        _rule(
            rule_id="a" * 32,
            name="HTTPS",
            protocol="tcp",
            port=443,
        ),
        _rule(
            rule_id="b" * 32,
            name="Jellyfin",
            protocol="tcp",
            port=8096,
            enabled=False,
        ),
    )

    payload = (
        service_rules_to_payload(
            rules
        )
    )

    restored = (
        service_rules_from_payload(
            payload
        )
    )

    assert restored == rules
    assert restored[1].enabled is False


def test_managed_persistence_preserves_other_settings(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "managed.json"
    )

    state = ManagedState()

    set_feature(
        state,
        "firewall",
        enabled=True,
        settings={
            "keep_me": "yes",
        },
    )

    save_managed_state(
        state,
        path,
    )

    rules = (
        _rule(
            rule_id="a" * 32,
            name="HTTPS",
            protocol="tcp",
            port=443,
        ),
        _rule(
            rule_id="b" * 32,
            name="Jellyfin",
            protocol="tcp",
            port=8096,
            enabled=False,
        ),
    )

    save_managed_service_rules(
        rules,
        transaction_id="c" * 32,
        path=path,
    )

    assert (
        load_managed_service_rules(
            path
        )
        == rules
    )

    loaded = load_managed_state(
        path
    )

    feature = loaded.features[
        "firewall"
    ]

    assert (
        feature.settings[
            "keep_me"
        ]
        == "yes"
    )

    assert (
        feature.last_transaction_id
        == "c" * 32
    )


def test_missing_managed_rules_returns_none(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "managed.json"
    )

    assert (
        load_managed_service_rules(
            path
        )
        is None
    )


def test_active_port_migration_is_deterministic():
    first = service_rules_from_active_ports(
        tcp_ports=(
            443,
            80,
        ),
        udp_ports=(
            53,
        ),
    )

    second = service_rules_from_active_ports(
        tcp_ports=(
            80,
            443,
        ),
        udp_ports=(
            53,
        ),
    )

    assert first == second

    assert [
        (
            rule.name,
            rule.protocol,
            rule.port,
        )
        for rule in first
    ] == [
        (
            "TCP 80",
            "tcp",
            80,
        ),
        (
            "TCP 443",
            "tcp",
            443,
        ),
        (
            "UDP 53",
            "udp",
            53,
        ),
    ]
