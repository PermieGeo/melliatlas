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

`listExternalSources(country)` reads the backend's enabled capability listing.
The presence of `saturn` for `RU` enables an isolated, manual source-read panel.
A country with no advertised Saturn capability has no Saturn UI or transport
calls. `readSaturnPage` posts a strictly typed provider region code and page
number, and `decodeSaturnPage` rejects malformed geography, mismatched country,
missing attribution or claims marked synthetic. Changing country or filter
cancels prior reads and clears prior polygons. External notices never enter
fictional investigation result state; the map renders their field polygons as
a visually distinct unverified source layer. Empty/failed pages cannot establish
complete coverage or site safety. The exact provider region codes remain
unverified and are entered manually, not inferred from administrative IDs.

## On-demand live weather forecast

`listExternalSources` validates the discriminated `TREATMENT_NOTICE/saturn` and
`WEATHER_FORECAST/open-meteo` capability pairs. `readWeatherForecast(point,
signal)` posts the selected coordinates in the JSON body to the same-origin API.
The strict decoder requires 24 sequential UTC hours, nullable bounded values,
source attribution, grid coordinates and non-empty uncertainties. An aborted or
stale request is not a completed forecast. `WeatherPanel` has a manual button,
does not log or persist coordinates, and includes Open-Meteo attribution using the validated `source_uri` supplied
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

The area panel reads Saturn page zero after the user's Analyze action; the user may fetch additional upstream pages one at a time. The UI deduplicates fetched record IDs and displays the number of valid polygons, with an explicit camera-fit control for fetched field shapes. This is still a region-wide sample, not verified district completeness or a safety conclusion; no source crawling or district-code inference occurs.
