"""SSH feature configuration schema."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SSHSettings:
    port: int = 22

    permit_root_login: str = "no"
    password_authentication: str = "no"
    pubkey_authentication: str = "yes"
    kbd_interactive_authentication: str = "no"

    allow_users: tuple[str, ...] = ()
    allow_groups: tuple[str, ...] = ()

    max_auth_tries: int = 3

    client_alive_interval: int = 0
    client_alive_count_max: int = 3

    x11_forwarding: str = "no"
    allow_tcp_forwarding: str = "yes"

    def validate(self) -> None:
        yes_no = {
            "yes",
            "no",
        }

        if (
            type(self.port) is not int
            or not 1 <= self.port <= 65535
        ):
            raise ValueError(
                "Port must be between 1 and 65535."
            )

        if self.permit_root_login not in {
            "yes",
            "no",
            "prohibit-password",
            "forced-commands-only",
        }:
            raise ValueError(
                "Invalid PermitRootLogin value."
            )

        for name, value in (
            (
                "PasswordAuthentication",
                self.password_authentication,
            ),
            (
                "PubkeyAuthentication",
                self.pubkey_authentication,
            ),
            (
                "KbdInteractiveAuthentication",
                self.kbd_interactive_authentication,
            ),
            (
                "X11Forwarding",
                self.x11_forwarding,
            ),
        ):
            if value not in yes_no:
                raise ValueError(
                    f"{name} must be yes or no."
                )

        if self.allow_tcp_forwarding not in {
            "yes",
            "no",
            "all",
            "local",
            "remote",
        }:
            raise ValueError(
                "AllowTcpForwarding must be one of: "
                "yes, no, all, local, remote."
            )

        self._validate_access_list(
            "AllowUsers",
            self.allow_users,
        )

        self._validate_access_list(
            "AllowGroups",
            self.allow_groups,
        )

        if (
            type(self.max_auth_tries) is not int
            or not 1 <= self.max_auth_tries <= 10
        ):
            raise ValueError(
                "MaxAuthTries must be between 1 and 10."
            )

        if (
            type(self.client_alive_interval) is not int
            or self.client_alive_interval < 0
        ):
            raise ValueError(
                "ClientAliveInterval must be "
                "zero or greater."
            )

        if (
            type(self.client_alive_count_max) is not int
            or self.client_alive_count_max < 0
        ):
            raise ValueError(
                "ClientAliveCountMax must be "
                "zero or greater."
            )

    @staticmethod
    def _validate_access_list(
        name: str,
        values: tuple[str, ...],
    ) -> None:
        if not isinstance(
            values,
            tuple,
        ):
            raise ValueError(
                f"{name} must be a tuple of SSH patterns."
            )

        for value in values:
            if not isinstance(
                value,
                str,
            ):
                raise ValueError(
                    f"{name} entries must be strings."
                )

            if not value:
                raise ValueError(
                    f"{name} entries cannot be empty."
                )

            if value != value.strip():
                raise ValueError(
                    f"{name} entries cannot contain "
                    "leading or trailing whitespace."
                )

            if any(
                character.isspace()
                for character in value
            ):
                raise ValueError(
                    f"{name} entries cannot contain "
                    "whitespace."
                )
