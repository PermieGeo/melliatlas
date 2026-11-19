# WEB-MVP-T08 — Implementation Plan (Task)

- **Requirements:** [task](task_08_saved_places_client.md); [normative Web sub-spec](subspec.md).
- **Partition to change:** `frontend` only.
- **Acceptance IDs:** `WEB-MVP-T08-A01`, `WEB-MVP-T08-A02`.
- **Implementation:** advisory; do not infer authorization or acceptance from this plan.

## Read scope

web/src/{App.tsx,components/AreaDraftPanel.tsx,hooks/useAreaDraft.ts,api/{client,types,validation}.ts,api/contract.md}; backend/src/melliatlas/api/contract.md (T07 verified). Existing paths must be checked before editing; dependency modules are read through public contracts.

## Proposed change scope

web/src/App.tsx; web/src/components/ (new focused saved-place UI); web/src/hooks/ (optional saved-place state); web/src/api/{client,types,validation}.ts; web/src/i18n.ts; web/src/styles.css. Path descriptions are candidates, not claims of new implemented files. Exclude all other partitions.

## Public boundaries and failure handling

UI is a consumer, never a persistence authority; do not bypass server authorization checks. Surface invalid inputs, unavailable dependencies and canceled or stale requests explicitly. Do not duplicate source-of-truth wire declarations in this plan.

## Deferred E2E and test inventory

| Existing/proposed test path | Independent oracle / execution note |
| --- | --- |
| `web/e2e/workspace.spec.ts` | Manual browser persistence/rollback/reopen and private-URL checks; extend in T09 tests task only. |

This is an implementation task on the shared sub-spec feature branch: do **not run or edit tests**, including the E2E scenarios listed above. Treat the inventory as proposed independent oracles for final test preparation in [`WEB-MVP-T09`](task_09_manual_e2e.md) and execution after review in [`WEB-MVP-T10`](task_10_test_suite_review.md). Report `NOT RUN — deferred until sub-spec completion`; use no `CHK` or per-task merge.
