# WEB-MVP-T09 — Final-phase browser and backend endpoint E2E preparation (Task)

- **Task ID:** `WEB-MVP-T09`.
- **Workstream:** [MVP-01 Web](subspec.md).
- **Status:** PLANNED — end-of-sub-spec tests-only preparation, not execution.
- **Partition:** `tests` — one change partition per task/PATCH.
- **Requirements:** `MVP01-WEB-R01–R13; MVP01-WEB-A01–A11; PLACE-A01–A05 where functionality exists` (existing normative IDs; no new approval implied).
- **Dependencies:** all WEB-MVP-T01–T08 implementation tasks delivered on the same sub-spec branch; planned endpoint and browser oracles available.
- **Implementation plan:** [paired plan](task_impl_plan_09_manual_e2e.md).
- **Authorization:** only previously approved W01 work is authorized; all new gated behavior needs explicit developer approval.
- **Acceptance:** PENDING.

## Required outcome

Prepare or update Playwright browser E2E and Python pytest/httpx endpoint/integration E2E that will later exercise real HTTP/ASGI boundaries, visible UI states, failure handling and privacy. **Do not execute tests in this task**; the independently reviewed final run belongs to `WEB-MVP-T10`.

## Constraints

Keep test fixtures explicit and synthetic only where a scenario requires them. Distinguish intercepted browser UX checks, real FastAPI/ASGI endpoint checks and disposable PostGIS integration. External Saturn/Open-Meteo calls are never required for deterministic E2E and must not be represented as verified live. Review expected responses independently of implementation, and record the execution inventory for T10. No test run or completion claim occurs before T10.

## Non-goals

No production code, public API contracts, feature acceptance or global test runner modifications in this tests task.

## Acceptance oracles

- **WEB-MVP-T09-A01:** Playwright cases are prepared to cover search, bbox, visible analysis progress, error/empty states, reload/date preference, accessibility and map/source attribution with screenshots/traces on failure.
- **WEB-MVP-T09-A02:** Pytest/httpx cases are prepared for real ASGI endpoint status/schema/error validation, RU/BY source gating and coordinates without forbidden upstream I/O.
- **WEB-MVP-T09-A03:** The documented E2E execution inventory identifies setup, required disposable DB fixtures and missing external/DB prerequisites. Execution remains `NOT RUN` pending T10.
