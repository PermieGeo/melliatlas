"""Regression checks for the distinction between authorization and acceptance."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_ROOT = ROOT / "docs/specs"
ACTIVE_SPEC = SPEC_ROOT / "active/subspecs/subspec-01-backend-planning.md"
ACTIVE_PLAN = SPEC_ROOT / "active/subspecs/subspec-01-backend-planning_implementation_plan.md"


def _field(markdown: str, name: str) -> str:
    match = re.search(rf"(?m)^(?:- )?\*\*{re.escape(name)}:\*\*\s*(.+)$", markdown)
    return match.group(1).strip() if match else ""


def authorization_errors(
    phase: str, umbrella: str, spec: str, plan: str, index: str
) -> list[str]:
    """Find contradictory workstream approval claims, independent of test outcomes."""
    errors: list[str] = []
    if phase != "READY_FOR_IMPLEMENTATION":
        return errors
    for label, document in (("sub-spec", spec), ("plan", plan)):
        approval = _field(document, "Requirements approval").casefold()
        implementation = _field(document, "Implementation authorization").casefold()
        acceptance = _field(document, "Acceptance").casefold()
        if "approved" not in approval:
            errors.append(f"{label}: requirements not approved")
        if "authorized" not in implementation or re.search(r"\bnone\b|\bnot authorized\b", implementation):
            errors.append(f"{label}: implementation authorization conflicts with checkpoint")
        if not acceptance.startswith("pending"):
            errors.append(f"{label}: acceptance conflicts with unfinished checkpoint")
    umbrella_authorization = _field(umbrella, "Active authorization").casefold()
    if "mvp-01" not in umbrella_authorization or "backend" not in umbrella_authorization:
        errors.append("umbrella: active backend authorization missing")
    umbrella_acceptance = _field(umbrella, "Acceptance").casefold()
    if "no" not in umbrella_acceptance or "accepted" in umbrella_acceptance:
        errors.append("umbrella: whole-stage acceptance must remain pending")
    if "backend requirements are approved" not in index.casefold():
        errors.append("index: active backend approval missing")
    if "acceptance" not in index.casefold() or "pending" not in index.casefold():
        errors.append("index: acceptance status missing")
    return errors


class SddAuthorizationTests(unittest.TestCase):
    def _inputs(self) -> tuple[str, str, str, str, str]:
        state = json.loads((SPEC_ROOT / "STATE.json").read_text(encoding="utf-8"))
        selected = next(
            item for item in state["workstreams"] if item["id"] == state["selectedWorkstreamId"]
        )
        self.assertEqual("mvp-01-backend", selected["id"])
        self.assertEqual(str(ACTIVE_SPEC.relative_to(ROOT)), selected["specPath"])
        return (
            selected["phase"],
            (SPEC_ROOT / "umbrella_spec_melliatlas.md").read_text(encoding="utf-8"),
            ACTIVE_SPEC.read_text(encoding="utf-8"),
            ACTIVE_PLAN.read_text(encoding="utf-8"),
            (SPEC_ROOT / "README.md").read_text(encoding="utf-8"),
        )

    def test_active_workstream_has_consistent_approval_and_pending_acceptance(self) -> None:
        self.assertEqual([], authorization_errors(*self._inputs()))

    def test_unauthorized_spec_mutation_is_rejected(self) -> None:
        phase, umbrella, spec, plan, index = self._inputs()
        changed = spec.replace(
            "**Implementation authorization:** Active workstream authorized",
            "**Implementation authorization:** none",
            1,
        )
        self.assertIn(
            "sub-spec: implementation authorization conflicts with checkpoint",
            authorization_errors(phase, umbrella, changed, plan, index),
        )

    def test_premature_acceptance_is_rejected(self) -> None:
        phase, umbrella, spec, plan, index = self._inputs()
        changed = plan.replace("**Acceptance:** Pending", "**Acceptance:** Accepted", 1)
        self.assertIn(
            "plan: acceptance conflicts with unfinished checkpoint",
            authorization_errors(phase, umbrella, spec, changed, index),
        )

    def test_unapproved_future_workstreams_are_not_implicitly_authorized(self) -> None:
        _, umbrella, _, _, _ = self._inputs()
        self.assertIn("future workstreams remain proposals", umbrella)
        self.assertIn("no `mvp-01` stage acceptance", umbrella.casefold())
        self.assertRegex(umbrella, r"(?m)^\*\*Document status:\*\* Working roadmap")


if __name__ == "__main__":
    unittest.main()
