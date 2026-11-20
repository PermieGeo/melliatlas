# WEB-MVP-T10 — Implementation Plan (Task)

- **Requirements:** [task](task_10_test_suite_review.md); [normative Web sub-spec](subspec.md).
- **Partition to change:** `tests` only.
- **Acceptance IDs:** `WEB-MVP-T10-A01`, `WEB-MVP-T10-A02`, `WEB-MVP-T10-A03`.
- **Implementation:** advisory; do not infer authorization or acceptance from this plan.

## Read scope

tests/test_documentation.py; tests/test_selected_web_task.py; tests/test_web_workstream.py; tests/test_feature_traceability.py; tests/test_sdd_authorization.py; tests/test_contract_consistency.py; backend/tests/; web/tests/; web/e2e/; run-tests.sh; web/package.json; backend/pyproject.toml; docs/TESTS.md. Existing paths must be checked before editing; dependency modules are read through public contracts.

## Proposed change scope

tests/ (including old Web path-assumption tests); backend/tests/; web/tests/; web/e2e/; run-tests.sh only if assigned to the tests partition and explicitly authorized. Path descriptions are candidates, not claims of new implemented files. Exclude all other partitions.

## Public boundaries and failure handling

This is the **only test-execution phase** of the sub-spec. Review and adjust test oracles first, then run required unit/contract/architecture, Playwright UI/E2E, real-ASGI endpoint and disposable-DB integration suites. Run canonical `CHK` after test review; `apatch` commit safety remains unchanged. Any missing required suite or failing check blocks publication. Repair work uses new partition-scoped follow-up ZIPs on the same feature branch before rerunning the complete final gate. Surface invalid inputs, unavailable dependencies and canceled or stale requests explicitly. Do not duplicate source-of-truth wire declarations in this plan.

## Deferred E2E and test inventory

| Existing/proposed test path | Independent oracle / execution note |
| --- | --- |
| `tests/test_selected_web_task.py`, `tests/test_web_workstream.py`, `tests/test_documentation.py` | Update verified old canonical path assumptions for the flat Web task layout without weakening selection or authorization oracles. |
| `tests/test_check_runners.py` | Verify canonical suite wiring and no silent omissions. |
| `backend/tests/architecture/test_module_boundaries.py` | Review current architecture constraint enforcement without auto-relaxing. |
| `web/e2e/workspace.spec.ts` | Execute browser/UI Playwright suite; intercepted API tests are not proof of live backend responses. |
| `backend/tests/e2e/*.py` | Execute reviewed real-ASGI endpoint E2E cases; use disposable PostGIS for integration where promised. |

After T09 and independent test review, execute all required manual E2E/UI/integration suites and the full canonical `CHK` against the final feature-branch content. Record exact commands/results. Repairs may touch other partitions only through their own separately scoped tasks and ZIPs on the same branch; all affected and final-gate checks must then be repeated. Only a fully green gate permits developer-approved `CMT`, PR and merge into `main`.
