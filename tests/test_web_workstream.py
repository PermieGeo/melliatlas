"""Enforce W01 Web selection without inventing feature acceptance."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/specs/active/subspecs/subspec-01-web-mvp.md"
PLAN = ROOT / "docs/specs/active/subspecs/subspec-01-web-mvp_implementation_plan.md"


def web_selection_errors(state: dict[str, object], spec: str, plan: str) -> list[str]:
    errors: list[str] = []
    if state.get("selectedWorkstreamId") != "mvp-01-web":
        errors.append("Web W01 must be the selected workstream")
    workstreams = state.get("workstreams")
    if not isinstance(workstreams, list):
        return ["Missing workstream list"]
    selected = [item for item in workstreams if isinstance(item, dict) and item.get("id") == "mvp-01-web"]
    if len(selected) != 1 or selected[0].get("phase") != "READY_FOR_IMPLEMENTATION":
        errors.append("Web implementation checkpoint missing")
    for label, text in (("spec", spec), ("plan", plan)):
        for field in (
            "**Requirements approval:** APPROVED",
            "**Implementation authorization:** AUTHORIZED",
            "**Acceptance:** PENDING",
        ):
            if field not in text:
                errors.append(f"{label}: missing {field}")
    if state.get("featureAcceptances") != []:
        errors.append("Unapproved acceptance recorded")
    return errors


class WebAuthorizationTests(unittest.TestCase):
    def _inputs(self) -> tuple[dict[str, object], str, str]:
        return (
            json.loads((ROOT / "docs/specs/STATE.json").read_text(encoding="utf-8")),
            SPEC.read_text(encoding="utf-8"),
            PLAN.read_text(encoding="utf-8"),
        )

    def test_web_implementation_is_selected_but_unaccepted(self) -> None:
        self.assertEqual([], web_selection_errors(*self._inputs()))

    def test_web_authorization_cannot_be_silently_withdrawn(self) -> None:
        state, spec, plan = self._inputs()
        broken = spec.replace("**Implementation authorization:** AUTHORIZED", "**Implementation authorization:** NOT AUTHORIZED")
        self.assertTrue(web_selection_errors(state, broken, plan))

    def test_web_acceptance_is_not_implicit_from_code(self) -> None:
        state, spec, plan = self._inputs()
        broken = plan.replace("**Acceptance:** PENDING", "**Acceptance:** ACCEPTED")
        self.assertTrue(web_selection_errors(state, spec, broken))

    def test_unselected_web_is_not_treated_as_authorized(self) -> None:
        state, spec, plan = self._inputs()
        state["selectedWorkstreamId"] = "mvp-01-backend"
        self.assertTrue(web_selection_errors(state, spec, plan))
