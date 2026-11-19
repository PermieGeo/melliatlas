# WEB-MVP-T07 — Owner-scoped saved-place API activation (Task)

- **Task ID:** `WEB-MVP-T07`.
- **Workstream:** [MVP-01 Web](subspec.md).
- **Status:** BLOCKED — external ownership/security and real database evidence pending.
- **Partition:** `backend` — one change partition per task/PATCH.
- **Requirements:** `MVP01-WEB-R12; PLACE-A03, PLACE-A04, PLACE-A05` (existing normative IDs; no new approval implied).
- **Dependencies:** WEB-PLACE-01 and explicit developer approval.
- **Implementation plan:** [paired plan](task_impl_plan_07_saved_places_service.md).
- **Authorization:** only previously approved W01 work is authorized; all new gated behavior needs explicit developer approval.
- **Acceptance:** PENDING.

## Required outcome

Persist named private places and their validated WGS84 bbox through an explicitly authorized, owner-isolated FastAPI service that survives independent process/database sessions.

## Constraints

Review ownership/authentication/CSRF/loopback limitation, create/update/read/list/delete transport DTOs, concurrency and revision rules before route activation. Reuse prepared place values, migration and PostGIS adapter only after real disposable-DB verification.

## Non-goals

No frontend state or tests changed in this task; no public unauthenticated private-location listing or data synchronization across devices.

## Acceptance oracles

- **WEB-MVP-T07-A01:** Server rejects missing/other-owner access, invalid regions, invalid rectangles and revision conflicts without exposing private coordinates.
- **WEB-MVP-T07-A02:** Named place create/list/update/delete/reopen persists via a real PostGIS session; missing ADM2 coverage remains explicit.
