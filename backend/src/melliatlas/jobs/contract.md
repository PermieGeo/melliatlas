# Investigation Jobs Contract — V01 and V04-03

`InvestigationService` provides `submit`, `get` and `process` operations. `InMemoryInvestigationService` stores immutable snapshot values in a lock-protected mapping per application instance; a new process or app instance has an empty store. A successful `submit` validates the fixed scenario and date window **before** inserting `QUEUED` state. `process` transitions through `RUNNING` to terminal `COMPLETED` or `FAILED` and does not mutate a terminal snapshot again.

`InvestigationOutcomeKind` reports domain suitability separately from execution `InvestigationStatus`. Insufficient fixture evidence is `COMPLETED/INSUFFICIENT_EVIDENCE`, not `FAILED`. Unexpected calculation failures are logged and surfaced only as a sanitized `FAILED` diagnostic. No restart recovery, database transaction, automatic retries, deduplication or cross-worker synchronization is claimed. Production persistence and immutable historical reopening are reserved for V02.

## Optional completed-snapshot persistence (V02 partial)

`CompletedInvestigationStore` is a jobs-owned port for saving and reading terminal `COMPLETED` snapshots. Passing a store to `InMemoryInvestigationService(provider, completed_store=...)` saves a successful completed result before making it observable as `COMPLETED`; storage failures yield `FAILED` with sanitized diagnostics. A fresh service instance can reopen previously saved completed results by UUID through the store. The in-memory statuses `QUEUED`, `RUNNING`, and `FAILED` remain process-local and are lost after restart. Persistence adapters import the jobs public API; jobs never imports persistence. The JSON snapshot codec is internal-to-backend storage, not an HTTP contract or a claim of approved long-term schema evolution.

## Opt-in fictional ecology integration (V04-03 partial)

A supplied `EcologyPlannerFactory` creates a bounded `DeterministicPlanner` for a scenario whose `ecology_zones` tuple is nonempty. The default FastAPI composition supplies the pure synthetic inspector; direct service composition without that collaborator fails with a sanitized `FAILED` snapshot, never a non-screened plan. `jobs` imports `agent` and `planning` public interfaces, not the spatial `analyzers` module or source implementation.

A completed V04-03 snapshot includes the optional typed `ReplanResult` alongside its existing top-level plan, evidence, status, and legacy string trace. `CHECK_LIMIT_REACHED` produces `COMPLETED/INSUFFICIENT_EVIDENCE` with no plan; no viable checked alternative produces `COMPLETED/NO_FEASIBLE_ALTERNATIVE`. Inspector exceptions produce `FAILED` without an actionable or leaked provider exception. The optional JSON replanning payload has typed decoding and cross-checks top-level plan/outcome consistency; historical snapshots lacking it remain readable and are serialized without adding the new key. Fake-store round trips are not real PostGIS verification.
