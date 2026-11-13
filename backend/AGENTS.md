# Python Backend Rules

Inherits `../AGENTS.md`. Applies to the Python FastAPI application, Engine, Agent, jobs, and storage. See narrower rules under `src/melliatlas/`.

- **Dependency direction:** `api/` validates/translates HTTP; `agent/` decides next actions; `engine/` defines typed execution contracts; `sources/` and `analyzers/` implement registered capabilities; `jobs/` coordinates durable execution; `persistence/` implements storage. No domain behavior in HTTP routes, SQL adapters, or app startup.
- The **Engine has no imports from Agent, FastAPI, PostgreSQL drivers, or concrete providers**. Invert such dependencies through narrow protocols; use explicit constructor/factory injection at composition boundaries. Avoid one interface per class.
- Use typed Python throughout: type all public signatures and return values; design for **pyright strict**, **Ruff**, and **pytest** once configured. Prefer Pydantic for external validation and immutable typed models for internal artifacts; do not pass unconstrained `dict[str, Any]` between capabilities.
- Centralize environment, model selection, provider allowlists, quotas, country profiles, and external URLs in validated configuration; no direct environment reads in domain functions. Never store real credentials in tracked files.
- Separate domain errors from transport errors. Map domain exceptions to stable, sanitized FastAPI responses at the HTTP boundary; preserve diagnostic context internally without logging secrets or precise apiary coordinates.
- Make I/O bounded and cancellation-aware. Do not block async event loops; use appropriate async clients or isolated worker execution. Do not spawn fire-and-forget in-process tasks for durable work.
- The worker and API share application services and contracts, **not HTTP routing state**. Persist job transitions, checkpoints, retries, and idempotency before claiming restart resilience.
- Use additive, reviewed database migrations and parameterized queries; test geospatial CRS/coordinate order, access control, transactions, retries, and restart with real PostGIS where needed.
- Do not add a Python framework, ORM, broker, or LLM framework solely for scaffolding. Select and pin dependencies in the workstream that needs them.
