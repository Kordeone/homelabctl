from homelabctl.system import (
    runtime_defaults,
)


def test_current_user_prefers_sudo_user(
    monkeypatch,
):
    monkeypatch.setenv(
        "SUDO_USER",
        "operator",
    )

    monkeypatch.setattr(
        runtime_defaults.getpass,
        "getuser",
        lambda: "root",
    )

    assert (
        runtime_defaults.current_user()
        == "operator"
    )


def test_management_network_from_default_route(
    monkeypatch,
):
    runtime_defaults.management_network.cache_clear()

    def fake_ip_json(command):
        if "route" in command:
            return [
                {
                    "dst": "default",
                    "dev": "mgmt0",
                }
            ]

        return [
            {
                "ifname": "mgmt0",
                "addr_info": [
                    {
                        "family": "inet",
                        "local": "192.0.2.42",
                        "prefixlen": 24,
                        "scope": "global",
                    }
                ],
            }
        ]

    monkeypatch.setattr(
        runtime_defaults,
        "_ip_json",
        fake_ip_json,
    )

    assert (
        runtime_defaults.management_network()
        == (
            "mgmt0",
            "192.0.2.0/24",
        )
    )

    assert (
        runtime_defaults
        .default_management_interface()
        == "mgmt0"
    )

    assert (
        runtime_defaults
        .default_management_ipv4_cidr()
        == "192.0.2.0/24"
    )

    runtime_defaults.management_network.cache_clear()
