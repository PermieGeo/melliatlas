# WEB-MVP-T05 — Synchronized evidence and seasonal timeline (Task)

- **Task ID:** `WEB-MVP-T05`.
- **Workstream:** [MVP-01 Web](subspec.md).
- **Status:** PARTIAL — existing visualization; acceptance pending.
- **Partition:** `frontend` — one change partition per task/PATCH.
- **Requirements:** `MVP01-WEB-R05, R06, R07, R08` (existing normative IDs; no new approval implied).
- **Dependencies:** WEB-MVP-T04.
- **Implementation plan:** [paired plan](task_impl_plan_05_evidence_timeline.md).
- **Authorization:** only previously approved W01 work is authorized; all new gated behavior needs explicit developer approval.
- **Acceptance:** PENDING.

## Required outcome

The currently selected stop has one map/timeline/evidence identity, with date windows, distinct reported treatment claims, fictional ecology decisions and explicit uncertainty.

## Constraints

Never infer real spraying or safety from fictional rules, proximity, absence of records or an empty provider page. Keep full attribution and visible access to results without basemap tiles.

## Non-goals

No numeric hazard/drift model, source acquisition, real-world optimizer, or new backend evidence semantics.

## Acceptance oracles

- **WEB-MVP-T05-A01:** Choosing a stop from map or timeline selects the same evidence record and explains excluded/replaced candidates.
- **WEB-MVP-T05-A02:** Source-report, model/fixture, precaution and unknown states remain visually and textually distinguishable even without map tiles.
