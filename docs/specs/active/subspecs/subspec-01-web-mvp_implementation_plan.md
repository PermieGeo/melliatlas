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

**Public contracts and integration design:** `sources.providers.synthetic.api.SyntheticFixtureProvider.list_scenarios(country)` advertises only executable fictional sources and their supported `TimeWindow`. `api.routes_investigations` maps these records to a `ScenarioListingDto` with stable `id`, `name`, `country`, `territory_id`, `territory_name`, `source_mode`, `season_start`, `season_end`, `is_default`. `GET /api/v1/investigations/scenarios?country=...` returns `200` and an empty array for countries with no scenario, and the existing `422/INVALID_REQUEST` response for unsupported country codes. For explicitly injected custom investigation services, no synthetic source is advertised without an injected scenario listing.

`web/src/api/` validates the response before any scenario can be selected. The UI country code is an open ISO alpha-2 string validated at the network boundary; backend support is still governed by its declared current country catalog. The default preference is RU when offered, otherwise the first API country. Switching country aborts stale results and reloads both actual regions and executable scenarios. Scenario boundaries set the initial dates and constrain user input. An unavailable catalog is never represented as validated geography; fictional options are clearly labeled. UI-controlled text lives in a typed RU/EN dictionary, while provider-authored source claims remain unmodified for provenance.

**Interaction layers:** `components/InvestigationControls.tsx` owns the input view, `hooks/useInvestigation.ts` owns bounded polling and cancellation, `notifications.ts` maps error and outcome types to translation keys, `i18n.ts` owns presentational strings. `App.tsx` composes these capabilities without country-specific feature branches or scenario identifiers. Country-specific fictional evidence remains inside `sources`, never the client. No new runtime dependencies are introduced.

**Tests:** `backend/tests/contract/test_web_scenario_discovery.py` checks executable metadata, non-RU empty country, invalid country and HTTP POST compatibility. `web/tests/scenarios.test.ts`, `web/tests/i18n.test.ts`, `web/tests/workflow.test.tsx` validate wire parsing, typed translation, country switches, third-country fixture, dynamic seasons and in-flight cancellation. Existing `WEB-T001`–`WEB-T005` tests remain required. W01 acceptance still requires local TypeScript, lint, Vitest, build and browser E2E verification.

### W01 R02 — read-only territory reference navigation (implementation increment)

**Requirement and oracle:** `MVP01-WEB-R02` / `MVP01-WEB-A06`, partial pending approved reference catalogs. Implement against existing `GET /api/v1/territories/regions`, `/districts`, and `/geometry/{territory_id}` with no backend contract changes.

**Public contracts and integration design:** `web/src/api/types.ts` defines `TerritoryGeometry` and Polygon/MultiPolygon WGS84 wire structures; `validation.ts` strictly decodes coordinates, rings and CRS. `client.ts` exposes `getTerritoryGeometry(territoryId, signal): Promise<ApiResult<TerritoryGeometry>>`; `listDistricts` remains unchanged. The view-level `useTerritoryReference(country, regions)` owns cancellable district and geometry reads, ID/version matching and explicit `404/409/503` presentation states. `ReferenceControls` is a separate reference selector; the fictional scenario selector never treats administrative catalogs as executable sources. `MapPanel` renders only a returned, validated reference polygon; external map tiles remain opt-in.

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
abstracts on-demand page reading, `sources.providers.saturn.api` exposes the
pure decoder and bounded read adapter, and the only permitted network transport
is `api.saturn_http`. The composition root enables this **independently** of
`SourceProviderMode` with `AppSettings.saturn_live_enabled` / the exact
`MELLIATLAS_SATURN_LIVE_ENABLED=true` environment flag. `api.routes_sources`
provides `GET /api/v1/sources` capability discovery and a strict POST bounded
read. Source-country validation precedes transport. Reuse permission and exact
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
use `sources.providers.open_meteo.api.OpenMeteoForecastReader` through
`api.composition.compose_weather_reader`. `api.weather_http` is the sole
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
or persistence. `api.saturn_http.get_public_subject_directory()` uses a pinned
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
