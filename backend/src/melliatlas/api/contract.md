# HTTP API Contract

**Public Python interfaces:** `melliatlas.api.app.create_app`, `melliatlas.api.app.AppSettings`, `melliatlas.api.public.HealthResponse`, `ApiErrorCode`, `ErrorResponse`, and versioned territory endpoints.

## Implemented

- `create_app(settings=..., territories=...)` constructs an independent FastAPI application without network calls or implicit database connections. The territory catalog is injected through its public `TerritoryCatalog` protocol; omitting it leaves protected reference reads unavailable unless both local reference paths are explicitly configured in `AppSettings`. A configured ASGI lifespan validates the snapshot and independent inventory before serving; invalid, missing, incomplete or checksum-mismatched inputs fail startup. Mixed explicit `territories` injection and file configuration, or one-sided file configuration, are rejected at composition time.
- `GET /health` returns HTTP 200 and `{"status":"ok"}`. It measures process responsiveness, not readiness of references or databases.
- `GET /openapi.json` exposes success and error response schemas, stable error codes, and applicable `404`, `409`, `422` and `503` statuses; `/docs` provides the framework API viewer.
- `GET /api/v1/territories/countries` lists supported country codes RU/BY, **not** claims of loaded boundary data.
- `GET /api/v1/territories/regions?country=RU|BY` returns typed first-order catalog entries when a catalog has been injected. The standard ASGI entry point uses its pinned local name-only ISO list when no database is configured; it does not imply region boundaries or district coverage.
- `GET /api/v1/territories/districts?region_id=...` returns the complete supported pilot district catalog or an explicit unsupported-depth error.
- `GET /api/v1/territories/{territory_id}` returns one canonical territory.
- `GET /api/v1/territories/geometry/{territory_id}` returns an available WGS84 GeoJSON geometry, reference ID, and coordinate system.

## Error semantics

Public domain errors have the typed envelope `{"error":{"code":"...","message":"..."}}` (`ErrorResponse`, `ApiErrorCode`). Missing catalog -> `503/TERRITORY_REFERENCE_UNAVAILABLE`; unknown territory -> `404/TERRITORY_NOT_FOUND`; missing geometry -> `404/TERRITORY_GEOMETRY_MISSING`; unsupported districts -> `409/DISTRICT_COVERAGE_UNSUPPORTED`; malformed input -> `422/INVALID_REQUEST`. The shared FastAPI validation handler returns `422/INVALID_REQUEST` in the same envelope; OpenAPI documents this actual response instead of the framework default validation schema. An unavailable catalog is **never** represented as a successfully loaded empty catalog.

## Provider-neutral routes and evidence boundaries

`routes_sources.py` only lists injected source capabilities and builds the sanitized
HTTP error envelope. `providers/saturn/routes.py` and `providers/open_meteo/routes.py` own their
provider-specific request validation, capability visibility and projections; the
FastAPI composition root registers them independently. Source transports, decoders
and operational weather policy belong to `sources/providers/`, never generic HTTP
route modules. Stable domain warning codes are localized by the browser.

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

## Opt-in fictional treatment investigation (V04-05 partial)

`scenario_id=synthetic-ru-2026-v04-treatment` reuses existing `POST /api/v1/investigations` and `GET /api/v1/investigations/{id}`. It adds nullable `InvestigationResponse.treatment_review` with typed per-site screening, source record IDs, source-attributed capture/application timestamps, reported product/crop/bee hazard claims, approximate proximity, avoided candidates, and explicit uncertainty warnings. It contains **no real application, validated drift estimate, or authorized safe placement**. One fictional treatment polygon intersects the initial candidate and leads the provisional plan to select a fictional alternative; all other previous scenarios retain unchanged outcomes and traces. Request starting coordinates remain private. Missing or inconsistent injected planner input results in a sanitized `FAILED` state. Completed snapshots can round-trip through the optional existing store port, but real PostGIS integration remains unverified.

## Joint fictional ecology/treatment scenario (V04-06 partial)

`scenario_id=synthetic-ru-2026-v04-ecology-treatment` uses the unchanged investigation POST/GET operations. Completed responses populate **both** `replanning` and `treatment_review` while `plan` is the final joint result, not either standalone intermediate proposal. `replanning.decisions` includes typed `TREATMENT_CHECK` entries with attributed record IDs alongside ecology decisions; the treatment review retains reported dates/products and screening uncertainties. A missing evaluator or malformed observation returns sanitized `FAILED` without a plan. The original V01, ecology-only and treatment-only scenario contracts are unchanged. All evidence is synthetic; no spraying occurrence, site safety, weather drift or real-world eligibility is established.


## Read-only synthetic scenario discovery (W01 client refactor)

`GET /api/v1/investigations/scenarios?country=RU|BY` returns a typed list of executable source-declared fictional scenarios, with an opaque `id`, display `name`, `country`, source-owned `territory_id` and `territory_name`, `source_mode=SYNTHETIC`, inclusive `season_start`/`season_end`, and an optional `is_default` preference. Values derive from `SyntheticFixtureProvider.list_scenarios` and actual provider-supported seasons, not client configuration. A supported country with no scenario returns `200 []`; an invalid country returns the normal `422/INVALID_REQUEST` envelope. With a custom investigation service injected, the default application advertises no fictional scenarios instead of implying execution support.

This is **not** a full source registry, an approval of any territory reference, live treatment data, a safe-site guarantee or a provider discovery endpoint. Current country support is RU/BY; future country support requires backend catalog and fixture/provider implementation, but no browser-side country cases. The existing POST/GET DTOs remain unchanged.


## Explicit source-provider composition (W01 follow-up)

`AppSettings.source_provider` is a typed `SourceProviderMode` defaulting to
`DISABLED`, not the synthetic provider. `create_app()` composes providers only at
`api.composition.compose_sources` and injects their typed collaborators into
`InMemoryInvestigationService`. The `DISABLED` configuration returns an empty
scenario discovery list and rejects synthetic investigation POSTs as unsupported
rather than silently loading fixture evidence. `SYNTHETIC` explicitly activates
the offline, bounded provider and its ecology/treatment evaluation callbacks.
The ASGI entry point reads `MELLIATLAS_SOURCE_PROVIDER` (`disabled` or `synthetic`),
rejecting unknown values during startup. External service injection remains explicit,
and custom investigation services do not implicitly expose fixture discovery.
This composition is deliberately small and does not add a service locator, global
registry, runtime dependency or provider auto-discovery.

## Experimental public Saturn read, separate from investigations (RU only)

`GET /api/v1/sources?country=RU|BY` returns a source capability list from the
explicit server configuration: with `MELLIATLAS_SATURN_LIVE_ENABLED=true`, `RU`
returns one `saturn` entry (`LIVE`, `EXPERIMENTAL`), while `BY` returns `[]`.
The disabled/default mode advertises no live providers. This is not a general
source catalog or a guarantee of upstream availability.

`POST /api/v1/sources/saturn/treatments` accepts `country=RU`, a strictly
validated positive provider-specific `region_code` and bounded zero-based
`page_number`; it performs **one** explicit remote page read through a fixed
HTTPS endpoint. The response returns `source_id`, capture time, unknown records,
optional pagination, `coverage_complete=false`, and typed source-reported field
notices with optional WGS84 geometry and treatment/product claims. No result is
appended to synthetic investigations, persisted or treated as a safety outcome.

Cross-country requests return `404/SOURCE_NOT_AVAILABLE` before any I/O; an
disabled source returns `503/SOURCE_NOT_AVAILABLE`, an inaccessible or malformed
upstream read returns `502/SOURCE_READ_FAILED`, and invalid inputs receive the
standard `422/INVALID_REQUEST`. No synthetic fallback, retries, crawler,
redirects, hidden polling or browser-side cross-origin requests are permitted.
Official public API compatibility and reuse permission have not been verified;
this feature requires explicit local opt-in and independent acceptance.

## Experimental weather forecast HTTP API

`AppSettings.weather_live_enabled` defaults to `False`. A separately injected
`WeatherForecastReader` is only used when enabled. Source capability discovery
adds `open-meteo` / `WEATHER_FORECAST` for currently supported countries without
changing the independent RU-only restriction for `saturn`.

`POST /api/v1/sources/weather/forecast` accepts only WGS84 `latitude` and
`longitude` in the JSON body, not query parameters. It returns exactly 24 UTC
hourly model forecasts with provider ID, retrieval time, provider grid position,
units documented as km/h, degrees and mm, and explicit uncertainty. Bad input
returns `422/INVALID_REQUEST`; disabled reading returns
`503/SOURCE_NOT_AVAILABLE`; missing, corrupt or unreachable upstream data
returns sanitized `502/SOURCE_READ_FAILED`. No public route performs an automatic
request or makes a treatment safety decision.

The coordinates are passed to Open-Meteo only after an explicit user action.
The free endpoint is non-commercial with CC BY 4.0 attribution; commercial use
requires separate terms. Upstream live responses and rights must be rechecked
before acceptance or public release.

## Optional persistent region directory and Saturn translation

With a preseeded `MELLIATLAS_DATABASE_URL`, the application injects a PostgreSQL
implementation of the existing territory catalog. `GET /api/v1/territories/regions`
then returns independently keyed RU/BY subdivision names even when no polygon
reference snapshot is loaded. Geometry remains `missing`; requests for
unsupported districts return `409`. Without database or file references,
region reads retain the explicit `503` state.

The Saturn manual read accepts either a canonical `region_id` or the legacy
numeric `region_code`, **never both**. With `region_id`, the server resolves
`melliatlas_source_saturn` before any provider HTTP access. `409` with
`SOURCE_REGION_UNMAPPED` means no reviewed mapping exists, not that the source
reported no treatments; `503` means the region mapping database is unavailable.
The response includes `region_id` for a canonical-ID request, or null for the
legacy code. Country BY is still rejected before mapping and transport.
No source-specific identifier is leaked into the independent region catalog.



## Optional map point lookup (W01 R02 partial)

`POST /api/v1/territories/resolve-point` accepts `country`, `longitude`, and `latitude` in a JSON body, validated as finite WGS84. It calls the optional `TerritoryPointLocator` port and returns `{region_id, district_id}` using canonical IDs. No hit is `404/TERRITORY_NOT_FOUND`; missing/ambiguous PostGIS coverage is `503/TERRITORY_REFERENCE_UNAVAILABLE`; bad coordinates are `422/INVALID_REQUEST`. The route is read-only, does not log point data, and does not fabricate containment in synthetic or name-only catalogs.

## Deferred weather configuration

The optional `weather_reader_factory` is injected into `create_app` and runs once
inside the ASGI lifespan, off the event loop. Module import and route registration
never query Postgres for Open-Meteo configuration. The factory cannot be combined
with an explicitly injected `weather_reader`. A disabled database row produces
no advertised weather capability; unavailable or unmigrated configuration aborts
startup rather than substituting defaults. Reader availability is scoped to the
application lifespan and cleared on shutdown. Direct `create_app` injection of
`weather_reader` keeps the existing explicit testing semantics.

## District-scoped Saturn read (W01 extension)

`POST /api/v1/sources/saturn/treatments` accepts optional canonical
`district_id` and date-only `date_start` and `date_end`, both present, ordered
and at most 31 days apart. A district requires a canonical region. The
server resolves its provider code with `SourceDistrictCodeLookup`; it never
trusts a client-supplied Saturn district code. Missing mapping yields
`409/SOURCE_REGION_UNMAPPED`, unavailable configured storage yields
`503/TERRITORY_REFERENCE_UNAVAILABLE`, and malformed requests yield 422.
The response echoes the selected district and dates for client validation.
Legacy region requests are retained for controlled clients but must never
serve as a fallback for a requested district. The provider `UpdateMap`
filter semantics and rights to read remain unverified.
