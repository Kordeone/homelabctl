"""Process identity and permission inspection."""

from __future__ import annotations

import os
import pwd


def effective_uid() -> int:
    return os.geteuid()


def effective_gid() -> int:
    return os.getegid()


def is_root() -> bool:
    return effective_uid() == 0


def current_username() -> str:
    return pwd.getpwuid(effective_uid()).pw_name


def user_exists(username: str) -> bool:
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False


def user_uid(username: str) -> int | None:
    try:
        return pwd.getpwnam(username).pw_uid
    except KeyError:
        return None


def supplementary_groups() -> set[int]:
    return set(os.getgroups())
