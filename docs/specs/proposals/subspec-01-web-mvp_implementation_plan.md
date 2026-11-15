# MVP-01 Web — Proposed Implementation Plan

- **Status:** PROPOSED — preparatory contract handoff, not implementation acceptance
- **Normative source if approved:** [Web sub-spec](subspec-01-web-mvp.md)
- **Parent:** [Umbrella MVP-01](../umbrella_spec_melliatlas.md#mvp-01--working-sustainable-beekeeping-mvp)
- **Implementation authorization:** PENDING developer approval and state selection

The next task is a **first runnable browser vertical slice**, not a wholesale frontend or historical Admin port. Only interfaces consumed by that slice are designed here; later evidence filters, routes and generic UI frameworks are not predesigned.

## 1. Verified backend boundary (current implementation)

| Operation | Existing contract | Consumer behavior |
| --- | --- | --- |
| `GET /api/v1/territories/countries` | `list[CountryResponse]`, RU/BY; no claim of reference readiness | Show country options; region availability is separate |
| `GET /api/v1/territories/regions?country=RU|BY` | `list[TerritoryResponse]`; `422`, `503` | Render versioned references or a precise unavailable state |
| `GET /api/v1/territories/districts?region_id=...` | `list[TerritoryResponse]`; `404`, `409`, `422`, `503` | Navigate only supported depth; do not make an empty list imply complete coverage |
| `GET /api/v1/territories/geometry/{territory_id}` | `GeometryResponse` with WGS84 geometry and reference ID; `404`, `422`, `503` | Render only validated geometry; fallback to textual selection |
| `POST /api/v1/investigations` | `InvestigationCreateDto`, returns `202` + `InvestigationResponse` | Submit season and optional private starting point in the body; retain UUID |
| `GET /api/v1/investigations/{id}` | `InvestigationResponse`; `404`, `422`, `503` | Poll/reopen without replaying POST; stop at terminal state |

`InvestigationResponse` includes `status`, nullable `outcome` and `plan`, `synthetic`, `evidence`, `limitations`, `decision_trace`, nullable `replanning` and nullable `treatment_review`. For the joint fixture, both findings are present; `replanning` includes `assessments` and typed `decisions`, while `treatment_review` includes source record IDs, reported product claims, proposed application times, proximity and warnings. The private `starting_point` occurs only in the create DTO, not the response request echo.

**Concrete consumer fixture for the first slice:** `country=RU`, `territory_id=ru:region:smolensk`, `scenario_id=synthetic-ru-2026-v04-ecology-treatment`, season `2026-05-01` through `2026-08-15`. This is an explicitly synthetic RU demonstration, **not** a substitute for the unfinished RU/BY reference catalogs or source discovery API. These identifiers and dates are for the fixture selector, not hardcoded domain decisions.

Source declarations: [`api/routes_investigations.py`](../../../backend/src/melliatlas/api/routes_investigations.py), [`api/routes_territories.py`](../../../backend/src/melliatlas/api/routes_territories.py), [`api/contract.md`](../../../backend/src/melliatlas/api/contract.md), [`sources/api.py`](../../../backend/src/melliatlas/sources/api.py). Existing OpenAPI is the wire-schema source of truth. No duplicated handwritten HTTP schema may silently diverge from it.

## 2. W01 — first Web implementation slice (next, pending approval)

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

The first slice uses only existing POST/GET operations and additive nullable response fields. No new backend endpoint is required for a fixture-only demo. Full region/district navigation, sources/scenarios discovery and true post-restart result durability are separate backend gaps, not reasons to invent data in React. Do not persist `starting_point` in URLs, browser storage, logs or telemetry. The URL may contain only an opaque investigation ID.

#### Contract-first tests

1. `WEB-T001`: a browser submit/poll/reopen test observes the joint fixture's completed stops, treatment findings, ecology decisions and synthetic banner (`R03`–`R07`).
2. `WEB-T002`: map and timeline selection agree on one stop; textual navigation still works if map tiles fail (`R05`, `R08`).
3. `WEB-T003`: `404/422/503`, no-plan, `FAILED`, abort and stale response are distinct (`R04`, `R08`).
4. `WEB-T004`: mobile, keyboard and privacy checks cover touch controls, source labels and no private point in URL/logs (`R01`, `R07`, `R08`).
5. `WEB-T005`: RU/BY and unsupported geometry cases are driven by API responses, never fabricated catalogs (`R02`).

**Exit evidence:** runnable `web/` client with strict TS typechecks, component tests, browser E2E for the fixture scenario and preserved backend regressions. This preparation alone produces no UI and meets none of these acceptance scenarios.

**Approval gates:** developer approval of the Web sub-spec and workstream state, approved runtime/dev dependencies for React/Leaflet/Vite/test tooling, and explicit local browser test setup. Do not switch `STATE.json`, claim acceptance, or publish live source data during preparation.

## 3. Follow-on work (do not predesign)

| Order | Slice | Dependency and unresolved decision |
| --- | --- | --- |
| W02 | Territory navigation and validated geometry layers | Approved, complete RU/BY references and correct `409/503` handling; real data availability must be proven |
| W03 | Treatment timelines and source transparency polish | Validate the exact server DTOs and distinguish source notices from spatial screening and unknown wind |
| V05 backend | Source/scenario discovery and complete HTTP contract handoff | Current API does not expose `/api/v1/sources` or `/api/v1/scenarios`; plan and contract-test these on the backend workstream |
| V04 backend | Minimal typed source/analyzer execution | Required for full MVP-01 backend acceptance, but need not block the first browser demo |

No generic frontend state framework, map drawing engine, Admin workspace or speculative API is part of W01.
