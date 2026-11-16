# Backend AGENTS.md

Extends `../AGENTS.md`. Applies to Python backend code and tests.

## Architecture and contracts
- Keep domain modules independent of FastAPI, SQL/ORM, and HTTP clients. Keep HTTP routes responsible for validation, serialization, orchestration, and error mapping, not domain policy.
- Use capability-owned, typed public interfaces. Import peer capabilities only through their public API or explicitly approved facade.
- Inject I/O clients and repositories at composition boundaries. Add adapters, protocols, and indirection only when required by actual consumers or testing seams.
- Keep provider HTTP transport, parsing and source-specific routes under provider-owned modules; cross-provider routing may depend only on public capability ports.
- Keep `api.py` for public types and `Protocol` ports; use named feature modules for algorithms, adapters and stateful implementations. Export concrete implementations through explicit package facades, never through generic `implementation.py` buckets. Introduce a `Protocol` only for a real replaceable dependency or callback, not every pure function.
- Record non-obvious public invariants, failure modes, and ownership in the relevant module contract; do not duplicate type declarations as prose.

## Python and integrations
- Type public functions and run strict Pyright. Validate untrusted data at I/O boundaries with Pydantic or equivalent explicit parsing.
- Preserve meaningful exception causes internally and sanitize external error responses. Do not silence type warnings or swallow failures.
- Pass settings explicitly; keep secrets and environment loading out of domain modules. Differentiate protocol/geometric invariants from operator settings; only operational values belong in configuration or persistence.
- Represent repeated source failures and user-visible domain warnings with stable typed codes; never embed translated UI prose in domain decisions.
- Do not block the async event loop with synchronous external I/O. Close owned resources, respect cancellation, and bound external calls with timeouts.
- For persistence, use parameterized queries, explicit transaction boundaries, reviewable migrations, and tests for rollback/idempotency. In-process tasks are not durable across restarts.

## Verification
- Use deterministic pytest unit and contract tests, covering invalid inputs and failure paths. Use a real database to establish database, migration, or PostGIS correctness.
- Keep architecture constraints executable; test forbidden imports independently of ordinary functional tests.
- Run configured Ruff, Pyright, pytest, architecture, and package checks. Report unavailable checks rather than silently skipping them.
