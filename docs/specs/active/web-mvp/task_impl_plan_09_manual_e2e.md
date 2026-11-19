# WEB-MVP-T09 — Implementation Plan (Task)

- **Requirements:** [task](task_09_manual_e2e.md); [normative Web sub-spec](subspec.md).
- **Partition to change:** `tests` only.
- **Acceptance IDs:** `WEB-MVP-T09-A01`, `WEB-MVP-T09-A02`, `WEB-MVP-T09-A03`.
- **Implementation:** advisory; do not infer authorization or acceptance from this plan.

## Read scope

web/{playwright.config.ts,e2e/workspace.spec.ts,package.json}; backend/tests/contract/ (as read-only examples); backend/src/melliatlas/api/contract.md; docs/TESTS.md; backend/pyproject.toml. Existing paths must be checked before editing; dependency modules are read through public contracts.

## Proposed change scope

web/e2e/*.spec.ts; backend/tests/e2e/*.py (proposed; classified under tests partition); tests/e2e/ (optional orchestration scripts owned by tests partition). Do not modify web/src, backend/src, runtime configuration or package manifests. Path descriptions are candidates, not claims of new implemented files. Exclude all other partitions.

## Public boundaries and failure handling

E2E tests may cross runtime services as clients, but the patch changes only test files. No changes to production source. Surface invalid inputs, unavailable dependencies and canceled or stale requests explicitly. Do not duplicate source-of-truth wire declarations in this plan.

## Deferred E2E and test inventory

| Existing/proposed test path | Independent oracle / execution note |
| --- | --- |
| `web/e2e/workspace.spec.ts` | Extend or split into browser scenarios and prepare the later `cd web && npm run test:e2e` command; do not run it in T09. |
| `backend/tests/e2e/test_public_http.py` | Prepare Python pytest/httpx real-ASGI endpoint cases, with status/body oracles and no mock of the FastAPI router; defer execution to T10. |
| `backend/tests/e2e/test_source_availability_http.py` | Proposed offline source gating and malformed result E2E, using a fake upstream only at the provider boundary. |

Begin T09 only after all implementation tasks have been delivered on the shared sub-spec feature branch. Prepare test files and execution prerequisites without running them; report **NOT RUN**. The full independent test audit and all suite execution belong exclusively to [`WEB-MVP-T10`](task_10_test_suite_review.md). Do not use `apatch CHK` while preparing tests.
