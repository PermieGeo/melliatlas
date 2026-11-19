# WEB-MVP-T10 — End-of-sub-spec test audit and release gate (Task)

- **Task ID:** `WEB-MVP-T10`.
- **Workstream:** [MVP-01 Web](subspec.md).
- **Status:** DEFERRED — final stage after all implementation tasks and T09 preparation are delivered.
- **Partition:** `tests` — one change partition per task/PATCH.
- **Requirements:** `MVP01-WEB-A01–A11 and backend invariants exercised by selected features` (existing normative IDs; no new approval implied).
- **Dependencies:** completed implementation-task deliveries T01–T08 and T09 test preparation, plus an explicit developer decision to begin final verification.
- **Implementation plan:** [paired plan](task_impl_plan_10_test_suite_review.md).
- **Authorization:** only previously approved W01 work is authorized; all new gated behavior needs explicit developer approval.
- **Acceptance:** PENDING.

## Required outcome

Independently review existing unit/contract/architecture, UI E2E, endpoint E2E and integration tests; adjust stale expectations to approved contracts, remove obsolete/duplicate cases with recorded rationale and generate missing valid regressions. **After** test review and generation, execute all required suites, formatting/lint/typecheck/build and canonical `CHK`. Merge into `main` is prohibited until every required test and check passes and the developer approves publication.

## Constraints

Do not weaken valid assertions for green output. Review test behavior independently of generated implementation, including architecture/security/DB assumptions, before deleting or regenerating anything. UI/Playwright, Python real-ASGI endpoint and disposable PostGIS integration are explicit execution gates; intercepted browser mocks do not prove server or database behavior. If a required test cannot run, the sub-spec remains blocked. Fix failures with partition-scoped follow-up ZIPs on the **same feature branch**, then rerun all required suites on the final bytes.

## Non-goals

No production code changes, no direct changes to external apatch utility or its ignored local config in this tests task.

## Acceptance oracles

- **WEB-MVP-T10-A01:** Every retained/adjusted/deleted/generated test has a reviewed behavior owner, rationale and independent oracle; obsolete tests are not deleted without justification.
- **WEB-MVP-T10-A02:** All required unit/contract/architecture, Playwright UI/E2E, real-ASGI endpoint E2E and database/integration suites have recorded successful execution on final code; missing prerequisites are blockers.
- **WEB-MVP-T10-A03:** Read-only canonical `CHK`, strict type/lint/format/build checks and independent manual suites all PASS on final bytes before authorized `CMT` and any PR/merge into `main`.
