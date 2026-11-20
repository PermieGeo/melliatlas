"""Ensure build and test stages execute disjoint project gates."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProjectShellRunnerTests(unittest.TestCase):
    def _invoke(self, script_name: str, *, with_web: bool = False) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / script_name
            shutil.copyfile(ROOT / script_name, script)
            (root / "backend" / "src").mkdir(parents=True)
            (root / "backend" / "scripts").mkdir()
            (root / "backend" / "pyproject.toml").write_text("[project]\nname='fixture'\n")
            binary = root / "bin"
            binary.mkdir()
            python = binary / "python3"
            python.write_text('#!/bin/sh\nprintf "python3:%s\\n" "$*" >> "$RECORDED_COMMANDS"\n')
            python.chmod(0o755)

            if with_web:
                web = root / "web"
                (web / "src").mkdir(parents=True)
                (web / "package.json").write_text('{}\n')
                (web / "node_modules" / ".bin").mkdir(parents=True)
                for command in ("prettier", "eslint", "tsc", "vite"):
                    executable = web / "node_modules" / ".bin" / command
                    executable.write_text(
                        '#!/bin/sh\nprintf "%s:%s\\n" "$(basename "$0")" "$*" '
                        '>> "$RECORDED_COMMANDS"\n'
                    )
                    executable.chmod(0o755)
                npm = binary / "npm"
                npm.write_text('#!/bin/sh\nprintf "npm:%s\\n" "$*" >> "$RECORDED_COMMANDS"\n')
                npm.chmod(0o755)

            journal = root / "calls.txt"
            environment = dict(os.environ)
            environment["PATH"] = f"{binary}{os.pathsep}{environment.get('PATH', '')}"
            environment["RECORDED_COMMANDS"] = str(journal)
            subprocess.run(["sh", str(script)], env=environment, check=True, capture_output=True)
            return journal.read_text().splitlines()

    def test_build_runner_checks_application_without_running_tests(self) -> None:
        calls = self._invoke("build.sh", with_web=True)
        self.assertIn("python3:-m ruff check --no-cache backend/src backend/scripts", calls)
        self.assertIn("python3:-m ruff format --check backend/src backend/scripts", calls)
        self.assertIn("python3:-m pyright --project backend backend/src", calls)
        self.assertNotIn("python3:-m pyright --project backend backend/src backend/scripts", calls)
        self.assertIn("tsc:-p ../tsconfig.build.json --noEmit", calls)
        self.assertIn("vite:build", calls)
        self.assertIn("eslint:src", calls)
        self.assertTrue(any(call.startswith("python3:-B -c") for call in calls))
        self.assertFalse(any("pytest" in call or "test:ci" in call for call in calls))

    def test_build_typescript_configuration_excludes_tests(self) -> None:
        config = json.loads((ROOT / "tsconfig.build.json").read_text())
        self.assertEqual(config["extends"], "./web/tsconfig.json")
        self.assertEqual(config["include"], ["web/src", "web/vite.config.ts"])
        self.assertEqual(config["exclude"], ["web/tests", "web/e2e"])

    def test_check_runner_runs_tests_without_rebuilding(self) -> None:
        calls = self._invoke("run-tests.sh", with_web=True)
        self.assertIn("python3:-B -m unittest discover -s tests -p test_*.py -v", calls)
        self.assertIn("python3:-B -m pytest -p no:cacheprovider backend/tests", calls)
        self.assertIn("npm:run test:ci", calls)
        self.assertFalse(any("ruff" in call or "pyright" in call or "build" in call for call in calls))

    def test_shell_formatter_executes_project_formatters(self) -> None:
        calls = self._invoke("run-format.sh")
        self.assertIn("python3:-m ruff check --fix --no-cache backend", calls)
        self.assertIn("python3:-m ruff format backend", calls)


if __name__ == "__main__":
    unittest.main()
