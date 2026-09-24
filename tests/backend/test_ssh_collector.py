import base64
import hashlib

from homelabctl.backend.collectors.ssh import SSHCollector


def test_parse_effective_config():
    output = """
port 22
permitrootlogin no
passwordauthentication no
pubkeyauthentication yes
kbdinteractiveauthentication no
allowusers operator admin
allowgroups ssh-users
maxauthtries 3
clientaliveinterval 300
clientalivecountmax 2
x11forwarding no
allowtcpforwarding yes
"""

    values = SSHCollector._parse_effective_config(output)

    assert values["port"] == 22
    assert values["permit_root_login"] == "no"
    assert values["password_authentication"] == "no"
    assert values["pubkey_authentication"] == "yes"
    assert values["kbd_interactive_authentication"] == "no"
    assert values["allow_users"] == ["operator", "admin"]
    assert values["allow_groups"] == ["ssh-users"]
    assert values["max_auth_tries"] == 3
    assert values["client_alive_interval"] == 300
    assert values["client_alive_count_max"] == 2
    assert values["x11_forwarding"] == "no"
    assert values["allow_tcp_forwarding"] == "yes"


def test_effective_config_defaults_empty_access_lists():
    values = SSHCollector._parse_effective_config(
        "port 22\npermitrootlogin no\n"
    )

    assert values["allow_users"] == []
    assert values["allow_groups"] == []


def test_parse_include_patterns():
    text = """
# comment
Include /etc/ssh/sshd_config.d/*.conf
PermitRootLogin no
"""

    assert SSHCollector._parse_include_patterns(text) == [
        "/etc/ssh/sshd_config.d/*.conf"
    ]

def test_parse_authorized_key():
    encoded = base64.b64encode(b"abc").decode("ascii")

    record = SSHCollector._parse_authorized_key(
        (
            'from="192.0.2.0/24" '
            f"ssh-ed25519 {encoded} laptop"
        ),
        user="operator",
        source_file="/home/operator/.ssh/authorized_keys",
    )

    digest = hashlib.sha256(b"abc").digest()
    expected = (
        "SHA256:"
        + base64.b64encode(digest)
        .decode("ascii")
        .rstrip("=")
    )

    assert record is not None
    assert record["user"] == "operator"
    assert record["type"] == "ssh-ed25519"
    assert record["fingerprint"] == expected
    assert record["comment"] == "laptop"


def test_parse_authorized_key_ignores_comments():
    assert (
        SSHCollector._parse_authorized_key(
            "# disabled key",
            user="operator",
            source_file="authorized_keys",
        )
        is None
    )


def test_parse_who_idle_by_pid_variable_terminal_width():
    output = """
operator sshd         2026-09-22 22:15   ?     4796 (192.0.2.10)
operator sshd pts/5   2026-09-22 22:05   .     3372 (192.0.2.10)
operator sshd pts/4   2026-09-22 22:03 00:07   3245 (192.0.2.10)
Debian-gdm tty1     2026-09-22 21:11 old     1412
"""

    assert SSHCollector._parse_who_idle_by_pid(
        output
    ) == {
        "4796": "?",
        "3372": ".",
        "3245": "00:07",
    }


def test_parse_loginctl_key_value_output():
    output = """
Id=12
Name=operator
Leader=2874
Remote=yes
RemoteHost=192.0.2.10
Service=sshd
Type=tty
Class=user
State=active
"""

    assert SSHCollector._parse_key_value_output(
        output
    ) == {
        "Id": "12",
        "Name": "operator",
        "Leader": "2874",
        "Remote": "yes",
        "RemoteHost": "192.0.2.10",
        "Service": "sshd",
        "Type": "tty",
        "Class": "user",
        "State": "active",
    }
