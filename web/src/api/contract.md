# Browser HTTP boundary — W01

`client.ts` exposes `listCountries`, `listRegions`, `listDistricts`, `startInvestigation` and `getInvestigation`. Every operation receives an `AbortSignal`, returns an `ApiResult<T>` discriminated union, and sends requests only to same-origin `/api/v1/` paths. The Vite development proxy is configured separately from production API deployment.

`types.ts` documents the subset of actual FastAPI wire responses consumed by W01. `validation.ts` rejects malformed or mismatched response shapes before returning typed data; nested treatment findings, ecological decisions, evidence summaries and coordinates are checked. The Python Pydantic DTOs, generated OpenAPI and backend contract tests remain authoritative; client contract tests exercise an HTTP fixture generated from the real combined FastAPI scenario. No browser module imports Python source, source-provider internals or database adapters.

An error retains the HTTP status and stable server error code when available. Cancelled requests return `ABORTED`, transport failures return `NETWORK_ERROR`, and incorrectly structured responses return `INVALID_RESPONSE`. A successful HTTP 202 is not a completed analysis; polling and bounded retries belong to `App.tsx`.

The private `starting_point` exists only in the POST body; the decoder rejects an unexpected private coordinate in the returned request. Do not log, store or place it in a URL. Completed data may be reloaded by opaque investigation UUID only while the server still has a snapshot. No frontend action triggers source scraping or a background provider collection job.

## Country-neutral executable scenario discovery (W01 refactor)

`listScenarios(country, signal)` calls `GET /api/v1/investigations/scenarios?country=...` and validates each scenario's country code, opaque ID, fictional territory ID and title, `SYNTHETIC` mode, canonical inclusive dates, and default flag. Invalid, duplicate or contradictory metadata becomes `INVALID_RESPONSE`. Empty discovery means no executable scenario for that country, not safe or fully covered geography. The UI never keeps scenario/fixture IDs or default season years in source code. The backend still authorizes individual POST requests. Country codes have an open ISO alpha-2 representation on the client; languages RU/EN are independent UI locales.

## W01 R02 — reference geometry boundary

`getTerritoryGeometry(territoryId, signal)` reads the existing `GET /api/v1/territories/geometry/{territory_id}` response. `decodeTerritoryGeometry` checks its territory ID, nonempty reference version, `EPSG:4326`, WGS84 finite longitude/latitude, closed rings and Polygon/MultiPolygon structure. The UI separately checks that the returned territory ID and reference ID match the currently selected catalog entry before displaying it. Geometry topology and catalog completeness remain backend reference-validation responsibilities.

`listDistricts(regionId, signal)` supplies only supported children; HTTP `409`, `404`, and `503` remain explicit states. Country/region/district switches abort obsolete reads. Administrative outlines are a view-only map layer, never synthetic source evidence or validated pesticide safety. No new backend routes or live reference data are introduced.
