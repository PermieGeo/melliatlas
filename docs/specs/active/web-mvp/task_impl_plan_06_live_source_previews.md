# WEB-MVP-T06 — Implementation Plan (Task)

- **Requirements:** [task](task_06_live_source_previews.md); [normative Web sub-spec](subspec.md).
- **Partition to change:** `frontend` only.
- **Acceptance IDs:** `WEB-MVP-T06-A01`, `WEB-MVP-T06-A02`.
- **Implementation:** advisory; do not infer authorization or acceptance from this plan.

## Read scope

web/src/components/{LiveAreaAnalysis,SaturnPanel,WeatherPanel,FieldHelp}.tsx; web/src/geo/sourceDatePreference.ts; web/src/api/{client,types,contract.md}; backend/src/melliatlas/sources/contract.md; backend/src/melliatlas/api/contract.md. Existing paths must be checked before editing; dependency modules are read through public contracts.

## Proposed change scope

web/src/components/{LiveAreaAnalysis,SaturnPanel,WeatherPanel,FieldHelp}.tsx; web/src/geo/sourceDatePreference.ts; web/src/App.tsx; web/src/i18n.ts; web/src/styles.css. Path descriptions are candidates, not claims of new implemented files. Exclude all other partitions.

## Public boundaries and failure handling

Use only the public source/weather APIs. No frontend access to upstream Saturn credentials or internal Python provider clients. Surface invalid inputs, unavailable dependencies and canceled or stale requests explicitly. Do not duplicate source-of-truth wire declarations in this plan.

## Deferred E2E and test inventory

| Existing/proposed test path | Independent oracle / execution note |
| --- | --- |
| `web/e2e/workspace.spec.ts` | Manual start/progress/empty/error, country/mapping guard and date persistence; separate tests partition task. |
| `backend/tests/contract/test_saturn_district_scope.py` | Existing offline restriction check, not a claim of live provider availability. |

This is an implementation task on the shared sub-spec feature branch: do **not run or edit tests**, including the E2E scenarios listed above. Treat the inventory as proposed independent oracles for final test preparation in [`WEB-MVP-T09`](task_09_manual_e2e.md) and execution after review in [`WEB-MVP-T10`](task_10_test_suite_review.md). Report `NOT RUN — deferred until sub-spec completion`; use no `CHK` or per-task merge.
