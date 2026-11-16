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

## Explicit live public notice read (W01 experimental addition)

`listExternalSources(country)` discovers the explicitly enabled RU-only Saturn
capability. `readSaturnPage` sends the selected canonical region and district,
page number and bounded source date interval; the backend resolves provider
IDs from separately reviewed source mappings. Invalid, unavailable and
unmapped district scope is an error, never a region-wide fallback. A distinct
legacy `region_code` form remains available to controlled API clients only.
`decodeSaturnPage` rejects malformed notice records or unattributed geography;
changing the selection cancels prior reads and clears source polygons. Source
records never enter fictional investigation state. An empty page cannot prove
coverage or safety, and upstream filter compatibility is not independently
verified.

## On-demand live weather forecast

`listExternalSources` validates the discriminated `TREATMENT_NOTICE/saturn` and
`WEATHER_FORECAST/open-meteo` capability pairs. `readWeatherForecast(point,
signal)` posts the selected coordinates in the JSON body to the same-origin API.
The strict decoder requires 24 sequential UTC hours, nullable bounded values,
source attribution, grid coordinates and non-empty uncertainties. An aborted or
stale request is not a completed forecast. `WeatherPanel` automatically reads for a validated territory point, offers an
optional refresh action, never stores private coordinates, and includes
Open-Meteo attribution using the validated `source_uri` supplied
by the backend; browser modules do not duplicate a provider documentation URL.
Neither a weather forecast nor a live treatment notice modifies synthetic
investigation results or certifies pesticide drift, exposure or placement safety.

## Persistent regional directory and manual Saturn source selection

The country-scoped region list is authoritative for user-selectable first-order
regions. The UI passes its canonical `region_id` to the manual Saturn reader;
it never derives provider numeric IDs from region names, array indexes, ISO
codes, or synthetic scenarios. Region changes cancel outstanding Saturn
requests and clear prior notices. `SOURCE_REGION_UNMAPPED` is an explicit
no-data-source-mapping state, not a negative treatment finding. The numeric
`region_code` request is retained only for older API clients and controlled
operator tooling; the beekeeper UI does not expose it.

## Point-to-district selection and incremental Saturn display

`resolveTerritoryPoint` posts the clicked coordinate in JSON (never a URL), decodes the canonical containing region and optional district, and aborts stale lookups on another click or country/territory change. After region selection, the client only selects a district confirmed by the region's separately fetched catalog. A missing point lookup leaves the manual selector available.

The area panel reads Saturn page zero after the user's Analyze action; the user may fetch additional upstream pages one at a time. The UI deduplicates fetched record IDs and displays the number of valid polygons, with an explicit camera-fit control for fetched field shapes. This is a single district-filtered page requiring a reviewed provider mapping, not verified district completeness or a safety conclusion; no source crawling or district-code inference occurs.

## Restored selection, inline forecast, and district-scoped reads

`geo/territoryPreference.ts` persists public country/region/district IDs only;
`useTerritoryReference` restores each ID after the current server catalogs
confirm the parent-child relationship. Map clicks and weather coordinates are
not persisted. `geo/selection.ts#representativePoint` chooses a point strictly
inside the matched geographic polygon, and the automatic Open-Meteo forecast
appears in an inline card above the map. Without a validated boundary, no
point forecast is automatically requested. This read does not trigger Saturn.

`geo/dateRange.ts` defaults to local today through one calendar month (with a
clamped day for short months). A user-chosen source interval must be ordered
and no longer than one calendar year. The manual Saturn action submits canonical
`district_id`, `date_start`, and `date_end`; the response must echo all three
before the client shows provider polygons or pages. A missing reviewed Saturn
district mapping is 409 and must never fall back to whole-region data. The
Up to 100 source records can be read in 10 explicit requests of 10 records
(pages 0–9). The response field `record_limit_exceeded` shows when the source
reports more than 100 records or indicates another page beyond the cap.
No automatic pagination occurs; the UI stops manual pagination at page 9 and
warns that a truncated result is incomplete. `total_elements` remains the
upstream total, not a count of actually loaded or deduplicated records. The
upstream `UpdateMap` filter keys have not been independently verified to
represent actual treatment/application dates.

## Additive territory name localization

`TerritoryResponse.name_ru` is an optional nullable Russian display label for
imported districts. A browser selecting Russian may prefer it, but must retain
`name` as a source-language fallback and never use either label as a territory
identifier. The canonical `id`, `parent_id`, reference version, geometry and
source display name remain unchanged. The initial operator-curated seed is
limited to the Smolensk district names shown in `0006_smolensk_district_names.sql`.
