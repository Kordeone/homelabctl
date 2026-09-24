"""Read-only OpenSSH state collector."""

from __future__ import annotations

import base64
import glob
import hashlib
import os
import pwd
import shlex
import shutil
from pathlib import Path
from typing import Any

from homelabctl.backend.collectors import CollectorResult
from homelabctl.core.actual_state import make_actual_state
from homelabctl.core.models import Status
from homelabctl.system.commands import run_command
from homelabctl.system.systemd import (
    unit_active_state,
    unit_enabled_state,
    unit_exists,
)


class SSHCollector:
    name = "ssh"

    MAIN_CONFIG = Path("/etc/ssh/sshd_config")
    DEFAULT_DROPIN_DIR = Path("/etc/ssh/sshd_config.d")
    MANAGED_FILENAME = "00-homelabctl.conf"
    LEGACY_FILENAMES: tuple[str, ...] = ()

    KEYS = {
        "port": "port",
        "permitrootlogin": "permit_root_login",
        "passwordauthentication": "password_authentication",
        "pubkeyauthentication": "pubkey_authentication",
        "kbdinteractiveauthentication":
            "kbd_interactive_authentication",
        "allowusers": "allow_users",
        "allowgroups": "allow_groups",
        "maxauthtries": "max_auth_tries",
        "clientaliveinterval": "client_alive_interval",
        "clientalivecountmax": "client_alive_count_max",
        "x11forwarding": "x11_forwarding",
        "allowtcpforwarding": "allow_tcp_forwarding",
    }

    INTEGER_KEYS = {
        "port",
        "max_auth_tries",
        "client_alive_interval",
        "client_alive_count_max",
    }

    def collect(self) -> CollectorResult:
        service = self._service_name()
        executable = self._find_sshd()

        values: dict[str, Any] = {
            "service": service,
            "service_exists": bool(service),
            "service_active": (
                unit_active_state(service)
                if service
                else "not-found"
            ),
            "service_enabled": (
                unit_enabled_state(service)
                if service
                else "not-found"
            ),
            "sshd_binary": executable,
        }

        effective, available, error = self._effective_config(
            executable
        )

        values["effective_config_available"] = available
        values["effective_config_error"] = error
        values.update(effective)

        values.update(self._configuration_files())
        (
            sessions,
            sessions_available,
            sessions_error,
        ) = self._active_sessions()

        values["sessions"] = sessions
        values["sessions_available"] = sessions_available
        values["sessions_error"] = sessions_error

        (
            authorized_keys,
            scan_complete,
            key_errors,
        ) = self._authorized_keys()

        values["authorized_keys"] = authorized_keys
        values["authorized_keys_scan_complete"] = scan_complete
        values["authorized_keys_errors"] = key_errors

        status = (
            Status.PASS
            if service and available
            else Status.WARNING
        )

        state = make_actual_state(
            "ssh",
            status=status,
            summary=(
                "OpenSSH service, effective configuration, "
                "sessions and authorized keys."
            ),
            values=values,
        )

        return CollectorResult(modules=[state])

    def _service_name(self) -> str | None:
        for unit in ("ssh.service", "sshd.service"):
            if unit_exists(unit):
                return unit

        return None

    @staticmethod
    def _find_sshd() -> str | None:
        candidates = (
            "/usr/sbin/sshd",
            "/usr/local/sbin/sshd",
            "/sbin/sshd",
        )

        for candidate in candidates:
            if os.path.isfile(candidate) and os.access(
                candidate,
                os.X_OK,
            ):
                return candidate

        return shutil.which("sshd")

    def _effective_config(
        self,
        executable: str | None,
    ) -> tuple[dict[str, Any], bool, str | None]:
        if not executable:
            return {}, False, "sshd executable not found"

        result = run_command(
            [executable, "-T"],
            timeout=10.0,
        )

        if not result.success:
            detail = (
                getattr(result, "stderr", "")
                or getattr(result, "stdout", "")
                or "sshd -T failed"
            )

            return {}, False, str(detail).strip()

        return (
            self._parse_effective_config(result.stdout),
            True,
            None,
        )

    @classmethod
    def _parse_effective_config(
        cls,
        output: str,
    ) -> dict[str, Any]:
        values: dict[str, Any] = {
            "allow_users": [],
            "allow_groups": [],
        }

        for line in output.splitlines():
            key, separator, raw_value = line.partition(" ")

            if not separator:
                continue

            mapped = cls.KEYS.get(key.lower())

            if not mapped:
                continue

            value = raw_value.strip()

            if mapped in {"allow_users", "allow_groups"}:
                values[mapped] = (
                    value.split()
                    if value
                    else []
                )
                continue

            if mapped in cls.INTEGER_KEYS:
                try:
                    values[mapped] = int(value)
                except ValueError:
                    values[mapped] = value
                continue

            values[mapped] = value

        return values

    def _configuration_files(self) -> dict[str, Any]:
        include_patterns: list[str] = []
        dropin_files: list[str] = []
        config_error: str | None = None

        if self.MAIN_CONFIG.exists():
            try:
                text = self.MAIN_CONFIG.read_text(
                    encoding="utf-8",
                    errors="replace",
                )

                include_patterns = (
                    self._parse_include_patterns(text)
                )

                for pattern in include_patterns:
                    for match in glob.glob(pattern):
                        if match not in dropin_files:
                            dropin_files.append(match)

            except OSError as exc:
                config_error = str(exc)

        dropin_files.sort()

        managed_file = (
            self.DEFAULT_DROPIN_DIR
            / self.MANAGED_FILENAME
        )

        legacy_files = [
            str(self.DEFAULT_DROPIN_DIR / filename)
            for filename in self.LEGACY_FILENAMES
            if (
                self.DEFAULT_DROPIN_DIR
                / filename
            ).exists()
        ]

        return {
            "main_config": str(self.MAIN_CONFIG),
            "main_config_present": self.MAIN_CONFIG.exists(),
            "main_config_error": config_error,
            "include_patterns": include_patterns,
            "dropin_files": dropin_files,
            "managed_file": str(managed_file),
            "managed_file_present": managed_file.exists(),
            "legacy_managed_files": legacy_files,
        }

    @staticmethod
    def _parse_include_patterns(
        text: str,
    ) -> list[str]:
        patterns: list[str] = []

        for raw_line in text.splitlines():
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            try:
                parts = shlex.split(
                    line,
                    comments=True,
                    posix=True,
                )
            except ValueError:
                continue

            if (
                not parts
                or parts[0].lower() != "include"
            ):
                continue

            for pattern in parts[1:]:
                if pattern not in patterns:
                    patterns.append(pattern)

        return patterns

    def _active_sessions(
        self,
    ) -> tuple[
        list[dict[str, str]],
        bool,
        str | None,
    ]:
        loginctl = self._find_command(
            "/usr/bin/loginctl",
            "loginctl",
        )

        if not loginctl:
            return (
                [],
                False,
                "loginctl executable not found",
            )

        list_result = run_command(
            [
                loginctl,
                "list-sessions",
                "--no-legend",
                "--no-pager",
            ],
            timeout=5.0,
        )

        if not list_result.success:
            detail = (
                getattr(list_result, "stderr", "")
                or getattr(list_result, "stdout", "")
                or "loginctl list-sessions failed"
            )

            return [], False, str(detail).strip()

        idle_by_pid = self._who_idle_by_pid()

        sessions: list[dict[str, str]] = []
        errors: list[str] = []

        for raw_line in list_result.stdout.splitlines():
            parts = raw_line.split()

            if not parts:
                continue

            session_id = parts[0]

            result = run_command(
                [
                    loginctl,
                    "show-session",
                    session_id,
                    "--no-pager",
                    "-p",
                    "Id",
                    "-p",
                    "Name",
                    "-p",
                    "Leader",
                    "-p",
                    "Remote",
                    "-p",
                    "RemoteHost",
                    "-p",
                    "RemoteUser",
                    "-p",
                    "Service",
                    "-p",
                    "Type",
                    "-p",
                    "Class",
                    "-p",
                    "State",
                    "-p",
                    "Timestamp",
                ],
                timeout=5.0,
            )

            if not result.success:
                errors.append(
                    f"{session_id}: "
                    f"{getattr(result, 'stderr', '').strip()}"
                )
                continue

            data = self._parse_key_value_output(
                result.stdout
            )

            if data.get("Remote") != "yes":
                continue

            if data.get("Class") != "user":
                continue

            # systemd-logind identifies SSH sessions by
            # PAM service. Keep the check conservative, but
            # tolerate missing Service on older systems.
            service = data.get("Service", "")

            if service and service != "sshd":
                continue

            leader = data.get("Leader", "")

            sessions.append(
                {
                    "session_id": (
                        data.get("Id")
                        or session_id
                    ),
                    "user": data.get("Name", ""),
                    "from": data.get(
                        "RemoteHost",
                        "",
                    ),
                    "login": data.get(
                        "Timestamp",
                        "",
                    ),
                    "idle": idle_by_pid.get(
                        leader,
                        "-",
                    ),
                    "service": service,
                    "type": data.get("Type", ""),
                    "state": data.get("State", ""),
                    "remote": "yes",
                }
            )

        sessions.sort(
            key=lambda item: (
                item.get("login", ""),
                item.get("session_id", ""),
            ),
            reverse=True,
        )

        error = (
            "; ".join(errors)
            if errors
            else None
        )

        return sessions, True, error

    def _who_idle_by_pid(
        self,
    ) -> dict[str, str]:
        who = self._find_command(
            "/usr/bin/who",
            "who",
        )

        if not who:
            return {}

        result = run_command(
            [who, "-u"],
            timeout=5.0,
        )

        if not result.success:
            return {}

        return self._parse_who_idle_by_pid(
            result.stdout
        )

    @staticmethod
    def _parse_who_idle_by_pid(
        output: str,
    ) -> dict[str, str]:
        idle_by_pid: dict[str, str] = {}

        for raw_line in output.splitlines():
            parts = raw_line.split()

            # Remote who -u rows end with:
            #
            # <date> <time> <idle> <pid> (<host>)
            #
            # The terminal field may itself occupy one or
            # multiple tokens, so parse from the right.
            if len(parts) < 7:
                continue

            remote = parts[-1]

            if not (
                remote.startswith("(")
                and remote.endswith(")")
            ):
                continue

            pid = parts[-2]
            idle = parts[-3]

            if not pid.isdigit():
                continue

            idle_by_pid[pid] = idle

        return idle_by_pid

    @staticmethod
    def _parse_key_value_output(
        output: str,
    ) -> dict[str, str]:
        values: dict[str, str] = {}

        for raw_line in output.splitlines():
            key, separator, value = raw_line.partition(
                "="
            )

            if not separator:
                continue

            values[key] = value

        return values

    def _authorized_keys(
        self,
    ) -> tuple[
        list[dict[str, str]],
        bool,
        list[str],
    ]:
        records: list[dict[str, str]] = []
        errors: list[str] = []

        for account in pwd.getpwall():
            home = Path(account.pw_dir)

            if not home.is_absolute():
                continue

            path = home / ".ssh" / "authorized_keys"

            try:
                if not path.is_file():
                    continue

                content = path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )

            except (OSError, PermissionError) as exc:
                errors.append(
                    f"{account.pw_name}: {exc}"
                )
                continue

            for raw_line in content.splitlines():
                record = self._parse_authorized_key(
                    raw_line,
                    user=account.pw_name,
                    source_file=str(path),
                )

                if record is not None:
                    records.append(record)

        records.sort(
            key=lambda item: (
                item["user"],
                item["fingerprint"],
            )
        )

        scan_complete = os.geteuid() == 0

        if not scan_complete:
            errors.append(
                "Backend is not running as root; "
                "authorized-key scan may be incomplete."
            )

        return records, scan_complete, errors

    @staticmethod
    def _parse_authorized_key(
        line: str,
        *,
        user: str,
        source_file: str,
    ) -> dict[str, str] | None:
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            return None

        try:
            parts = shlex.split(
                stripped,
                comments=False,
                posix=True,
            )
        except ValueError:
            return None

        key_index: int | None = None

        for index, token in enumerate(parts):
            if (
                token.startswith("ssh-")
                or token.startswith("ecdsa-")
                or token.startswith("sk-")
            ):
                key_index = index
                break

        if key_index is None:
            return None

        if key_index + 1 >= len(parts):
            return None

        key_type = parts[key_index]
        encoded = parts[key_index + 1]

        try:
            blob = base64.b64decode(
                encoded,
                validate=True,
            )
        except (ValueError, TypeError):
            return None

        digest = hashlib.sha256(blob).digest()

        fingerprint = (
            "SHA256:"
            + base64.b64encode(digest)
            .decode("ascii")
            .rstrip("=")
        )

        comment = " ".join(
            parts[key_index + 2:]
        )

        return {
            "user": user,
            "type": key_type,
            "fingerprint": fingerprint,
            "comment": comment,
            "source_file": source_file,
        }

    @staticmethod
    def _find_command(
        fixed_path: str,
        name: str,
    ) -> str | None:
        if os.path.isfile(fixed_path) and os.access(
            fixed_path,
            os.X_OK,
        ):
            return fixed_path

        return shutil.which(name)
