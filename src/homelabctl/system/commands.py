"""Safe subprocess helpers."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from collections.abc import Sequence


@dataclass(slots=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


def run_command(
    command: Sequence[str],
    *,
    timeout: float = 10.0,
    check: bool = False,
    env: dict[str, str] | None = None,
) -> CommandResult:
    if not command:
        raise ValueError("Command cannot be empty.")

    completed = subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=env,
    )

    result = CommandResult(
        command=tuple(command),
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )

    if check and not result.success:
        raise subprocess.CalledProcessError(
            result.returncode,
            list(command),
            output=result.stdout,
            stderr=result.stderr,
        )

    return result
