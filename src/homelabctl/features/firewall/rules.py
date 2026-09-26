"""Managed service-rule model for the firewall feature."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from uuid import NAMESPACE_URL, uuid4, uuid5

from homelabctl.config.managed import (
    DEFAULT_MANAGED_STATE_PATH,
    load_managed_state,
    save_managed_state,
    set_feature,
)


SERVICE_RULES_SETTINGS_KEY = "service_rules"

_RULE_ID_RE = re.compile(
    r"^[0-9a-f]{32}$"
)

_ALLOWED_PROTOCOLS = {
    "tcp",
    "udp",
}

_V1_SOURCE = "trusted"
_V1_INTERFACE = "management"
_V1_ACTION = "allow"


@dataclass(
    frozen=True,
    slots=True,
)
class FirewallServiceRule:
    """One user-managed inbound service rule."""

    id: str
    name: str
    protocol: str
    port: int
    enabled: bool = True

    source: str = _V1_SOURCE
    interface: str = _V1_INTERFACE
    action: str = _V1_ACTION

    def validate(self) -> None:
        if not _RULE_ID_RE.fullmatch(
            self.id
        ):
            raise ValueError(
                "Service rule ID must be "
                "32 lowercase hexadecimal characters."
            )

        if (
            not self.name
            or self.name != self.name.strip()
            or len(self.name) > 48
            or "\n" in self.name
            or "\r" in self.name
        ):
            raise ValueError(
                "Service rule name must be "
                "1-48 trimmed characters."
            )

        if (
            self.protocol
            not in _ALLOWED_PROTOCOLS
        ):
            raise ValueError(
                "Service rule protocol must be "
                "tcp or udp."
            )

        if (
            not isinstance(
                self.port,
                int,
            )
            or isinstance(
                self.port,
                bool,
            )
            or not 1 <= self.port <= 65535
        ):
            raise ValueError(
                "Service rule port must be "
                "between 1 and 65535."
            )

        if not isinstance(
            self.enabled,
            bool,
        ):
            raise ValueError(
                "Service rule enabled state "
                "must be boolean."
            )

        if self.source != _V1_SOURCE:
            raise ValueError(
                "Firewall service rules currently "
                "support only trusted sources."
            )

        if (
            self.interface
            != _V1_INTERFACE
        ):
            raise ValueError(
                "Firewall service rules currently "
                "support only the management interface."
            )

        if self.action != _V1_ACTION:
            raise ValueError(
                "Firewall service rules currently "
                "support only allow actions."
            )


def new_service_rule(
    *,
    name: str,
    protocol: str,
    port: int,
    enabled: bool = True,
) -> FirewallServiceRule:
    rule = FirewallServiceRule(
        id=uuid4().hex,
        name=name.strip(),
        protocol=protocol.strip().lower(),
        port=port,
        enabled=enabled,
    )

    rule.validate()

    return rule


def validate_service_rules(
    rules: Iterable[
        FirewallServiceRule
    ],
) -> tuple[
    FirewallServiceRule,
    ...,
]:
    normalized = tuple(
        rules
    )

    seen_ids: set[str] = set()
    seen_endpoints: set[
        tuple[str, int]
    ] = set()

    for rule in normalized:
        if not isinstance(
            rule,
            FirewallServiceRule,
        ):
            raise TypeError(
                "Firewall service rules must use "
                "FirewallServiceRule values."
            )

        rule.validate()

        if rule.id in seen_ids:
            raise ValueError(
                "Firewall service rule IDs "
                "must be unique."
            )

        endpoint = (
            rule.protocol,
            rule.port,
        )

        if endpoint in seen_endpoints:
            raise ValueError(
                "A firewall service rule already "
                "uses this protocol and port."
            )

        seen_ids.add(
            rule.id
        )

        seen_endpoints.add(
            endpoint
        )

    return normalized


def compile_allowed_ports(
    rules: Iterable[
        FirewallServiceRule
    ],
) -> tuple[
    tuple[int, ...],
    tuple[int, ...],
]:
    normalized = (
        validate_service_rules(
            rules
        )
    )

    tcp = sorted(
        rule.port
        for rule in normalized
        if (
            rule.enabled
            and rule.protocol == "tcp"
        )
    )

    udp = sorted(
        rule.port
        for rule in normalized
        if (
            rule.enabled
            and rule.protocol == "udp"
        )
    )

    return (
        tuple(tcp),
        tuple(udp),
    )


def service_rules_to_payload(
    rules: Iterable[
        FirewallServiceRule
    ],
) -> list[
    dict[str, object]
]:
    normalized = (
        validate_service_rules(
            rules
        )
    )

    return [
        {
            "id": rule.id,
            "name": rule.name,
            "protocol": rule.protocol,
            "port": rule.port,
            "enabled": rule.enabled,
            "source": rule.source,
            "interface": (
                rule.interface
            ),
            "action": rule.action,
        }
        for rule in normalized
    ]


def service_rules_from_payload(
    payload: Any,
) -> tuple[
    FirewallServiceRule,
    ...,
]:
    if not isinstance(
        payload,
        list,
    ):
        raise ValueError(
            "Firewall service rules must "
            "be stored as a list."
        )

    rules = []

    for raw in payload:
        if not isinstance(
            raw,
            dict,
        ):
            raise ValueError(
                "Each firewall service rule "
                "must be an object."
            )

        rule = FirewallServiceRule(
            id=raw.get(
                "id",
                "",
            ),
            name=raw.get(
                "name",
                "",
            ),
            protocol=raw.get(
                "protocol",
                "",
            ),
            port=raw.get(
                "port",
                0,
            ),
            enabled=raw.get(
                "enabled",
                True,
            ),
            source=raw.get(
                "source",
                _V1_SOURCE,
            ),
            interface=raw.get(
                "interface",
                _V1_INTERFACE,
            ),
            action=raw.get(
                "action",
                _V1_ACTION,
            ),
        )

        rule.validate()

        rules.append(
            rule
        )

    return validate_service_rules(
        rules
    )


def load_managed_service_rules(
    path: Path = (
        DEFAULT_MANAGED_STATE_PATH
    ),
) -> tuple[
    FirewallServiceRule,
    ...,
] | None:
    state = load_managed_state(
        path
    )

    feature = state.features.get(
        "firewall"
    )

    if feature is None:
        return None

    if (
        SERVICE_RULES_SETTINGS_KEY
        not in feature.settings
    ):
        return None

    return service_rules_from_payload(
        feature.settings[
            SERVICE_RULES_SETTINGS_KEY
        ]
    )


def save_managed_service_rules(
    rules: Iterable[
        FirewallServiceRule
    ],
    *,
    transaction_id: str | None = None,
    path: Path = (
        DEFAULT_MANAGED_STATE_PATH
    ),
) -> None:
    normalized = (
        validate_service_rules(
            rules
        )
    )

    state = load_managed_state(
        path
    )

    feature = state.features.get(
        "firewall"
    )

    settings = (
        dict(
            feature.settings
        )
        if feature is not None
        else {}
    )

    settings[
        SERVICE_RULES_SETTINGS_KEY
    ] = service_rules_to_payload(
        normalized
    )

    set_feature(
        state,
        "firewall",
        enabled=True,
        settings=settings,
        transaction_id=transaction_id,
    )

    save_managed_state(
        state,
        path,
    )


def service_rules_from_active_ports(
    *,
    tcp_ports: Iterable[int],
    udp_ports: Iterable[int],
) -> tuple[
    FirewallServiceRule,
    ...,
]:
    rules: list[
        FirewallServiceRule
    ] = []

    for protocol, ports in (
        (
            "tcp",
            tcp_ports,
        ),
        (
            "udp",
            udp_ports,
        ),
    ):
        for port in sorted(
            ports
        ):
            if (
                not isinstance(
                    port,
                    int,
                )
                or isinstance(
                    port,
                    bool,
                )
                or not 1 <= port <= 65535
            ):
                raise ValueError(
                    "Active firewall ports must "
                    "be between 1 and 65535."
                )

            identity = uuid5(
                NAMESPACE_URL,
                (
                    "homelabctl/firewall/"
                    f"{protocol}/{port}"
                ),
            ).hex

            rules.append(
                FirewallServiceRule(
                    id=identity,
                    name=(
                        f"{protocol.upper()} "
                        f"{port}"
                    ),
                    protocol=protocol,
                    port=port,
                    enabled=True,
                )
            )

    return validate_service_rules(
        rules
    )
