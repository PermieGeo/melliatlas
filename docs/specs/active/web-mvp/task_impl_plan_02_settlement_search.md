# WEB-MVP-T02 — Implementation Plan (Task)

- **Requirements:** [task](task_02_settlement_search.md); [normative Web sub-spec](subspec.md).
- **Partition to change:** `frontend` only.
- **Acceptance IDs:** `WEB-MVP-T02-A01`, `WEB-MVP-T02-A02`.
- **Implementation:** advisory; do not infer authorization or acceptance from this plan.

## Read scope

web/src/components/{PlaceSearchToolbar,FieldHelp,ReferenceControls}.tsx; web/src/App.tsx; web/src/api/{client,types,validation,contract.md}; backend/src/melliatlas/api/contract.md. Existing paths must be checked before editing; dependency modules are read through public contracts.

## Proposed change scope

web/src/components/{PlaceSearchToolbar,FieldHelp}.tsx; web/src/App.tsx; web/src/i18n.ts; web/src/styles.css; web/src/api/{client,types,validation}.ts only if the existing contract changes. Path descriptions are candidates, not claims of new implemented files. Exclude all other partitions.

## Public boundaries and failure handling

Geocoding transport and coordinates stay behind the typed browser API client; use `POST /api/v1/sources/geocoding/settlements` and `POST /api/v1/territories/resolve-point`. Surface invalid inputs, unavailable dependencies and canceled or stale requests explicitly. Do not duplicate source-of-truth wire declarations in this plan.

## Deferred E2E and test inventory

| Existing/proposed test path | Independent oracle / execution note |
| --- | --- |
| `web/e2e/workspace.spec.ts` | Manual search with names/coordinates, no input-triggered network, verified region, stale responses. |
| `backend/tests/contract/test_settlement_search_http.py` | Existing offline contract baseline, not to be changed in this frontend task. |

This is an implementation task on the shared sub-spec feature branch: do **not run or edit tests**, including the E2E scenarios listed above. Treat the inventory as proposed independent oracles for final test preparation in [`WEB-MVP-T09`](task_09_manual_e2e.md) and execution after review in [`WEB-MVP-T10`](task_10_test_suite_review.md). Report `NOT RUN — deferred until sub-spec completion`; use no `CHK` or per-task merge.
