# MVP Development Workflow — Task and Snapshot Isolation

## Scope and source of truth

The selected Web workstream is [MVP-01 Web](specs/active/web-mvp/subspec.md). Its numbered flat task pairs carry bounded implementation instructions. The [backend MVP workstream](specs/active/subspecs/subspec-01-backend-planning.md) is paused; no new backend task is selected by this document. The current code, typed public APIs and capability contracts establish implemented behavior; specifications establish requirements, not implementation proof.

This process changes **how work is delivered**, not the accepted product scope, runtime source access, licensing, privacy model or `apatch` safety contracts.

## Four concatenated source partitions

Future repository snapshots must provide four independently addressable concatenations with the same Git baseline metadata, a tracked-path manifest and stable `=== FILE` delimiters. A manifest states the part owning each path; no path is emitted into two parts. Content omitted by size filtering is explicitly marked and fetched before editing. Each snapshot records `git_commit`, branch, dirty status and generation timestamp. An incomplete or inconsistent source set cannot authorize guessing.

| Partition | Owned paths and examples | Boundary |
| --- | --- | --- |
| `frontend` | `web/src/`, `web/index.html`, `web/package.json`, `web/tsconfig.json`, `web/vite.config.ts`, web-only runtime configuration and styles | Production browser application, not tests |
| `backend` | `backend/src/`, `backend/migrations/`, `backend/scripts/`, `backend/pyproject.toml`, runtime/reference assets | Production Python service and provider adapters, not tests |
| `tests` | `web/tests/`, `web/e2e/`, `web/playwright.config.ts`, `backend/tests/`, root `tests/`, test fixtures and `run-tests.sh` | Independent test code and check-runner wiring, even when physically inside `web/` or `backend/` |
| `docs` | `docs/`, root `README.md`, `web/README.md`, `backend/README.md`, root/nested `AGENTS.md`, documentation-only metadata | Normative specs, task plans, user/developer documentation |

Files not yet classified (for example, shared automation or config scripts) require an explicit ownership decision in the task plan before being edited. Do not invent extra snapshot parts to avoid choosing an owner. A cross-part source dependency may be read from another part, but the patch changes only its assigned part. Use `api.py`, `contract.md`, typed DTOs and OpenAPI rather than all internal source for dependent capabilities. An API change must be a `backend` task first and a separate `frontend` consumer task next; independent `tests` tasks validate the integrated result.

**Compatibility phase:** Existing repository documentation/SDD unit tests still assert the prior Web sub-spec and selected-task paths; they will need review and path reconciliation in the `tests` partition before the full canonical `CHK` can pass. This is a known migration dependency, not a green check or authorization to weaken their behavior. The existing single concatenation remains the verified baseline until four complete, matching part snapshots are provided. Its subsequent incremental overlays, in creation order, form the current virtual project image. A new complete split baseline replaces that chain only after manifests and identity are checked. No file is silently copied from an unrelated older snapshot.

## One feature branch per sub-spec

Each active sub-spec has exactly **one feature branch** for its entire task series, including implementation, testing, repair and publication. Select the branch for the sub-spec once on a clean, synchronized base. Every later partition-scoped ZIP is an incremental `followup=true` overlay on that same unfinished branch; it does not start a new branch and does not merge a task into `main`. Archive creation is not proof of application. The current external `apatch` cannot commit without `CHK`, so changes stay uncommitted in the working tree until the final gate; check `STS` and the actual branch before each handoff. Do not assume an earlier feature branch remains unfinished after a merge or an interrupted operation.

## Task workflow and final gate

1. Select one sub-spec and a task/plan pair in `STATE.json`; confirm its single change partition and the developer's authorization. The sub-spec branch is created only once; tasks do not each receive a new feature branch.
2. Read the selected task/plan, normative anchors, owning implementation and necessary external public contracts. Deliver each production task as an incremental one-partition `apatch` ZIP on the same branch. Keep requirements, failure oracles and reviewable changes visible.
3. During **all implementation tasks**, apply/format only (`APL,FMT,STS` with `followup=true` after the first `APL,BRN,FMT,STS`). Inspect the formatter result for unintended edits outside the task partition; stop and reconcile them before proceeding. Do not run unit, contract, architecture, UI, E2E or integration tests, either manually or through `CHK`. Do not modify tests as part of a production task. Record checks as `NOT RUN — deferred to sub-spec completion` rather than PASS.
4. After **all implementation tasks** of the sub-spec are delivered, begin the dedicated **final test and verification phase**. First, in the `tests` partition, create/adjust browser/Playwright, Python endpoint and integration E2E coverage against independent behavioral oracles; no test execution yet. Review retained ordinary unit/contract/architecture tests, remove only objectively obsolete tests with rationale and generate missing cases. Keep test code in tests-only ZIPs.
5. After test preparation and independent review, run the complete required suite on the combined feature-branch image: unit, contract and architecture tests; real ASGI endpoint E2E; browser/UI Playwright E2E; DB/integration tests for promised persistence/behavior; and format/lint/strict type/build checks. Manually invoked E2E checks are explicit prerequisites; their results do not substitute for canonical `CHK`. Record environment, fixtures, data provenance, commands and actual outcomes.
6. On **any failure or missing required environment**, block the merge. Repair either production code or test infrastructure in its owning partition on the **same branch** using a new follow-up PATCH, then repeat affected checks and the entire final gate before acceptance. Never change a legitimate oracle to make an implementation pass. External live-provider access or scientifically unverified conclusions cannot be promoted to success by mocks.
7. When all required manual suites are PASS and the canonical `CHK` passes on the final bytes, obtain developer review/approval and only then `CMT`, followed by authorized push, PR, merge into `main` and synchronization. An accepted task is not an independent merge. `STATE.json` acceptance and archival remain explicit developer decisions, never implicit consequences of a ZIP or green test run.

## Final-phase E2E strategy

**Browser:** use existing Playwright through `cd web && npm run test:e2e` after browser dependencies are installed. Existing `web/e2e/workspace.spec.ts` intercepts API requests and is useful for UI state validation; it does **not** prove running backend endpoints, PostGIS persistence or live Saturn availability. At the end of the sub-spec, the tests task should add cases for settlement/coordinate search, area/district preview, date persistence, visible request progress, missing provider mapping, stale requests and privacy-sensitive URL behavior.

**Backend endpoints:** use Python `pytest` and typed `httpx.AsyncClient`/`ASGITransport` against the real FastAPI app and full routing/composition. Use a dedicated `backend/tests/e2e/` suite (proposed, not currently implemented) with controlled provider fakes and disposable PostGIS where required. Exercise real HTTP status and response schema for valid, invalid, unsupported-country, missing-reference and unavailable-provider requests. Do not mock the router under test, and distinguish service-in-process E2E from externally deployed HTTP checks. No default E2E test should call live Saturn, leak coordinates or write production data.

**Current state:** Playwright dependency and a mocked-browser test exist. There is no separate accepted end-to-end Python endpoint runner or verified browser-to-live-Saturn-to-DB flow. Test authoring is reserved for final-phase `WEB-MVP-T09`; execution of all required suites occurs only in final-phase `WEB-MVP-T10` after test review. Nothing is run during implementation tasks.

## Fast `apatch` stage policy

The `apatch` utility is an external guarded handoff mechanism, not MelliAtlas's test runner. Its supported `CMT` requires fresh successful `CHK` evidence. Consequently the sub-spec implementation cycle accumulates uncommitted changes on **one** feature branch; it **cannot produce a checked/committed/merged task PATCH through a no-CHK sequence**.

After checking current `STS` and branch/registry state, and only with configured `FMT`, use the first command **once per sub-spec**:

```sh
apatch <new-zip-stem> opSeq=APL,BRN,FMT,STS skipApproves=true
```

For **every later task, final test-authoring ZIP and repair** on that same verified unfinished feature branch:

```sh
apatch <new-zip-stem> opSeq=APL,FMT,STS followup=true skipApproves=true
```

These are templates, not commands to run with literal placeholders. Do not replay `APL` after a failed check/format; use `STS` to determine resumption. No tests (including manual E2E) run while implementation or final test-authoring tasks are in progress. Avoid `CMT,PSH,PR,MRG,SYN` until all required suites pass and a developer authorizes the gate. The ignored `.apatch/config.yaml` is user-owned; never overwrite it in an overlay.

At the end of the **sub-spec**, review the canonical check selection and output, run all manual UI/E2E/integration suites and `CHK` explicitly on the final snapshot, and only then choose `CMT` and authorized `PSH,PR,MRG,SYN,STS`. Tests and `CHK` must be repeated if edits invalidate the results. Any demand to commit **without** `CHK` requires a separately reviewed change to the external `apatch` utility, not a hidden script/config workaround.
