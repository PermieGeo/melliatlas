# HTTP API Contract

**Public Python interfaces:** `melliatlas.api.app.create_app`, `melliatlas.api.app.AppSettings`, `melliatlas.api.public.HealthResponse`, `ApiErrorCode`, `ErrorResponse`, and versioned territory endpoints.

## Implemented

- `create_app(settings=..., territories=...)` constructs an independent FastAPI application without network calls or implicit database connections. The territory catalog is injected through its public `TerritoryCatalog` protocol; omitting it leaves protected reference reads unavailable unless both local reference paths are explicitly configured in `AppSettings`. A configured ASGI lifespan validates the snapshot and independent inventory before serving; invalid, missing, incomplete or checksum-mismatched inputs fail startup. Mixed explicit `territories` injection and file configuration, or one-sided file configuration, are rejected at composition time.
- `GET /health` returns HTTP 200 and `{"status":"ok"}`. It measures process responsiveness, not readiness of references or databases.
- `GET /openapi.json` exposes success and error response schemas, stable error codes, and applicable `404`, `409`, `422` and `503` statuses; `/docs` provides the framework API viewer.
- `GET /api/v1/territories/countries` lists supported country codes RU/BY, **not** claims of loaded boundary data.
- `GET /api/v1/territories/regions?country=RU|BY` returns typed first-order catalog entries when a validated reference has been injected.
- `GET /api/v1/territories/districts?region_id=...` returns the complete supported pilot district catalog or an explicit unsupported-depth error.
- `GET /api/v1/territories/{territory_id}` returns one canonical territory.
- `GET /api/v1/territories/geometry/{territory_id}` returns an available WGS84 GeoJSON geometry, reference ID, and coordinate system.

## Error semantics

Public domain errors have the typed envelope `{"error":{"code":"...","message":"..."}}` (`ErrorResponse`, `ApiErrorCode`). Missing catalog -> `503/TERRITORY_REFERENCE_UNAVAILABLE`; unknown territory -> `404/TERRITORY_NOT_FOUND`; missing geometry -> `404/TERRITORY_GEOMETRY_MISSING`; unsupported districts -> `409/DISTRICT_COVERAGE_UNSUPPORTED`; malformed input -> `422/INVALID_REQUEST`. The shared FastAPI validation handler returns `422/INVALID_REQUEST` in the same envelope; OpenAPI documents this actual response instead of the framework default validation schema. An unavailable catalog is **never** represented as a successfully loaded empty catalog.

## Deferred

Full versioned investigation/source endpoints, source provenance DTOs, PostGIS repositories and migrations, and durable server-side job processing remain deferred to later implementation-plan steps. The initial backend stages do not meet full `MVP01-BE-A01` or the browser MVP acceptance gate.

## Synthetic investigation API (V01, development-only)

- `create_app(..., investigations=...)` optionally injects an `InvestigationService`; when omitted, each app instance constructs an independent, non-durable `InMemoryInvestigationService` and offline `SyntheticFixtureProvider`. Existing `settings` and `territories` keyword arguments are unchanged.
- `POST /api/v1/investigations` accepts `country`, `territory_id`, `scenario_id`, inclusive `season_start`/`season_end`, and an optional private `starting_point` in `{longitude, latitude}` WGS84 degrees. It returns `202` with a UUID, `QUEUED`, and typed optional result fields. Its background task performs a bounded **in-process** fixture calculation; no durability or restart recovery is promised.
- `GET /api/v1/investigations/{id}` returns a typed snapshot with technical `status`, independent domain `outcome`, optional ordered `plan`, synthetic evidence summaries, `decision_trace`, diagnostics and limitations. The private starting point is deliberately omitted from the read response. A completed snapshot is immutable; `GET` never recomputes it.
- The original fixture is `synthetic-ru-2026-v01`, country `RU`, synthetic scope `ru:region:smolensk`, inclusive season `2026-05-01`–`2026-08-15`. All forage windows, coordinates and labels are fictional. Even though the scope label resembles a real administrative region, it does **not** establish geographic reference availability, real forage, ecological suitability, approved legal boundaries or a reliable travel recommendation.
- A window with fewer than two suitable synthetic stops is `COMPLETED` with `INSUFFICIENT_EVIDENCE` and no fabricated plan. Invalid combinations return `422/INVALID_INVESTIGATION_REQUEST`, unknown UUIDs return `404/INVESTIGATION_NOT_FOUND`, and malformed JSON/UUIDs return `422/INVALID_REQUEST`. OpenAPI lists the typed error envelope.
- The default V01 path remains non-durable. An explicitly injected completed-snapshot store can reopen a previously finished result from PostGIS, but only after separately configured database driver, migrations, and test evidence. Live PostGIS wiring is **not** the default application composition; queued/running jobs cannot survive a restart. If the completed store cannot be read, GET returns sanitized `503/INVESTIGATION_STORAGE_UNAVAILABLE`.
- This path does not implement the full Source registry, Agent, DAG executor, ecological conflict screening, real geographic references, live weather, cross-process jobs or full `MVP01-BE-A08/A09` acceptance. It must not be treated as production-ready.

## Opt-in fictional ecology investigation (V04-03 partial)

`scenario_id=synthetic-ru-2026-v04-ecology` uses the existing `POST /api/v1/investigations` and `GET /api/v1/investigations/{id}` operations with an explicit offline fixture. An initial selected site intersects a fictional exclusion, and the injected pure analysis/agent chain replans to a different synthetic site. The original `synthetic-ru-2026-v01` scenario and its string `decision_trace` are unchanged.

`InvestigationResponse.replanning` is additive and nullable (`null` for V01/pending/failed). For a completed fictional ecology analysis it provides a typed `outcome`, `checks_used`, `excluded_site_ids`, `unknown_site_ids`, `assessments` (`SiteAssessmentDto`: status, evidence/rule IDs, reasons, unknowns, synthetic marker), ordered `decisions` (`ReplanDecisionDto`: kind, site/evidence/rule IDs and note), and explicit `warnings`. The private request `starting_point` remains absent. No result claims actual ecological suitability or legal restrictions; all polygons and forage observations are fictional. Bounded exhaustion and insufficient evidence are completed domain outcomes, not implicit recommendations. This is not a substitute for real PostGIS or Web acceptance.
