"""Headless and sleep-policy collector."""

from __future__ import annotations

import pwd
import re
import tempfile

from homelabctl.backend.collectors import CollectorResult
from homelabctl.core.actual_state import make_actual_state
from homelabctl.core.models import Status
from homelabctl.system.commands import run_command


POWER_SCHEMA = (
    "org.gnome.settings-daemon.plugins.power"
)

NON_INTERACTIVE_SHELLS = {
    "/bin/false",
    "/sbin/nologin",
    "/usr/bin/false",
    "/usr/sbin/nologin",
}


class HeadlessCollector:
    name = "headless"

    def collect(self) -> CollectorResult:
        logind = self._logind_config()

        values: dict[str, object] = {
            "lid_switch": logind.get(
                "HandleLidSwitch"
            ),
            "lid_switch_external_power": logind.get(
                "HandleLidSwitchExternalPower"
            ),
            "lid_switch_docked": logind.get(
                "HandleLidSwitchDocked"
            ),
            "idle_action": logind.get(
                "IdleAction"
            ),
        }

        values.update(
            self._gsettings_for_user(
                "Debian-gdm",
                prefix="gdm",
            )
        )

        desktop_users: dict[
            str,
            dict[str, object],
        ] = {}

        for username in self._desktop_usernames():
            desktop_users[username] = (
                self._gsettings_for_user(
                    username,
                    prefix="",
                )
            )

        values["desktop_users"] = desktop_users

        status = self._status(values)

        state = make_actual_state(
            "headless",
            status=status,
            summary=(
                "Headless, lid and login-screen "
                "power policy."
            ),
            values=values,
        )

        return CollectorResult(modules=[state])

    def _desktop_usernames(self) -> list[str]:
        """Return eligible interactive non-system users."""

        usernames: list[str] = []

        for entry in pwd.getpwall():
            if (
                entry.pw_uid < 1000
                or entry.pw_uid >= 65534
            ):
                continue

            shell = (
                entry.pw_shell or ""
            ).strip()

            if shell in NON_INTERACTIVE_SHELLS:
                continue

            usernames.append(
                entry.pw_name
            )

        return sorted(
            set(usernames)
        )

    def _logind_config(self) -> dict[str, str]:
        result = run_command(
            [
                "systemd-analyze",
                "cat-config",
                "systemd/logind.conf",
            ],
            timeout=10.0,
        )

        if not result.success:
            return {}

        values: dict[str, str] = {}

        for raw_line in result.stdout.splitlines():
            line = raw_line.strip()

            if (
                not line
                or line.startswith("#")
                or line.startswith("[")
                or "=" not in line
            ):
                continue

            key, value = line.split("=", 1)

            if re.fullmatch(
                r"[A-Za-z][A-Za-z0-9]*",
                key.strip(),
            ):
                values[key.strip()] = value.strip()

        return values

    def _gsettings_for_user(
        self,
        username: str,
        *,
        prefix: str,
    ) -> dict[str, object]:
        """Read a user's GSettings without changing UID.

        homelabd deliberately runs inside a hardened systemd sandbox.
        Some sandbox combinations prevent setuid(), so the read-only
        collector must not depend on runuser.

        The user's real configuration directory remains read-only.
        dconf cache writes are redirected to a temporary directory.
        """

        keys = (
            "sleep-inactive-ac-type",
            "sleep-inactive-ac-timeout",
            "sleep-inactive-battery-type",
            "sleep-inactive-battery-timeout",
        )

        try:
            account = pwd.getpwnam(
                username
            )
        except KeyError:
            return {
                (
                    f"{prefix}_{key.replace('-', '_')}"
                    if prefix
                    else key.replace("-", "_")
                ): None
                for key in keys
            }

        home = account.pw_dir

        values: dict[str, object] = {}

        with tempfile.TemporaryDirectory(
            prefix="homelabctl-dconf-",
        ) as cache_dir:
            for key in keys:
                result = run_command(
                    [
                        "/usr/bin/env",
                        f"HOME={home}",
                        (
                            "XDG_CONFIG_HOME="
                            f"{home}/.config"
                        ),
                        (
                            "XDG_CACHE_HOME="
                            f"{cache_dir}"
                        ),
                        "/usr/bin/gsettings",
                        "get",
                        POWER_SCHEMA,
                        key,
                    ],
                    timeout=10.0,
                )

                normalized = (
                    key.replace("-", "_")
                )

                output_key = (
                    f"{prefix}_{normalized}"
                    if prefix
                    else normalized
                )

                output = (
                    result.stdout.strip()
                    if result.success
                    else None
                )

                if output and (
                    output.startswith("'")
                    and output.endswith("'")
                ):
                    output = output[1:-1]

                if output is not None:
                    try:
                        output = int(output)
                    except ValueError:
                        pass

                values[output_key] = output

        return values

    def _status(
        self,
        values: dict[str, object],
    ) -> Status:
        expected = {
            "lid_switch": "ignore",
            "lid_switch_external_power": "ignore",
            "lid_switch_docked": "ignore",
            "idle_action": "ignore",
            "gdm_sleep_inactive_ac_type": "nothing",
            "gdm_sleep_inactive_battery_type": "nothing",
        }

        for key, expected_value in expected.items():
            if values.get(key) != expected_value:
                return Status.WARNING

        return Status.PASS
