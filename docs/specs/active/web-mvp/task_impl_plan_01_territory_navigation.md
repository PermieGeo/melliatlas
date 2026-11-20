# WEB-MVP-T01 — Implementation Plan (Task)

- **Requirements:** [task](task_01_territory_navigation.md); [normative Web sub-spec](subspec.md).
- **Partition to change:** `frontend` only.
- **Acceptance IDs:** `WEB-MVP-T01-A01`, `WEB-MVP-T01-A02`.
- **Implementation:** advisory; do not infer authorization or acceptance from this plan.

## Read scope

web/src/{App,components/WorkspaceHeader,components/ReferenceControls,components/MapPanel,hooks/useTerritoryReference,geo/territoryPreference}.tsx or .ts as applicable; web/src/api/{client,types,contract.md}; backend/src/melliatlas/territories/{api.py,contract.md}; backend/src/melliatlas/api/contract.md. Existing paths must be checked before editing; dependency modules are read through public contracts.

## Proposed change scope

web/src/App.tsx; web/src/components/{WorkspaceHeader,ReferenceControls,MapPanel}.tsx; web/src/hooks/useTerritoryReference.ts; web/src/geo/territoryPreference.ts; web/src/i18n.ts; web/src/styles.css. Path descriptions are candidates, not claims of new implemented files. Exclude all other partitions.

## Public boundaries and failure handling

Consume only the documented territory API; server geometry and provider identifiers are not frontend responsibilities. Surface invalid inputs, unavailable dependencies and canceled or stale requests explicitly. Do not duplicate source-of-truth wire declarations in this plan.

## Deferred E2E and test inventory

| Existing/proposed test path | Independent oracle / execution note |
| --- | --- |
| `web/e2e/workspace.spec.ts` | Region navigation with a real browser, missing-reference response, keyboard and tile failure; extend only during the separate tests partition task. |
| `tests/e2e/browser/navigation.spec.ts` | Proposed additional E2E if the tests partition is consolidated; do not create in this frontend task. |

This is an implementation task on the shared sub-spec feature branch: do **not run or edit tests**, including the E2E scenarios listed above. Treat the inventory as proposed independent oracles for final test preparation in [`WEB-MVP-T09`](task_09_manual_e2e.md) and execution after review in [`WEB-MVP-T10`](task_10_test_suite_review.md). Report `NOT RUN — deferred until sub-spec completion`; use no `CHK` or per-task merge.
