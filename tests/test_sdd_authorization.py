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
    def status(markdown: str, field: str) -> str:
        return _field(markdown, field).split(" — ", maxsplit=1)[0].strip()

    for label, document in (("sub-spec", spec), ("plan", plan)):
        if status(document, "Requirements approval") != "APPROVED":
            errors.append(f"{label}: requirements not approved")
        if status(document, "Implementation authorization") != "AUTHORIZED":
            errors.append(f"{label}: implementation authorization conflicts with checkpoint")
        if status(document, "Acceptance") != "PENDING":
            errors.append(f"{label}: acceptance conflicts with unfinished checkpoint")
    if status(umbrella, "Active authorization") != "AUTHORIZED":
        errors.append("umbrella: active backend authorization missing")
    if status(umbrella, "Acceptance") != "PENDING":
        errors.append("umbrella: whole-stage acceptance must remain pending")
    if status(index, "Requirements approval") != "APPROVED":
        errors.append("index: active backend approval missing")
    if status(index, "Implementation authorization") != "AUTHORIZED":
        errors.append("index: implementation authorization missing")
    if status(index, "Acceptance") != "PENDING":
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
            "**Implementation authorization:** AUTHORIZED — active workstream",
            "**Implementation authorization:** none — active workstream",
            1,
        )
        self.assertIn(
            "sub-spec: implementation authorization conflicts with checkpoint",
            authorization_errors(phase, umbrella, changed, plan, index),
        )

    def test_premature_acceptance_is_rejected(self) -> None:
        phase, umbrella, spec, plan, index = self._inputs()
        changed = plan.replace("**Acceptance:** PENDING", "**Acceptance:** ACCEPTED", 1)
        self.assertIn(
            "plan: acceptance conflicts with unfinished checkpoint",
            authorization_errors(phase, umbrella, spec, changed, index),
        )

    def test_unauthorized_word_is_not_treated_as_authorized(self) -> None:
        phase, umbrella, spec, plan, index = self._inputs()
        changed = spec.replace(
            "**Implementation authorization:** AUTHORIZED — active workstream",
            "**Implementation authorization:** unauthorized — active workstream",
            1,
        )
        self.assertIn(
            "sub-spec: implementation authorization conflicts with checkpoint",
            authorization_errors(phase, umbrella, changed, plan, index),
        )

    def test_unapproved_word_is_not_treated_as_approved(self) -> None:
        phase, umbrella, spec, plan, index = self._inputs()
        changed = spec.replace("**Requirements approval:** APPROVED", "**Requirements approval:** unapproved", 1)
        self.assertIn(
            "sub-spec: requirements not approved",
            authorization_errors(phase, umbrella, changed, plan, index),
        )

    def test_contradictory_pending_acceptance_is_rejected(self) -> None:
        phase, umbrella, spec, plan, index = self._inputs()
        changed = plan.replace("**Acceptance:** PENDING", "**Acceptance:** PENDING; accepted", 1)
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
