# WEB-MVP-T07 — Implementation Plan (Task)

- **Requirements:** [task](task_07_saved_places_service.md); [normative Web sub-spec](subspec.md).
- **Partition to change:** `backend` only.
- **Acceptance IDs:** `WEB-MVP-T07-A01`, `WEB-MVP-T07-A02`.
- **Implementation:** advisory; do not infer authorization or acceptance from this plan.

## Read scope

backend/src/melliatlas/places/{api.py,contract.md,validation.py}; backend/src/melliatlas/persistence/{api.py,contract.md,saved_places.py}; backend/src/melliatlas/api/{app.py,composition.py,contract.md}; backend/migrations/0008_saved_places.sql; web/src/api/contract.md (read-only). Existing paths must be checked before editing; dependency modules are read through public contracts.

## Proposed change scope

backend/src/melliatlas/api/ (new bounded places router and composition); backend/src/melliatlas/places/; backend/src/melliatlas/persistence/ only if reviewed contracts require; backend/migrations/ only after approval. Path descriptions are candidates, not claims of new implemented files. Exclude all other partitions.

## Public boundaries and failure handling

Place ownership stays on the backend; no browser localStorage replacement, no region-database access from frontend; source API and place API remain distinct. Surface invalid inputs, unavailable dependencies and canceled or stale requests explicitly. Do not duplicate source-of-truth wire declarations in this plan.

## Deferred E2E and test inventory

| Existing/proposed test path | Independent oracle / execution note |
| --- | --- |
| `tests/e2e/backend/test_saved_places_http.py` | Proposed Python/httpx real-ASGI/PostGIS E2E, to be written only in T09. |
| `backend/tests/unit/test_saved_place_repository.py` | Existing test retained but not run in fast MVP loop; reviewed at T10. |

This is an implementation task on the shared sub-spec feature branch: do **not run or edit tests**, including the E2E scenarios listed above. Treat the inventory as proposed independent oracles for final test preparation in [`WEB-MVP-T09`](task_09_manual_e2e.md) and execution after review in [`WEB-MVP-T10`](task_10_test_suite_review.md). Report `NOT RUN — deferred until sub-spec completion`; use no `CHK` or per-task merge.
