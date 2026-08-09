from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.bash_function_launcher import (
    BashFunctionLauncherError,
    build_bash_command,
    validate_function_name,
)


ROOT = Path(__file__).resolve().parents[1]


class BashFunctionLauncherTests(unittest.TestCase):
    def test_function_name_validation_rejects_shell_syntax(self) -> None:
        self.assertEqual(validate_function_name("codex_yinhe"), "codex_yinhe")
        for value in (
            "codex-yinhe",
            "codex_yinhe;echo bad",
            "$(touch /tmp/bad)",
            "1codex",
            "",
        ):
            with self.subTest(value=value):
                with self.assertRaises(BashFunctionLauncherError):
                    validate_function_name(value)

    def test_build_command_passes_arguments_positionally(self) -> None:
        prompt = "hello; $(not-a-command) ' quoted"
        command = build_bash_command(
            "codex_yinhe",
            ["exec", "--sandbox", "read-only", "--json", prompt],
        )
        self.assertEqual(command[:3], ["bash", "--noprofile", "-ic"])
        self.assertEqual(command[-6:], [
            "codex_yinhe",
            "exec",
            "--sandbox",
            "read-only",
            "--json",
            prompt,
        ])
        self.assertNotIn(prompt, command[3])

    def test_cli_executes_function_loaded_from_interactive_bashrc(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            home = Path(home_dir)
            (home / ".bashrc").write_text(
                "fake_codex() { printf 'FUNC:%s\\n' \"$*\"; }\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["HOME"] = str(home)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "bash_function_launcher.py"),
                    "fake_codex",
                    "exec",
                    "--json",
                    "hello world",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("FUNC:exec --json hello world", completed.stdout)

    def test_cli_returns_127_for_missing_function(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            home = Path(home_dir)
            (home / ".bashrc").write_text("# intentionally empty\n", encoding="utf-8")
            env = os.environ.copy()
            env["HOME"] = str(home)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "bash_function_launcher.py"),
                    "missing_function",
                    "exec",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
            )
            self.assertEqual(completed.returncode, 127)
            self.assertIn("bash function not found: missing_function", completed.stderr)


if __name__ == "__main__":
    unittest.main()
