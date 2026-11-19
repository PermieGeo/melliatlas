# WEB-PLACE-01 — Unsaved bbox draft and district preview (Task)

- **Task ID:** `WEB-PLACE-01`.
- **Workstream:** [MVP-01 Web](subspec.md).
- **Status:** PARTIAL — unsaved draft exists; acceptance pending.
- **Partition:** `frontend` — one change partition per task/PATCH.
- **Requirements:** `MVP01-WEB-R02, R08, R12; PLACE-A01, PLACE-A02, PLACE-A05` (existing normative IDs; no new approval implied).
- **Dependencies:** WEB-MVP-T01, WEB-MVP-T02.
- **Implementation plan:** [paired plan](task_impl_plan_03_area_draft.md).
- **Authorization:** only previously approved W01 work is authorized; all new gated behavior needs explicit developer approval.
- **Acceptance:** PENDING.

## Required outcome

A validated map point creates one editable unsaved 15 × 15 km draft rectangle, resizable up to 30 × 30 km and showing known overlapping ADM2 districts without claiming complete coverage.

## Constraints

Keep read-only bbox lookup and selected district outline separate from source collection; a map click during edit moves one draft, but must not write a saved place. Dimension edits are accessible without drag controls, and incoming responses are discarded after country/region changes or cancellation. No draft coordinates enter browser URL or persisted preferences.

## Non-goals

No saved-place REST CRUD, user ownership, database migration, full regional map layers, or analysis of all bbox districts in Saturn.

## Acceptance oracles

- **WEB-PLACE-01-A01:** Map click and coordinate search create/move the same 15 × 15 km draft; width and height never exceed 30 km and invalid geographic edges are rejected.
- **WEB-PLACE-01-A02:** The backend-returned district intersection list and coverage state are displayed without mistaking missing data for zero districts.
- **WEB-PLACE-01-A03:** Canceled/stale changes and region switching do not leak a previous rectangle or persist private coordinates.
