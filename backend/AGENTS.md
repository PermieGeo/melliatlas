# Backend AGENTS.md

Extends `../AGENTS.md`. Applies to Python code and tests under `backend/`.

## Architecture
- **ALWAYS** keep domain logic independent of FastAPI, SQL/ORM, and external transport clients.
- **ALWAYS** keep routes focused on validation, authorization, orchestration, serialization, and error mapping.
- **ALWAYS** group implementation by capability; expose narrow, typed module interfaces.
- **ALWAYS** inject external clients, repositories, and other I/O dependencies at composition boundaries.
- **NEVER** import across private module boundaries or create implicit infrastructure dependencies.
- **NEVER** introduce a layer, interface, or class hierarchy without a concrete need.

## Python & API
- **ALWAYS** type public signatures and run strict `pyright` checks when configured.
- **ALWAYS** validate untrusted requests, responses, and settings at their boundaries with Pydantic or equivalent explicit schemas.
- **NEVER** use broad `Any`, unchecked casts, or type-checker suppressions to bypass contracts.
- **ALWAYS** centralize environment and secret loading in typed settings; pass configuration explicitly.
- **ALWAYS** use explicit exception types, preserve error causes, and map application errors at the transport boundary.
- **NEVER** block the event loop with synchronous I/O; use asynchronous clients or explicit offloading.
- **ALWAYS** close owned resources, handle cancellation, and bound external I/O with timeouts.

## Persistence & Background Work
- **ALWAYS** isolate database operations and migrations behind owned persistence interfaces.
- **ALWAYS** use parameterized SQL, explicit transaction boundaries, and reviewable migrations.
- **ALWAYS** define retry, idempotency, and rollback behavior when operations can be repeated or interrupted.
- **NEVER** assume in-process tasks are durable; make lifecycle and recovery responsibilities explicit when needed.

## Verification
- **ALWAYS** write deterministic `pytest` tests for changed behavior, invalid inputs, and failure paths.
- **ALWAYS** isolate external dependencies in unit tests; use integration tests for database or framework behavior.
- **NEVER** use mocks as evidence that real SQL, migrations, or runtime integration works.
- **ALWAYS** run configured `ruff`, `pyright`, `pytest`, architecture, and package checks; report unavailable checks.
