#!/usr/bin/env python3
"""Invoke a Bash function from an interactive shell without interpolating arguments.

This small adapter exists for local launchers such as ``codex_yinhe`` that are
shell functions defined by the user's interactive Bash configuration rather
than executables discoverable through ``PATH``.

Usage with the host eval runner::

    python3 scripts/run_host_evals.py \
      --launcher "python3 scripts/bash_function_launcher.py codex_yinhe" \
      --suite trigger --case trend-zh-current-ai

The function name is restricted to a normal Bash identifier. All remaining
arguments are passed positionally to the function inside ``bash -ic``; no prompt
or eval content is interpolated into shell source text.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from typing import Mapping, Sequence


_FUNCTION_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_BASH_SCRIPT = r'''
function_name="$1"
shift
if [[ "$(type -t "$function_name")" != "function" ]]; then
  printf 'bash function not found: %s\n' "$function_name" >&2
  exit 127
fi
"$function_name" "$@"
'''.strip()


class BashFunctionLauncherError(ValueError):
    """Raised when a requested shell-function launcher is unsafe or invalid."""


def validate_function_name(value: str) -> str:
    if not _FUNCTION_NAME_RE.fullmatch(value):
        raise BashFunctionLauncherError(
            "Bash function name must match [A-Za-z_][A-Za-z0-9_]*"
        )
    return value


def build_bash_command(function_name: str, arguments: Sequence[str]) -> list[str]:
    name = validate_function_name(function_name)
    return [
        "bash",
        "--noprofile",
        "-ic",
        _BASH_SCRIPT,
        "ati-bash-function-launcher",
        name,
        *arguments,
    ]


def run(
    function_name: str,
    arguments: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
) -> int:
    command = build_bash_command(function_name, arguments)
    completed = subprocess.run(command, env=dict(env) if env is not None else None)
    return completed.returncode


def main(argv: Sequence[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if not values:
        print(
            "usage: bash_function_launcher.py FUNCTION [ARG ...]",
            file=sys.stderr,
        )
        return 2

    try:
        function_name = validate_function_name(values[0])
    except BashFunctionLauncherError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    return run(function_name, values[1:], env=os.environ)


if __name__ == "__main__":
    raise SystemExit(main())
