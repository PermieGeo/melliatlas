# MVP-01 Web — Implementation Plan

- **Status:** IN PROGRESS — W01 first runnable browser slice, acceptance pending
- **Normative source:** [Web sub-spec](subspec-01-web-mvp.md)
- **Parent:** [Umbrella MVP-01](../../umbrella_spec_melliatlas.md#mvp-01--working-sustainable-beekeeping-mvp)
- **Requirements approval:** APPROVED — first browser workflow scope
- **Implementation authorization:** AUTHORIZED — W01 following developer direction to proceed
- **Acceptance:** PENDING

The selected task is a **first runnable browser vertical slice**, not a wholesale frontend or historical Admin port. Only interfaces consumed by that slice are designed here; later evidence filters, routes and generic UI frameworks are not predesigned.

## 1. Verified backend boundary (current implementation)

| Operation | Existing contract | Consumer behavior |
| --- | --- | --- |
| `GET /api/v1/territories/countries` | `list[CountryResponse]`, currently RU/BY; no claim of reference readiness | Show country options; region availability is separate |
| `GET /api/v1/territories/regions?country=RU|BY` | `list[TerritoryResponse]`; `422`, `503` | Render versioned references or a precise unavailable state |
| `GET /api/v1/territories/districts?region_id=...` | `list[TerritoryResponse]`; `404`, `409`, `422`, `503` | Navigate only supported depth; do not make an empty list imply complete coverage |
| `GET /api/v1/territories/geometry/{territory_id}` | `GeometryResponse` with WGS84 geometry and reference ID; `404`, `422`, `503` | Render only validated geometry; fallback to textual selection |
| `GET /api/v1/investigations/scenarios?country=...` | `list[ScenarioListingDto]`, executed-only fictional sources; empty list means unavailable for that country | Supply selectable scenario, synthetic territory association and inclusive date bounds; never embed fixture IDs in browser code |
| `POST /api/v1/investigations` | `InvestigationCreateDto`, returns `202` + `InvestigationResponse` | Submit season and optional private starting point in the body; retain UUID |
| `GET /api/v1/investigations/{id}` | `InvestigationResponse`; `404`, `422`, `503` | Poll/reopen without replaying POST; stop at terminal state |

`InvestigationResponse` includes `status`, nullable `outcome` and `plan`, `synthetic`, `evidence`, `limitations`, `decision_trace`, nullable `replanning` and nullable `treatment_review`. For the joint fixture, both findings are present; `replanning` includes `assessments` and typed `decisions`, while `treatment_review` includes source record IDs, reported product claims, proposed application times, proximity and warnings. The private `starting_point` occurs only in the create DTO, not the response request echo.

**Concrete consumer fixture for the first slice:** the backend currently advertises the joint fictional RU scenario as its default. Fixture IDs, territories and inclusive season limits are read from scenario discovery, not encoded in the UI. Discovery is independent of the unfinished RU/BY reference catalogs and does not supply real geographic coverage.

Source declarations: [`api/routes_investigations.py`](../../../../backend/src/melliatlas/api/routes_investigations.py), [`api/routes_territories.py`](../../../../backend/src/melliatlas/api/routes_territories.py), [`api/contract.md`](../../../../backend/src/melliatlas/api/contract.md), [`sources/api.py`](../../../../backend/src/melliatlas/sources/api.py). Existing OpenAPI is the wire-schema source of truth. No duplicated handwritten HTTP schema may silently diverge from it.

## 2. W01 — first Web implementation slice (in progress)

**Goal:** render a single accessible browser page that calls the existing API, runs the joint fictional scenario, and synchronizes the returned selected stops between a map, season timeline and evidence/limitations panel. The map/timeline visual design must be newly designed around beekeeper decisions rather than copied from the historical application.

**Requirement IDs:** `MVP01-WEB-R01`, `R03`–`R08` (from the proposed sub-spec). `R02` is implemented only to the extent the backend has validated territory references.

### Public contracts and integration design

#### Public types and signatures

- `web/src/api/` will own a single typed HTTP client, response validation and an explicit `{ kind: 'ok', data } | { kind: 'error', status, code }` result boundary. Generate or derive wire types from current OpenAPI; choose a runtime validation strategy supported by an approved dependency. Do not bypass strict TypeScript with `any` or unverified assertions.
- `startInvestigation(request, signal)` accepts the fields of `InvestigationCreateDto` and returns the existing `InvestigationResponse`. `getInvestigation(id, signal)` consumes the same response schema. `listCountries`, `listRegions`, `listDistricts` and `getGeometry` consume the implemented territory operations; missing reference responses remain explicit errors.
- A view-only selection state holds the selected `site_id` and season cursor. The server result remains authoritative; do not store a second editable copy of stops or findings.

#### Module interactions

A top-level `web/src/` composition view owns the user workflow; dedicated map/timeline/evidence components receive typed, derived view data. HTTP requests are made only by the API client. No frontend module imports Python source or a private provider parser. Re-rendering, selecting a stop or navigating the map must not cause source collection or re-execution of the investigation.

#### Failure contracts

Cancel in-flight requests when switching run IDs, country/territory or unmounting. Reject stale responses using the current request identity, not timing assumptions. A `202` submission is not completed analysis. Poll with a finite interval and timeout/attempt ceiling; show a pending state if the limit is reached instead of fabricating a failure. Distinguish HTTP transport problems, typed domain error codes, `COMPLETED` with no plan, and `FAILED` investigation status. After reload, a `404` may mean the default in-memory store was lost.

#### Compatibility

The first slice uses only existing POST/GET operations and additive nullable response fields. A bounded read-only executable-scenario listing was added for W01 follow-up requirements. Full region/district navigation, live-source catalogs and true post-restart result durability remain separate backend gaps, not reasons to invent data in React. Do not persist `starting_point` in URLs, browser storage, logs or telemetry. The URL may contain only an opaque investigation ID.

#### Contract-first tests

1. `WEB-T001`: a browser submit/poll/reopen test observes the joint fixture's completed stops, treatment findings, ecology decisions and synthetic banner (`R03`–`R07`).
2. `WEB-T002`: map and timeline selection agree on one stop; textual navigation still works if map tiles fail (`R05`, `R08`).
3. `WEB-T003`: `404/422/503`, no-plan, `FAILED`, abort and stale response are distinct (`R04`, `R08`).
4. `WEB-T004`: mobile, keyboard and privacy checks cover touch controls, source labels and no private point in URL/logs (`R01`, `R07`, `R08`).
5. `WEB-T005`: RU/BY and unsupported geometry cases are driven by API responses, never fabricated catalogs (`R02`).

**TDD evidence:** `web/tests/client.test.ts`, `web/tests/workflow.test.tsx` and `web/e2e/workspace.spec.ts` encode the W01 behaviors. The HTTP fixture is generated from the actual FastAPI combined synthetic response.

**Implementation paths:** `web/src/api/contract.md`, `web/src/api/types.ts`, `web/src/api/validation.ts`, `web/src/api/client.ts`, `web/src/App.tsx`, `web/src/components/{MapPanel,Timeline,EvidencePanel}.tsx` and the W01 test sources. The backend Pydantic DTOs remain authoritative.

**Exit evidence:** frontend dependencies resolved, strict TypeScript and lint checks passed, component tests passed, browser E2E passed, and preserved backend regressions. Code presence alone does not meet these criteria; the current delivery remains partial until local dependency installation and browser checks are confirmed.

**Approval gates:** W01 is selected for implementation. React, Leaflet, Vite, TypeScript and task-scoped test tooling are limited to the user-requested browser MVP. No feature acceptance or live-data permission is implied by implementation. Browser execution and dependency installation still require local verification.

### W01 refactor — multi-country, two locales and server-driven fixtures (developer-authorized)

**Requirement IDs:** `MVP01-WEB-R02`, `R04`, `R08`–`R10`. **Acceptance remains pending.**

**Public contracts and integration design:** `sources.providers.synthetic.SyntheticFixtureProvider.list_scenarios(country)` advertises only executable fictional sources and their supported `TimeWindow`. `api.routes_investigations` maps these records to a `ScenarioListingDto` with stable `id`, `name`, `country`, `territory_id`, `territory_name`, `source_mode`, `season_start`, `season_end`, `is_default`. `GET /api/v1/investigations/scenarios?country=...` returns `200` and an empty array for countries with no scenario, and the existing `422/INVALID_REQUEST` response for unsupported country codes. For explicitly injected custom investigation services, no synthetic source is advertised without an injected scenario listing.

`web/src/api/` validates the response before any scenario can be selected. The UI country code is an open ISO alpha-2 string validated at the network boundary; backend support is still governed by its declared current country catalog. The default preference is RU when offered, otherwise the first API country. Switching country aborts stale results and reloads both actual regions and executable scenarios. Scenario boundaries set the initial dates and constrain user input. An unavailable catalog is never represented as validated geography; fictional options are clearly labeled. UI-controlled text lives in a typed RU/EN dictionary, while provider-authored source claims remain unmodified for provenance.

**Interaction layers:** `components/InvestigationControls.tsx` owns the input view, `hooks/useInvestigation.ts` owns bounded polling and cancellation, `notifications.ts` maps error and outcome types to translation keys, `i18n.ts` owns presentational strings. `App.tsx` composes these capabilities without country-specific feature branches or scenario identifiers. Country-specific fictional evidence remains inside `sources`, never the client. No new runtime dependencies are introduced.

**Tests:** `backend/tests/contract/test_web_scenario_discovery.py` checks executable metadata, non-RU empty country, invalid country and HTTP POST compatibility. `web/tests/scenarios.test.ts`, `web/tests/i18n.test.ts`, `web/tests/workflow.test.tsx` validate wire parsing, typed translation, country switches, third-country fixture, dynamic seasons and in-flight cancellation. Existing `WEB-T001`–`WEB-T005` tests remain required. W01 acceptance still requires local TypeScript, lint, Vitest, build and browser E2E verification.

### W01 R02 — read-only territory reference navigation (implementation increment)

**Requirement and oracle:** `MVP01-WEB-R02` / `MVP01-WEB-A06`, partial pending approved reference catalogs. Implement against existing `GET /api/v1/territories/regions`, `/districts`, and `/geometry/{territory_id}` with no backend contract changes.

**Public contracts and integration design:** `web/src/api/types.ts` defines `TerritoryGeometry` and Polygon/MultiPolygon WGS84 wire structures; `validation.ts` strictly decodes coordinates, rings and CRS. `client.ts` exposes `getTerritoryGeometry(territoryId, signal): Promise<ApiResult<TerritoryGeometry>>`; `listDistricts` remains unchanged. The view-level `useTerritoryReference(country, regions)` owns cancellable district and geometry reads, ID/version matching and explicit `404/409/503` presentation states. `ReferenceControls` is a separate reference selector; the fictional scenario selector never treats administrative catalogs as executable sources. `MapPanel` renders only a returned, validated reference polygon; the user-approved later navigation follow-up enables OpenStreetMap tiles by default and remembers the map camera in browser-local storage.

**Contract tests:** `web/tests/reference-geometry.test.ts` checks Polygon/MultiPolygon decoding, malformed coordinates, CRS and encoded IDs. `web/tests/reference-navigation.test.tsx` checks a reference region and district, unsupported depth, missing/mismatched geometry, country switching and separation from investigation POSTs. No complete RU/BY inventory, real spatial audit, or post-import country coverage is claimed.

**Acceptance gate:** use independently approved actual reference snapshots and real browser checks before declaring `MVP01-WEB-A06` complete. Retain the selected W01 workstream; do not change `STATE.json` or begin full W02.

## 3. Follow-on work (do not predesign)

| Order | Slice | Dependency and unresolved decision |
| --- | --- | --- |
| W02 | Territory navigation and validated geometry layers | Approved, complete RU/BY references and correct `409/503` handling; real data availability must be proven |
| W03 | Treatment timelines and source transparency polish | Validate the exact server DTOs and distinguish source notices from spatial screening and unknown wind |
| V05 backend | Approved source catalog and complete HTTP handoff | The new executable-fixture listing does not implement live `/api/v1/sources`, geographical discovery or verified source coverage |
| V04 backend | Minimal typed source/analyzer execution | Required for full MVP-01 backend acceptance, but need not block the first browser demo |

No generic frontend state framework, map drawing engine, Admin workspace or speculative API is part of W01.

### W01 additional user-authorized task — RU-only public Saturn preview

**Public contracts and integration design:** `sources.api.TreatmentNoticeReader`
abstracts on-demand page reading, `sources.providers.saturn` exports the
pure decoder and bounded read adapter, and the only permitted network transport
is `sources.providers.saturn.http`. The composition root enables this **independently** of
`SourceProviderMode` with `AppSettings.saturn_live_enabled` / the exact
`MELLIATLAS_SATURN_LIVE_ENABLED=true` environment flag. `api.routes_sources` lists only injected source capabilities;
`api.providers.saturn.routes` implements the strict POST bounded read. Source-country validation precedes transport. Reuse permission and exact
current upstream format remain unverified; the endpoint's payload is based on
an historical `planapplybees` capture and must fail visibly if incompatible.

**Browser integration:** A separate `SaturnPanel` appears only if the server
advertises it for the selected country; it accepts an explicit source-specific
numeric region code, fetches one page on click, attributes every claim and
provides a distinct optional map polygon layer. It does not influence the
synthetic season plan or infer that an empty response is complete. RU/BY
switching clears stale results; no automatic polling/crawling occurs.

**Tests:** `backend/tests/contract/test_saturn_live_http.py` verifies country
gating, disabled mode, request shape, source metadata and provider failures;
`web/tests/saturn.test.tsx` checks source discovery, manual-only reads and
wire rejection. Existing import-policy and Web tests must remain green.
External authorization, full geographic inventory, live provider compatibility,
normalization accuracy against observed current response samples, production
rate control and public release remain separately gated. W01 acceptance is
still pending.

### W01 additional developer-authorized task — live point weather forecast

**Scope:** add a real, optional, provider-neutral hourly forecast read to the
existing live-source panel without changing W01 acceptance or synthetic study
results. This is an independent source observation, not a new planning engine.

**Boundary:** `sources.api.WeatherForecastReader` and typed `WeatherForecast`
use `sources.providers.open_meteo.OpenMeteoForecastReader` through
`api.composition.compose_weather_reader`. `sources.providers.open_meteo.http` is the sole
fixed-origin transport; it requests 24 UTC hours, has strict time/size bounds,
and never follows redirects. `AppSettings.weather_live_enabled=False` and
`MELLIATLAS_WEATHER_LIVE_ENABLED=true` govern opt-in availability. Open-Meteo
is not RU-specific; Saturn remains unavailable outside RU. Frontend sources are
advertised by a typed country-scoped catalog; a selected point and explicit
click trigger a single weather POST. No hidden polling, fake fallback,
forecast-to-notice join or drift inference is permitted.

**Checks:** `backend/tests/contract/test_open_meteo_live_http.py` checks
nulls, units, UTC, source attribution, invalid inputs, country listing,
configuration and upstream failures. `web/tests/weather.test.tsx` verifies
source discovery, manual requests, schema rejection, attribution and state
clearing. Full local typecheck, lint, Vitest, browser and real provider
compatibility remain acceptance gates. Current live-source reading does not
establish legal/commercial reuse eligibility or forecast accuracy.

### W01 follow-up — usable live sources without fictional catalog entries

**Scope and requirement:** W01 source discovery and explicit `503` catalog handling,
not new geographic coverage or an accepted live Saturn mapping.

The country selector is the entry to real provider capabilities. The left
navigation links directly to on-demand live sources, while the synthetic
territory/scenario/season form is shown only when the backend advertises
executable fictional scenarios. A disabled synthetic provider must not leave
an apparently mandatory empty territory picker or block direct live reads.
The independent reference region selector continues to indicate unloaded
validated geography; it must never silently supply guessed Saturn subject IDs.

**Regression:** `web/tests/workflow.test.tsx` exercises the live-only RU/BY
workflow with an unavailable reference catalog and no synthetic scenarios,
including source discovery, manual selection of a weather point, and RU-only
Saturn visibility. Existing synthetic-plan and browser tests remain required.
**Acceptance:** local frontend checks and a real, permitted provider response
remain outstanding; no new actual regional catalog was imported.

### W01 follow-up — persistent region names and source-specific Saturn mapping (R02, partial)

**Authorization:** developer requested preloaded country-owned regions in a
shared database table, with a separate Saturn mapping table and a single
country/region selection in the browser. The geography catalog is independent
of every provider. W01 acceptance remains pending; W02 district/boundary
coverage is **not** implied.

#### Public contracts and integration design

- `TerritoryCatalog` and new `SourceTerritoryCodeLookup` in
  `backend/src/melliatlas/territories/api.py`: typed async, canonical region IDs,
  a provider-specific lookup that returns `None` for an unmapped region.
- `PostgresRegionCatalog` in `backend/src/melliatlas/persistence/regions.py`
  implements those ports through parameterized read-only database access.
  The adapter is injected at `main.py` when `MELLIATLAS_DATABASE_URL` is explicit.
  Do not auto-seed, migrate, or contact providers at ASGI startup. Missing
  database returns a typed unavailable state; district depth and geometry
  remain unsupported/missing for the ISO name-only seed.
- `backend/migrations/0002_region_directory.sql` adds `melliatlas_region`
  (country, canonical ID, ISO code, names, source/version/date) and the separate
  RU-only FK table `melliatlas_source_saturn` (source subject/OKTMO mapping,
  provenance). The first seed, `backend/reference/iso3166-2-regions.json`, pins
  83 RU and 7 BY first-order ISO 3166-2 subdivisions from iso-codes 4.18.0.
  It is not a verified full modern jurisdiction or polygon inventory.
  `bootstrap_regions.py` validates existing rows and seeds the archived
  Smolensk `55` mapping; an operator-reviewed offline import may add further
  exact-name mappings from a separate Saturn `/oktmo-subjects` capture.
- Existing `GET /api/v1/territories/regions?country=...` remains the browser
  directory contract. `POST /api/v1/sources/saturn/treatments` now accepts
  **either** `region_id` or the legacy numeric `region_code`; exactly one is
  required. Unmapped region returns `409/SOURCE_REGION_UNMAPPED` before any
  source transport. Country BY remains rejected before mapping. Responses
  echo the canonical region ID for matching client requests.
- `web/src/components/SaturnPanel.tsx` shares the selected canonical region
  from the left navigation. It neither requests Saturn regions on mount nor
  exposes numeric codes; switching region aborts/clears stale source notices.

**Tests:** `backend/tests/contract/test_persistent_region_directory.py`
asserts independent RU/BY seeded identities, protocol behavior, unavailable
catalog semantics, safe mapping, provider gating, and HTTP statuses. Existing
territory and Saturn HTTP contract tests preserve the injected in-memory
reference path and numeric legacy request. `web/tests/saturn.test.tsx` checks
canonical-ID posting, no-region disablement, and BY filtering. Manual Postgres
integration, captured full Saturn directory reconciliation, and W02 district/
geometry completion remain outstanding.

### W01 follow-up — operator-only Saturn subject catalog capture (R02, partial)

**Scope:** complete the operator path from independent preloaded RU regions to
verified source-specific Saturn IDs. This is an authorized small follow-up to
the existing PostgreSQL mapping work, not a new source registry, scheduled
collector, or accepted W02 geographic catalog.

**Public contracts and integration design:** `sources.providers.saturn.subjects`
validates one source-specific directory JSON array without importing transport
or persistence. `sources.providers.saturn.http.get_public_subject_directory()` uses a pinned
HTTPS GET with redirects/retries disabled, 8-second timeout and 256 KiB body cap;
`api.subject_capture.capture_subjects()` accepts an injected fetch and validator,
and saves to an explicitly named new local file with exclusive restrictive
permissions. `backend/scripts/capture_saturn_subjects.py` is the only operator
entrypoint; it reports only count, digest and timestamp. The existing
`import_saturn_subjects.py` reuses the same validator and continues to enforce
transactional exact-name matching into `melliatlas_source_saturn`. There is no
browser endpoint, application startup request or automatic source ingestion.

**Failure behavior:** invalid JSON, duplicate/blank identifiers, unexpectedly
small catalogs, non-JSON responses, 403, redirects, timeouts and preexisting
files fail closed. No raw payload is printed or included in repository fixtures.
Unknown region-name correspondences remain unmapped; source permissions and
live compatibility must be verified before operator capture. No actual local
PostgreSQL import or source read is claimed by these offline tests.

**Tests:** `backend/tests/contract/test_saturn_subject_capture.py` exercises
validation, privacy, byte budgets, exclusive capture and mocked transport
failures; existing region mapping tests and backend import architecture checks
remain required. W01/W02 acceptance remains pending PostgreSQL integration,
source inspection and verified region identifiers.


### W01 user-authorized follow-up — beekeeper-first area navigation (partial R02)

**Intent:** replace operator-oriented source actions with one beekeeper
workflow: country -> independent administrative region -> optional reviewed
district -> map -> one explicit *Analyze selected area* action. Keep synthetic
scenario execution hidden under optional details; remove the UUID reopen field
and provider-specific one-page/weather buttons from the primary interface.
Country changes and region changes must invalidate stale data and requests.

**Geographic boundary:** new `melliatlas_admin_geometry` in PostGIS stores
reviewed ADM1/ADM2 MultiPolygons independently of the canonical `melliatlas_region`
and the `melliatlas_source_saturn` mapping. `PostgisTerritoryCatalog` exposes the
existing typed territory API; no new browser wire endpoint is required. Import
is a deliberate offline operator action with original attribution and vintage
recorded, exact ADM1 matching, unambiguous spatial ADM2 parent assignment and
transactional conflict handling. No bulk provider data is bundled; a complete
RU/BY verified spatial inventory remains **pending**.

**Live-source boundary:** one browser click may request an attributed,
**first region-wide Saturn page (RU only)** and a point forecast in parallel.
The selected polygon bounds the UI interaction, not Saturn's server-side query;
this is explicitly a preliminary source inspection, not a complete spatial
query, treatment inventory, safety decision or pesticide drift estimate. Missing
territories/geometries block the main analysis and display an actionable state.

**Tests:** `backend/tests/contract/test_administrative_geometry.py` validates
the read adapter and invalid geometry; `web/tests/live-area-analysis.test.tsx`
checks one trigger, country gating and area selection. Existing W01 tests must
remain green. PostgreSQL/PostGIS migrations, real ADM1/ADM2 loads, full
React/Vitest/browser checks, actual Saturn compatibility and geography
completeness are **not yet accepted**. W02 and W03 remain distinct future stages.



### W01 R02 follow-up — visible ISO regions and automatic district navigation

**Scope:** A developer-requested repair to region selection readiness and the
country → region → district workflow, within `MVP01-WEB-R02` / `A06`; no
change to approved geographic coverage or W02 acceptance. The default ASGI
entry point loads the already-pinned ISO region names without requiring a
configured database. The independent API reference loader validates dataset
version, identities, uniqueness and country counts; the territory module
provides the read-only `TerritoryCatalog` with missing geometry and unsupported
district depth. When PostgreSQL is configured, the existing PostGIS catalog
remains authoritative; schema errors cannot silently fall back.

**Public contracts and integration design:** Existing `GET /regions`,
`GET /districts` and `GET /geometry/{territory_id}` response contracts are
unchanged. `RegionDirectoryCatalog` is a provider-independent name-only
implementation; `read_iso_region_directory` lives at the file-I/O boundary.
The browser already requests `/districts` on region selection; region-scoped
state now prevents obsolete district options from being displayed on rapid
switches. Actual district entries and polygons still require reviewed ADM1/
ADM2 PostGIS imports, with no silent remote collection or synthetic geography.

**Regression inventory:** `backend/tests/contract/test_bundled_region_directory.py`
checks 83/7 names and malformed datasets, explicit 409/404, and independence
from a database. `web/tests/reference-navigation.test.tsx` checks automatic
district loading, region switching and obsolete responses. The localized main
heading and subtitle are updated; no route, wire DTO or runtime dependency is
added. Acceptance remains pending verified local checks and real ADM2 import.

### W01 R02 follow-up — automatic map positioning and saved camera (partial R02/A06)

**Scope:** User-requested map UX refinement within the existing W01 navigation
workstream. Map tiles are displayed without an extra toggle. The Leaflet camera
restores the last locally saved center and zoom on browser reopen; only the
camera is retained (rounded to 4 decimal places), not the selected apiary
marker or investigation request. Tile requests share approximate viewport
coordinates with OpenStreetMap, which is disclosed in RU/EN map help. Storage
failures and malformed saved values do not block the map.

**Navigation:** Existing cancellable `GET /districts?region_id=...` requests
remain automatic on region selection. A successfully loaded, identity-checked
ADM1/ADM2 geometry always fits the Leaflet viewport when the beekeeper changes
the region or district, independently of an older saved camera. Switching
territories clears old live findings and fictional plans. Missing real
administrative geometry cannot be replaced by an invented region center:
backend PostGIS migration 0003 and reviewed ADM1/ADM2 imports remain explicit
prerequisites for positioning and district options.

**Tests:** `web/tests/viewport.test.ts` validates stored camera parsing,
privacy-limited serialization and storage failures. `web/e2e/workspace.spec.ts`
checks region-to-district viewport changes, restoration on reload, an absent
basemap checkbox, and a functioning text UI when tile requests are blocked.
Actual browser checks and real ADM2 imports remain separate acceptance gates.

### W01 R02 follow-up — country-switch reference recovery (partial)

**Scope:** isolate the loaded region catalog by country, invalidate selected
reference identities across country switches, and offer explicit retries for
failed region and district requests. Keep the existing HTTP DTOs and GeoJSON validation;
no geography is invented and no database mutation or automatic reimport occurs.
Per-region ADM2 distribution remains an operator inspection rather than a
claim inferred from the country-wide inventory check.

**Regression:** `web/tests/reference-navigation.test.tsx` exercises RU → BY →
RU with both district catalogs, failures followed by same-country or
same-region retries, and a delayed obsolete RU response after switching to BY. Manual verification
against an imported PostGIS dataset and browser/server logs remains necessary
before declaring the reported RU district issue resolved. W01/W02 acceptance
remains pending.

### W01 R02 follow-up — RU district availability diagnosis (partial)

**Scope:** The existing PostGIS catalog reads districts by canonical `region_id` for both countries. A complete ADM2 country count does not prove per-region coverage or browser/API consistency. `backend/scripts/diagnose_admin_navigation.py` compares imported region-level counts with the running local `/regions` and `/districts` responses, rejects cross-country or duplicate identities, and reports empty regions without changing the database. This is a diagnostic increment, not a claim that missing RU districts have been repaired.

**Tests:** `backend/tests/unit/test_navigation_diagnostics.py` covers matching, missing, cross-country and scoped checks. Real RU PostGIS and browser-network comparison remains a local verification gate under `MVP01-WEB-R02/A06`.

### W02 geography-data preparation — explicit PostGIS import workflow (pending acceptance)

**Scope:** Developer-authorized follow-up to the W01 territory navigator. The
existing `0002`/`0003` migrations, canonical ISO seed, read-only territory
endpoints and explicit PostGIS geometry importer remain authoritative. The
new offline operator CLI stages one geoBoundaries gbOpen ADM1/ADM2 layer with
source-version metadata, SHA-256, feature inventory and exact ADM1 review. A
repeatable four-layer CLI skips digest-verified staged files, prints network
progress, and stages source count mismatches as explicit pending review rather
than treating an incomplete source inventory as complete. An optional import
manifest rejects changed inputs or unacknowledged count mismatches; repeated
imports validate geometry and provenance. A read-only audit reports whether the stored version
matches the source inventory. No boundary data is shipped in Git or loaded on
application startup; no Saturn mapping or UX endpoint is changed.

**Test oracles:** offline metadata/URL/identity validation, digest mismatch,
non-overwrite, incorrect country/level, incomplete feature count, missing or
ambiguous matching and read-only database inventory. Full real PostgreSQL/PostGIS
import, matching review, source usage rights and current administrative
accuracy remain **unverified** and are required before W02 acceptance.
The repository `sh`-invoked formatter/check scripts use POSIX-compatible
file checks so backend checks cannot silently be skipped on shells without
Bash `[[ ... ]]` support; shell runner regression tests guard this behavior.

### W01 R02/R11 follow-up — click-to-district and explicit Saturn page expansion (partial)

**Public contracts and integration design:** `TerritoryPointLocator.locate_point` is an optional read-only geographic capability, implemented by the PostGIS adapter with `ST_Covers` against imported WGS84 ADM1/ADM2 boundaries. `POST /api/v1/territories/resolve-point` takes country and WGS84 coordinates in a JSON body; it returns canonical region and optional district IDs, `404` outside imported regions, `503` for unavailable/ambiguous geometry, `422` for invalid points. No point is logged or persisted by this operation. The browser validates the response, aborts obsolete clicks and waits for the region's district list before selecting a returned district. No synthetic or Saturn identity is involved.

**Saturn preview:** A completed manual area action still reads only source page zero. The user can request later pages one at a time, within the existing provider page cap. The browser deduplicates record IDs, clears stale pages on territory changes and draws any valid source polygons; a map control fits the camera to fetched fields. Counts distinguish available polygons from notices, and region-wide pagination is never represented as complete district inventory. The provider district-code mapping and complete district-scoped collection remain outside this increment pending separate source-contract and mapping review.

**Checks:** `backend/tests/contract/test_administrative_geometry.py` verifies parameterized point queries; `backend/tests/contract/test_territory_http.py` checks success, 404/503/422; `web/tests/reference-navigation.test.tsx` checks map click selection; `web/tests/live-area-analysis.test.tsx` checks manual pagination and polygon accumulation. Live PostGIS geography, provider field visibility and browser checks remain operator acceptance gates.

## W01 follow-up — persisted geographic context and live-source scope

The Web workspace restores public country/region/district IDs in order only
after independent catalog validation; its existing camera persistence remains
separate, and private map points are not stored. On a selected territory with
validated geometry, choose a point strictly inside its polygon and fetch one
24-hour Open-Meteo preview directly into the above-map panel. No automatic
Saturn harvesting or polling is authorized. The manual selected-area action
requires a reviewed district and a default date-only interval from local
today through one calendar month (maximum 31 days). The server resolves the
source-owned district ID from a new, deliberately unseeded migration `0005`
table; 409 is preferred to region-scope fallback. Provider `UpdateMap` filter
semantics and permission require independent verification before asserting
complete coverage. The layout uses a full-width workspace with navigation
sidebar rather than leaving unused right-hand space. New contract/unit tests
cover restoration, weather auto-read, geometry/point safety and no-unmapped-
district source calls. W01 and W02 acceptance statuses remain unchanged.
