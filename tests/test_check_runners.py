"""Ensure apatch shell invocations cannot silently skip project checks."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProjectShellRunnerTests(unittest.TestCase):
    def _invoke(self, script_name: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / script_name
            shutil.copyfile(ROOT / script_name, script)
            (root / "backend").mkdir()
            (root / "backend" / "pyproject.toml").write_text("[project]\nname='fixture'\n")
            binary = root / "bin"
            binary.mkdir()
            python = binary / "python3"
            python.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$RECORDED_COMMANDS"\n')
            python.chmod(0o755)
            journal = root / "calls.txt"
            environment = dict(os.environ)
            environment["PATH"] = f"{binary}{os.pathsep}{environment.get('PATH', '')}"
            environment["RECORDED_COMMANDS"] = str(journal)
            subprocess.run(["sh", str(script)], env=environment, check=True, capture_output=True)
            return journal.read_text().splitlines()

    def test_shell_check_runner_executes_backend_gates(self) -> None:
        calls = self._invoke("run-tests.sh")
        self.assertIn("-B -m pytest -p no:cacheprovider backend/tests", calls)
        self.assertIn("-m ruff check --no-cache backend", calls)
        self.assertIn("-m pyright --project backend", calls)

    def test_shell_formatter_executes_project_formatters(self) -> None:
        calls = self._invoke("run-format.sh")
        self.assertIn("-m ruff check --fix --no-cache backend", calls)
        self.assertIn("-m ruff format backend", calls)


if __name__ == "__main__":
    unittest.main()
