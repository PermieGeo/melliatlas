# HTTP API Contract

**Public Python interfaces:** `melliatlas.api.app.create_app`, `melliatlas.api.app.AppSettings`, and `melliatlas.api.public.HealthResponse`.

## Implemented in MVP-01 backend step 1

- `create_app(settings=...)` constructs an independent FastAPI instance without database or provider I/O. The settings object is immutable and can be replaced in tests.
- `GET /health` returns HTTP 200 with `{"status":"ok"}`. It establishes process responsiveness only, not data-source, database, or geographic readiness.
- `GET /openapi.json` serves OpenAPI metadata and a `HealthResponse` schema. `/docs` provides the framework's interactive specification view.
- `melliatlas.main:app` is the ASGI entry point. Importing it must not initiate network calls or database connections.

## Deferred to later backend steps

Versioned `/api/v1/` territory, source and investigation routes, domain-specific errors, dependency injection for their ports, persistence, and lifecycle ownership. No completed MVP-01 API acceptance criterion is claimed by this bootstrap.

## Dependency boundary

The API module may use FastAPI and Pydantic. Domain modules must not depend on HTTP types or import this module. Additional API DTOs must be defined before implementing their routes.
