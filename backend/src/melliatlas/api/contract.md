# HTTP API Contract

**Public Python interfaces:** `melliatlas.api.app.create_app`, `melliatlas.api.app.AppSettings`, `melliatlas.api.public.HealthResponse`, and versioned territory endpoints.

## Implemented

- `create_app(settings=..., territories=...)` constructs an independent FastAPI application without network calls or implicit database connections. The territory catalog is injected through its public `TerritoryCatalog` protocol; omitting it leaves protected reference reads unavailable.
- `GET /health` returns HTTP 200 and `{"status":"ok"}`. It measures process responsiveness, not readiness of references or databases.
- `GET /openapi.json` exposes the response models and enums; `/docs` provides the framework API viewer.
- `GET /api/v1/territories/countries` lists supported country codes RU/BY, **not** claims of loaded boundary data.
- `GET /api/v1/territories/regions?country=RU|BY` returns typed first-order catalog entries when a validated reference has been injected.
- `GET /api/v1/territories/districts?region_id=...` returns the complete supported pilot district catalog or an explicit unsupported-depth error.
- `GET /api/v1/territories/{territory_id}` returns one canonical territory.
- `GET /api/v1/territories/geometry/{territory_id}` returns an available WGS84 GeoJSON geometry, reference ID, and coordinate system.

## Error semantics

Public domain errors have the envelope `{"error":{"code":"...","message":"..."}}`. Missing catalog -> `503/TERRITORY_REFERENCE_UNAVAILABLE`; unknown territory -> `404/TERRITORY_NOT_FOUND`; missing geometry -> `404/TERRITORY_GEOMETRY_MISSING`; unsupported districts -> `409/DISTRICT_COVERAGE_UNSUPPORTED`; malformed input -> `422/INVALID_REQUEST`. An unavailable catalog is **never** represented as a successfully loaded empty catalog.

## Deferred

Full versioned investigation/source endpoints, source provenance DTOs, PostGIS repositories and migrations, and durable server-side job processing remain deferred to later implementation-plan steps. The initial backend stages do not meet full `MVP01-BE-A01` or the browser MVP acceptance gate.
