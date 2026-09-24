from homelabctl.features.ssh.plan import (
    render_config,
)
from homelabctl.features.ssh.schema import (
    SSHSettings,
)


def test_default_ssh_config():
    output = render_config(
        SSHSettings()
    )

    assert "PermitRootLogin no" in output
    assert "PasswordAuthentication no" in output
    assert "PubkeyAuthentication yes" in output
    assert "MaxAuthTries 3" in output


def test_full_ssh_settings_surface():
    settings = SSHSettings(
        port=2222,
        permit_root_login="prohibit-password",
        password_authentication="no",
        pubkey_authentication="yes",
        kbd_interactive_authentication="no",
        allow_users=(
            "operator",
            "admin",
        ),
        allow_groups=(
            "ssh-users",
        ),
        max_auth_tries=4,
        client_alive_interval=300,
        client_alive_count_max=2,
        x11_forwarding="no",
        allow_tcp_forwarding="local",
    )

    settings.validate()

    assert settings.port == 2222
    assert settings.allow_users == (
        "operator",
        "admin",
    )
    assert settings.allow_groups == (
        "ssh-users",
    )
    assert settings.client_alive_interval == 300
    assert settings.client_alive_count_max == 2
    assert settings.allow_tcp_forwarding == "local"


def test_empty_access_lists_are_valid():
    settings = SSHSettings(
        allow_users=(),
        allow_groups=(),
    )

    settings.validate()


def test_invalid_port_is_rejected():
    settings = SSHSettings(
        port=0,
    )

    try:
        settings.validate()
    except ValueError:
        return

    raise AssertionError(
        "Invalid SSH port was accepted."
    )


def test_negative_client_alive_interval_is_rejected():
    settings = SSHSettings(
        client_alive_interval=-1,
    )

    try:
        settings.validate()
    except ValueError:
        return

    raise AssertionError(
        "Negative ClientAliveInterval was accepted."
    )


def test_invalid_tcp_forwarding_is_rejected():
    settings = SSHSettings(
        allow_tcp_forwarding="sometimes",
    )

    try:
        settings.validate()
    except ValueError:
        return

    raise AssertionError(
        "Invalid AllowTcpForwarding was accepted."
    )


def test_access_list_entry_with_whitespace_is_rejected():
    settings = SSHSettings(
        allow_users=(
            "operator admin",
        ),
    )

    try:
        settings.validate()
    except ValueError:
        return

    raise AssertionError(
        "Whitespace-containing AllowUsers entry "
        "was accepted."
    )


def test_canonical_ssh_pipeline():
    from homelabctl.apply.runner import SAFE_TARGETS
    from homelabctl.features.ssh.apply import (
        build_apply_transaction,
    )
    from homelabctl.features.ssh.constants import (
        MANAGED_SSH_PATH,
    )
    from homelabctl.features.ssh.inspect import (
        desired_state,
    )
    from homelabctl.features.ssh.plan import (
        SSH_DROP_IN,
        render_config,
    )

    expected_path = (
        "/etc/ssh/sshd_config.d/"
        "00-homelabctl.conf"
    )

    assert MANAGED_SSH_PATH == expected_path
    assert SSH_DROP_IN == expected_path
    assert expected_path in SAFE_TARGETS["ssh"]

    settings = SSHSettings(
        port=2222,
        allow_users=(
            "operator",
            "admin",
        ),
        allow_groups=(
            "ssh-users",
        ),
        client_alive_interval=300,
        client_alive_count_max=2,
        allow_tcp_forwarding="local",
    )

    rendered = render_config(
        settings
    )

    assert "Port 2222" in rendered
    assert "PermitRootLogin no" in rendered
    assert "PasswordAuthentication no" in rendered
    assert "PubkeyAuthentication yes" in rendered

    assert (
        "KbdInteractiveAuthentication no"
        in rendered
    )

    assert (
        "AllowUsers operator admin"
        in rendered
    )

    assert (
        "AllowGroups ssh-users"
        in rendered
    )

    assert "MaxAuthTries 3" in rendered

    assert (
        "ClientAliveInterval 300"
        in rendered
    )

    assert (
        "ClientAliveCountMax 2"
        in rendered
    )

    assert "X11Forwarding no" in rendered

    assert (
        "AllowTcpForwarding local"
        in rendered
    )

    desired = desired_state(
        settings
    )

    assert (
        desired.settings["port"].value
        == 2222
    )

    assert (
        desired.settings["allow_users"].value
        == ["operator", "admin"]
    )

    assert (
        desired.settings["allow_groups"].value
        == ["ssh-users"]
    )

    transaction = build_apply_transaction(
        settings
    )

    assert (
        transaction.actions[0].target
        == expected_path
    )


def test_empty_access_lists_are_omitted_from_template():
    from homelabctl.features.ssh.plan import (
        render_config,
    )

    rendered = render_config(
        SSHSettings(
            allow_users=(),
            allow_groups=(),
        )
    )

    assert "AllowUsers " not in rendered
    assert "AllowGroups " not in rendered


def test_disconnect_session_transaction():
    from homelabctl.features.ssh.session_actions import (
        build_disconnect_session_transaction,
    )

    transaction = (
        build_disconnect_session_transaction(
            "69"
        )
    )

    assert transaction.feature == "ssh"
    assert len(transaction.actions) == 1

    action = transaction.actions[0]

    assert action.argv == [
        "/usr/bin/loginctl",
        "terminate-session",
        "69",
    ]

    assert action.backup is False


def test_disconnect_session_id_validation():
    from homelabctl.features.ssh.session_actions import (
        validate_session_id,
    )

    assert validate_session_id("69") == "69"
    assert validate_session_id("c1") == "c1"

    for invalid in (
        "",
        " ",
        "../69",
        "/69",
        "69 70",
        "69;whoami",
        "--help",
    ):
        try:
            validate_session_id(
                invalid
            )
        except ValueError:
            continue

        raise AssertionError(
            f"Invalid session ID accepted: "
            f"{invalid!r}"
        )


def test_runner_accepts_only_valid_session_terminate():
    from homelabctl.apply.runner import (
        validate_run_command,
    )

    validate_run_command(
        "ssh",
        [
            "/usr/bin/loginctl",
            "terminate-session",
            "69",
        ],
    )

    validate_run_command(
        "ssh",
        [
            "/usr/bin/loginctl",
            "terminate-session",
            "c1",
        ],
    )

    rejected = (
        [
            "/usr/bin/loginctl",
            "terminate-session",
            "../69",
        ],
        [
            "/usr/bin/loginctl",
            "terminate-session",
            "69",
            "--kill-who=all",
        ],
        [
            "/usr/bin/loginctl",
            "kill-session",
            "69",
        ],
        [
            "/bin/sh",
            "-c",
            "id",
        ],
    )

    for argv in rejected:
        try:
            validate_run_command(
                "ssh",
                list(argv),
            )
        except PermissionError:
            continue

        raise AssertionError(
            f"Unsafe command accepted: {argv!r}"
        )


def test_disconnect_target_rejects_current(
    monkeypatch,
):
    from homelabctl.apply import runner

    def fake_property(session_id, name):
        if session_id == "self":
            return "75"
        raise AssertionError

    monkeypatch.setattr(
        runner,
        "_logind_property",
        fake_property,
    )

    try:
        runner.validate_disconnect_target("75")
    except PermissionError:
        return

    raise AssertionError(
        "Current session was accepted."
    )


def test_disconnect_target_requires_remote_ssh(
    monkeypatch,
):
    from homelabctl.apply import runner

    values = {
        ("self", "Id"): "75",
        ("68", "Service"): "sshd",
        ("68", "Remote"): "yes",
        ("68", "State"): "active",
    }

    monkeypatch.setattr(
        runner,
        "_logind_property",
        lambda session_id, name: values[
            (session_id, name)
        ],
    )

    runner.validate_disconnect_target("68")
