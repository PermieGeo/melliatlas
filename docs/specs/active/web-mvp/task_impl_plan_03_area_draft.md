# WEB-PLACE-01 — Implementation Plan (Task)

- **Requirements:** [task](task_03_area_draft.md); [normative Web sub-spec](subspec.md).
- **Partition to change:** `frontend` only.
- **Acceptance IDs:** `WEB-PLACE-01-A01`, `WEB-PLACE-01-A02`, `WEB-PLACE-01-A03`.
- **Implementation:** advisory; do not infer authorization or acceptance from this plan.

## Read scope

web/src/{App.tsx,components/AreaDraftPanel.tsx,components/MapPanel.tsx,hooks/useAreaDraft.ts,hooks/useAreaDistrictBoundary.ts,geo/analysisDraft.ts,api/{client,types,validation}.ts,api/contract.md}; backend/src/melliatlas/geography/contract.md; backend/src/melliatlas/territories/contract.md. Existing paths must be checked before editing; dependency modules are read through public contracts.

## Proposed change scope

web/src/App.tsx; web/src/components/{AreaDraftPanel,MapPanel}.tsx; web/src/hooks/{useAreaDraft,useAreaDistrictBoundary}.ts; web/src/geo/analysisDraft.ts; web/src/i18n.ts; web/src/styles.css. Path descriptions are candidates, not claims of new implemented files. Exclude all other partitions.

## Public boundaries and failure handling

Only consume `/territories/intersecting-districts` and public district geometry reads; positive-area spatial intersection and completeness are server responsibilities. Surface invalid inputs, unavailable dependencies and canceled or stale requests explicitly. Do not duplicate source-of-truth wire declarations in this plan.

## Deferred E2E and test inventory

| Existing/proposed test path | Independent oracle / execution note |
| --- | --- |
| `web/e2e/workspace.spec.ts` | Draft creation, dimensions, geographic edge handling, server-backed intersection and stale-request behavior in manual browser E2E. |
| `backend/tests/contract/test_area_district_http.py` | Existing contract shape; use it for read-only context, do not edit in this frontend task. |

This is an implementation task on the shared sub-spec feature branch: do **not run or edit tests**, including the E2E scenarios listed above. Treat the inventory as proposed independent oracles for final test preparation in [`WEB-MVP-T09`](task_09_manual_e2e.md) and execution after review in [`WEB-MVP-T10`](task_10_test_suite_review.md). Report `NOT RUN — deferred until sub-spec completion`; use no `CHK` or per-task merge.
