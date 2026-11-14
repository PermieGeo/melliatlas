"""Regression checks for the local apatch formatter bootstrap."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "enable-apatch-fmt.py"
SPEC = importlib.util.spec_from_file_location("melliatlas_fmt_setup", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FormatterSetupTests(unittest.TestCase):
    def test_appends_only_formatter_and_keeps_other_settings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.yaml"
            original = 'schema_version: 1\nchecks:\n  - ["sh", "./run-tests.sh"]\ncustom: keep\n'
            config.write_text(original, encoding="utf-8")
            self.assertTrue(MODULE.enable_formatter(config))
            updated = config.read_text(encoding="utf-8")
            self.assertTrue(updated.startswith(original))
            self.assertIn('format_commands:\n  - ["sh", "./run-format.sh"]', updated)
            self.assertFalse(MODULE.enable_formatter(config))
            self.assertEqual(config.read_text(encoding="utf-8"), updated)

    def test_rejects_conflicting_format_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.yaml"
            original = 'schema_version: 1\nchecks: []\nformat_commands:\n  - ["echo", "other"]\n'
            config.write_text(original, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Existing format_commands differ"):
                MODULE.enable_formatter(config)
            self.assertEqual(config.read_text(encoding="utf-8"), original)

    def test_rejects_missing_checks_or_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.yaml"
            for original in ('schema_version: 1\n', 'checks: []\n'):
                config.write_text(original, encoding="utf-8")
                with self.assertRaises(ValueError):
                    MODULE.enable_formatter(config)
                self.assertEqual(config.read_text(encoding="utf-8"), original)

    def test_rejects_symlink_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "actual.yaml"
            source.write_text('schema_version: 1\nchecks: []\n', encoding="utf-8")
            config = Path(directory) / "config.yaml"
            config.symlink_to(source)
            with self.assertRaises(ValueError):
                MODULE.enable_formatter(config)
            self.assertEqual(source.read_text(encoding="utf-8"), 'schema_version: 1\nchecks: []\n')


if __name__ == "__main__":
    unittest.main()
