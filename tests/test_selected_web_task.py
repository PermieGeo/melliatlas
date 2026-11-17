"""Validate the selected task pointer without implying feature acceptance."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SPEC_ROOT = ROOT / "docs/specs"
TASK_PATTERN = re.compile(r"^docs/specs/active/tasks/[a-z0-9-]+/task\.md$")
ORACLE_PATTERN = re.compile(r"\*\*(PLACE-A\d{2}):\*\*")


def task_context_errors(state: dict[str, object], root: Path) -> list[str]:
    """Require one existing task pair bound to the selected workstream."""
    errors: list[str] = []
    task_path = state.get("selectedTaskPath")
    if not isinstance(task_path, str) or TASK_PATTERN.fullmatch(task_path) is None:
        return ["Invalid selected task path"]
    task_file = (root / task_path).resolve()
    plan_file = task_file.with_name("task-plan.md")
    if not task_file.is_relative_to(root.resolve()) or not task_file.is_file():
        errors.append("Selected task is missing or outside repository")
        return errors
    if not plan_file.is_file():
        errors.append("Selected task plan is missing")
        return errors
    workstreams = state.get("workstreams")
    selected = state.get("selectedWorkstreamId")
    if not isinstance(workstreams, list) or not any(
        isinstance(workstream, dict)
        and workstream.get("id") == selected
        and workstream.get("specPath") == "docs/specs/active/subspecs/subspec-01-web-mvp.md"
        for workstream in workstreams
    ):
        errors.append("Selected task does not match the selected Web workstream")
    task = task_file.read_text(encoding="utf-8")
    plan = plan_file.read_text(encoding="utf-8")
    ids = set(ORACLE_PATTERN.findall(task))
    if not ids or any(oracle not in plan for oracle in ids):
        errors.append("Selected task plan does not map its acceptance oracles")
    if "**Status:** DESIGN SELECTED" not in task or "**Status:** DESIGN ONLY" not in plan:
        errors.append("Selected task has unexpected authorization state")
    if "**Acceptance:** NOT CLAIMED" not in task:
        errors.append("Selected task claims acceptance prematurely")
    return errors


class SelectedWebTaskTests(unittest.TestCase):
    def test_checkpoint_pointer_and_task_pair(self) -> None:
        state = json.loads((SPEC_ROOT / "STATE.json").read_text(encoding="utf-8"))
        schema = json.loads((SPEC_ROOT / "state.schema.json").read_text(encoding="utf-8"))
        self.assertEqual([], list(Draft202012Validator(schema).iter_errors(state)))
        self.assertEqual([], task_context_errors(state, ROOT))
        self.assertEqual([], state["featureAcceptances"])

    def test_broken_task_path_is_rejected(self) -> None:
        state = json.loads((SPEC_ROOT / "STATE.json").read_text(encoding="utf-8"))
        state["selectedTaskPath"] = "docs/specs/active/tasks/../missing/task.md"
        self.assertIn("Invalid selected task path", task_context_errors(state, ROOT))
        state["selectedTaskPath"] = "docs/specs/active/tasks/unknown/task.md"
        self.assertIn("Selected task is missing or outside repository", task_context_errors(state, ROOT))

    def test_redesign_task_is_not_legacy_w01_acceptance(self) -> None:
        task = (ROOT / "docs/specs/active/tasks/web-saved-place-bbox/task.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("implementation pending explicit developer approval", task)
        self.assertIn("server-side", task)
        self.assertIn("30 km", task)
        self.assertIn("positive-area overlap", task)

    def test_spec_index_has_no_duplicate_section_heading(self) -> None:
        content = (SPEC_ROOT / "README.md").read_text(encoding="utf-8")
        headings = re.findall(r"(?m)^## (.+)$", content)
        self.assertEqual(len(headings), len(set(headings)))


if __name__ == "__main__":
    unittest.main()
