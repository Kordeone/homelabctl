"""Linux system inspection primitives used by HomeLabCTL."""

from homelabctl.system.commands import CommandResult, run_command
from homelabctl.system.permissions import (
    current_username,
    effective_gid,
    effective_uid,
    is_root,
)

__all__ = [
    "CommandResult",
    "current_username",
    "effective_gid",
    "effective_uid",
    "is_root",
    "run_command",
]
