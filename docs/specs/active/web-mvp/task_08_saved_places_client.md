# WEB-MVP-T08 — Saved-place selection and editing UI (Task)

- **Task ID:** `WEB-MVP-T08`.
- **Workstream:** [MVP-01 Web](subspec.md).
- **Status:** BLOCKED — requires T07 approved and verified API.
- **Partition:** `frontend` — one change partition per task/PATCH.
- **Requirements:** `MVP01-WEB-R08, R12; PLACE-A03, PLACE-A05` (existing normative IDs; no new approval implied).
- **Dependencies:** WEB-MVP-T07.
- **Implementation plan:** [paired plan](task_impl_plan_08_saved_places_client.md).
- **Authorization:** only previously approved W01 work is authorized; all new gated behavior needs explicit developer approval.
- **Acceptance:** PENDING.

## Required outcome

The beekeeper can name, save, select, rename, delete and reopen their own places while preserving consistent map/rectangle state and visible write failure feedback.

## Constraints

Use only approved owner-scoped service DTOs. Failed writes must not appear persisted; reset state on account/region changes and stale responses. Never store private places in URLs or localStorage as a substitute for the service.

## Non-goals

No backend API or DB edits, new authentication design, offline sync, or E2E test edits in this task.

## Acceptance oracles

- **WEB-MVP-T08-A01:** Saved place create/update/delete is explicit and reflected only after server confirmation; canceled edits roll back visually.
- **WEB-MVP-T08-A02:** Reload/reselect shows the server-owned bbox and keeps out-of-region or stale responses from replacing the active selection.
