"""Runtime-derived defaults for the local managed host."""

from __future__ import annotations

import getpass
import ipaddress
import json
import os
from functools import lru_cache
from typing import Any

from homelabctl.system.commands import run_command


def current_user() -> str:
    """Return the normal user running HomeLabCTL."""

    sudo_user = os.environ.get(
        "SUDO_USER",
        "",
    ).strip()

    if (
        sudo_user
        and sudo_user != "root"
    ):
        return sudo_user

    user = getpass.getuser().strip()

    if not user:
        raise RuntimeError(
            "Unable to determine the current user."
        )

    return user


def _ip_json(
    command: list[str],
) -> list[dict[str, Any]]:
    result = run_command(
        command,
        timeout=5.0,
    )

    if not result.success:
        raise RuntimeError(
            "Unable to inspect host networking."
        )

    try:
        data = json.loads(
            result.stdout
        )
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Invalid response from ip command."
        ) from exc

    if not isinstance(
        data,
        list,
    ):
        raise RuntimeError(
            "Unexpected response from ip command."
        )

    return [
        item
        for item in data
        if isinstance(
            item,
            dict,
        )
    ]


@lru_cache(maxsize=1)
def management_network() -> tuple[str, str]:
    """Return default-route interface and IPv4 network."""

    routes = _ip_json(
        [
            "ip",
            "-j",
            "route",
            "show",
            "default",
        ]
    )

    interface = ""

    for route in routes:
        candidate = route.get(
            "dev"
        )

        if isinstance(
            candidate,
            str,
        ) and candidate.strip():
            interface = candidate.strip()
            break

    if not interface:
        raise RuntimeError(
            "Unable to determine the management "
            "interface from the default route."
        )

    addresses = _ip_json(
        [
            "ip",
            "-j",
            "address",
            "show",
            "dev",
            interface,
        ]
    )

    for record in addresses:
        if record.get(
            "ifname"
        ) != interface:
            continue

        addr_info = record.get(
            "addr_info",
            [],
        )

        if not isinstance(
            addr_info,
            list,
        ):
            continue

        for address in addr_info:
            if not isinstance(
                address,
                dict,
            ):
                continue

            if address.get(
                "family"
            ) != "inet":
                continue

            if address.get(
                "scope"
            ) == "host":
                continue

            local = address.get(
                "local"
            )

            prefixlen = address.get(
                "prefixlen"
            )

            if not isinstance(
                local,
                str,
            ):
                continue

            if not isinstance(
                prefixlen,
                int,
            ):
                continue

            network = ipaddress.ip_interface(
                f"{local}/{prefixlen}"
            ).network

            return (
                interface,
                str(network),
            )

    raise RuntimeError(
        "Unable to determine the management "
        "IPv4 network."
    )


def default_management_interface() -> str:
    return management_network()[0]


def default_management_ipv4_cidr() -> str:
    return management_network()[1]
