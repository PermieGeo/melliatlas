"""Cross-check the next bounded task against normative requirements and test inventory."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/specs/active/subspecs/subspec-01-backend-planning_implementation_plan.md"
SPEC = ROOT / "docs/specs/active/subspecs/subspec-01-backend-planning.md"


def task_field(task: str, label: str) -> str:
    match = re.search(rf"(?m)^- \*\*{re.escape(label)}:\*\*\s*(.*)$", task)
    return match.group(1).strip() if match else ""


def convergence_errors(plan: str, spec: str, root: Path) -> list[str]:
    """Find unknown requirements/tests, nonexistent current owners, and false task acceptance."""
    errors: list[str] = []
    match = re.search(
        r"(?ms)^## (?:\d+\. )?Next bounded delivery task\s*\n(.*?)(?=^## |\Z)", plan
    )
    if match is None:
        return ["Missing next-task section"]
    task = match.group(1)
    task_id = task_field(task, "Task ID")
    if not re.fullmatch(r"`MVP01-BE-V\d{2}`", task_id):
        errors.append("Invalid bounded task identifier")
    status = task_field(task, "Status").casefold()
    if not status.startswith("proposed"):
        errors.append("Next task must not claim implementation or acceptance")

    requirements = re.findall(r"`(MVP01-BE-R\d{2})`", task_field(task, "Requirement IDs"))
    inventory_refs = re.findall(r"`(BE-T\d{3})`", task_field(task, "Test inventory IDs"))
    known_requirements = set(re.findall(r"(?m)^\| `(MVP01-BE-R\d{2})` \|", spec))
    inventory_ids = re.findall(r"(?m)^\| `(BE-T\d{3})` \|", plan)
    if not requirements:
        errors.append("Current task has no requirement IDs")
    if len(requirements) != len(set(requirements)):
        errors.append("Duplicate task requirement IDs")
    if not inventory_refs:
        errors.append("Current task has no test inventory IDs")
    if len(inventory_refs) != len(set(inventory_refs)):
        errors.append("Duplicate current task test IDs")
    for requirement in requirements:
        if requirement not in known_requirements:
            errors.append(f"Unknown requirement: {requirement}")
    for test_id in inventory_refs:
        if test_id not in inventory_ids:
            errors.append(f"Unknown test inventory ID: {test_id}")
    if len(set(inventory_ids)) != len(inventory_ids):
        errors.append("Duplicate test inventory IDs")
    if not inventory_ids:
        errors.append("Acceptance test inventory is empty")
    if inventory_ids and inventory_ids != [f"BE-T{i:03d}" for i in range(1, len(inventory_ids) + 1)]:
        errors.append("Acceptance test inventory has missing or unordered IDs")
    inventory_requirements: dict[str, set[str]] = {}
    for line in plan.splitlines():
        if not line.startswith("| `BE-T"):
            continue
        columns = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(columns) != 5 or not re.search(r"R\d{2}", columns[-1]):
            errors.append(f"Inventory entry lacks a requirement mapping: {columns[0]}")
            continue
        mapped = set()
        for reference in re.findall(r"R\d{2}", columns[-1]):
            full = f"MVP01-BE-{reference}"
            mapped.add(full)
            if full not in known_requirements:
                errors.append(f"Inventory {columns[0].strip(chr(96))} has unknown requirement {full}")
        inventory_requirements[columns[0].strip("`")] = mapped
    task_set = set(requirements)
    if task_set and inventory_refs and not any(
        task_set.intersection(inventory_requirements.get(test_id, set()))
        for test_id in inventory_refs
    ):
        errors.append("Selected tests do not cover current task requirements")
    interfaces = task_field(task, "Existing interfaces")
    if not interfaces:
        errors.append("Current task does not identify existing interfaces")
    for path in re.findall(r"`(backend/[^`]+)`", interfaces):
        if not (root / path).is_file():
            errors.append(f"Unknown existing interface: {path}")
    if "**Exit evidence:**" not in task or "**Approval gates:**" not in task:
        errors.append("Current task lacks exit evidence or approval gates")
    return errors


class SddConvergenceTests(unittest.TestCase):
    def _current(self) -> tuple[str, str]:
        return PLAN.read_text(encoding="utf-8"), SPEC.read_text(encoding="utf-8")

    def test_current_task_maps_to_real_requirements_and_inventory(self) -> None:
        self.assertEqual([], convergence_errors(*self._current(), ROOT))

    def test_unknown_requirement_is_rejected(self) -> None:
        plan, spec = self._current()
        broken = plan.replace("`MVP01-BE-R06`,", "`MVP01-BE-R99`,", 1)
        self.assertIn("Unknown requirement: MVP01-BE-R99", convergence_errors(broken, spec, ROOT))

    def test_unknown_test_reference_is_rejected(self) -> None:
        plan, spec = self._current()
        broken = plan.replace("`BE-T019`,", "`BE-T999`,", 1)
        self.assertIn("Unknown test inventory ID: BE-T999", convergence_errors(broken, spec, ROOT))

    def test_false_task_acceptance_is_rejected(self) -> None:
        plan, spec = self._current()
        broken = plan.replace("**Status:** Proposed", "**Status:** Accepted", 1)
        self.assertIn("Next task must not claim implementation or acceptance", convergence_errors(broken, spec, ROOT))

    def test_nonexistent_implemented_interface_is_rejected(self) -> None:
        plan, spec = self._current()
        broken = plan.replace(
            "`backend/src/melliatlas/api/app.py`", "`backend/src/melliatlas/api/missing.py`", 1
        )
        self.assertIn(
            "Unknown existing interface: backend/src/melliatlas/api/missing.py",
            convergence_errors(broken, spec, ROOT),
        )

    def test_unknown_requirement_in_inventory_is_rejected(self) -> None:
        plan, spec = self._current()
        broken = plan.replace(
            "| `BE-T019` | U/B | TimeWindow | Reversed/out-of-season dates rejected; a same-day inclusive interval is valid | R10/R15 |",
            "| `BE-T019` | U/B | TimeWindow | Reversed/out-of-season dates rejected; a same-day inclusive interval is valid | R98/R15 |",
            1,
        )
        self.assertIn(
            "Inventory BE-T019 has unknown requirement MVP01-BE-R98",
            convergence_errors(broken, spec, ROOT),
        )

    def test_task_tests_must_cover_a_relevant_requirement(self) -> None:
        plan, spec = self._current()
        broken = plan.replace(
            "- **Test inventory IDs:** `BE-T019`, `BE-T020`, `BE-T026`, `BE-T027`, `BE-T045`, `BE-T047`, `BE-T052`, `BE-T053`",
            "- **Test inventory IDs:** `BE-T001`, `BE-T002`",
            1,
        )
        self.assertIn(
            "Selected tests do not cover current task requirements",
            convergence_errors(broken, spec, ROOT),
        )

    def test_duplicate_inventory_id_is_rejected(self) -> None:
        plan, spec = self._current()
        broken = plan.replace("| `BE-T002` |", "| `BE-T001` |", 1)
        self.assertIn("Duplicate test inventory IDs", convergence_errors(broken, spec, ROOT))


if __name__ == "__main__":
    unittest.main()
