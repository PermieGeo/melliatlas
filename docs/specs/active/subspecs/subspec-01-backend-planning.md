# MVP-01 Backend — Territory, Evidence, Analysis, and Investigation API

- **Stage:** `MVP-01` — Working sustainable-beekeeping MVP
- **Workstream:** `mvp-01-backend`
- **Status:** Active
- **Requirements approval:** Approved for `MVP-01` backend scope; unresolved external decisions remain explicit
- **Implementation authorization:** Active workstream authorized; task-specific external gates remain open
- **Acceptance:** Pending; no complete backend acceptance criterion or overall `MVP-01` stage accepted
- **Normative parent:** [MelliAtlas umbrella](../../umbrella_spec_melliatlas.md), especially `MVP-01.R01`–`R14`, `MVP-01.A01`–`A09`, and applicable `SYS-01`–`SYS-20`
- **Linked advisory plan:** [Backend implementation plan](subspec-01-backend-planning_implementation_plan.md)
**Next dependent sub-spec:** MVP-01 React/Web interface; not yet activated or written

## 1. Purpose and boundary

Deliver the **backend half of the first working product**: real dated RU/BY administrative geography, a controlled synthetic apiary season, explicitly fixture-only public-web/Saturn evidence capabilities, typed analysis, a small executable dependency graph, evidence-driven deterministic replanning, PostgreSQL/PostGIS persistence of completed investigations, and an HTTP contract ready for one React client. Backend success is necessary but **not sufficient** for completing umbrella stage `MVP-01`: the separate Web sub-spec and its browser acceptance tests follow the backend contract.

The product is for migratory beekeepers **and** must account for conservation of wild pollinators. No backend endpoint may call synthetic evidence a live observation, treat precautionary ecological evidence as a legal prohibition, or certify a location as safe or legally available.

### 1.1. Actors and scenarios

- **Beekeeper:** selects RU or BY, an available region (and district only in the two pilot oblasts), a season, and launches or reopens a synthetic study.
- **Backend investigation controller:** validates input, initiates bounded analysis, persists the completed result, and reports status and failures.
- **Agent:** first considers forage opportunity, then observes a separate restriction assessment, revises a proposed placement if warranted, and explains that decision.
- **Conservation reviewer:** can inspect each exclusion, caution, unknown, evidence category, and provenance through the same public read contract; no privileged admin or research workflow is part of this sub-spec.

### 1.2. In scope

1. Python package, FastAPI application and versioned JSON API, with typed input/output validation.
2. Dated, inspectable, **complete first-order region catalogs** for Russia and Belarus, including Minsk city, and **complete administrative district catalogs** for Smolensk Oblast and Vitebsk Oblast from a declared reference snapshot. Validated GeoJSON/WGS84 boundaries for the supported country/region/district navigation. Other first-order regions do not promise district coverage.
3. Provider-neutral territory identifiers and a reproducible reference-data import with coverage and provenance diagnostics; verification against independently defined source inventories rather than invented hardcoded counts.
4. Three registered source categories: cartography in RU/BY, public web/news in RU/BY, Saturn in RU only. Public-web and Saturn **must be fixture-only or unavailable**; no live HTTP requests to those providers at this stage.
5. Small synthetic study data covering at least three candidate sites, illustrative forage intervals, one explicit *fictional binding-for-demo* exclusion, and one *fictional precautionary* area.
6. Typed Source/Analyzer contracts, a registry, dependency-ordered execution, bounded agent observation/replanning, an ordered proposal containing at least two stops and one relocation, diagnostics and reproducible explanation.
7. PostgreSQL/PostGIS-backed completed investigation results and selected geospatial data, with a read endpoint usable after browser refresh or backend restart.
8. API contract and independent tests for correctness, failures, boundaries, architecture and database integration.

### 1.3. Explicit non-goals

- React implementation, UI styles, browser E2E, or a second administration frontend (deferred to the separate MVP-01 Web sub-spec).
- Live websites, unrestricted crawling, live Saturn API access, meteorology, real treatment data, or real apiary placement advice (`MVP-02` or later).
- Accurate honey yield, validated biodiversity impact scores, traffic routing, protected-area legal inference from labels/buffers, and public sharing of private coordinates.
- User accounts, per-user authorization, public deployment, multi-tenancy, durable distributed queues, crash recovery of *unfinished* jobs, or LLM planning.
- A general workflow-plugin platform, dynamic code execution, arbitrary generated expressions, and externally supplied DAG definitions.

## 2. Information model and invariants

### 2.1. Geography

- `CountryCode`: finite values `RU`, `BY`.
- `TerritoryKind`: `COUNTRY`, `REGION`, `DISTRICT`.
- `TerritoryId`: stable, opaque, canonical MelliAtlas ID; never an OSM, Saturn, administrative or database-provider ID masquerading as a canonical ID.
- `Territory`: `{id, country, kind, name, parent_id, reference_id, valid_on, geometry_status}`.
- `TerritoryGeometry`: WGS84 GeoJSON `Polygon`/`MultiPolygon`, SRID 4326, source and precision metadata; a missing/invalid shape has an explicit diagnostic, never a fabricated polygon.
- `ReferenceManifest`: immutable `{dataset_id, publication_or_snapshot_date, retrieved_at, origin_url_or_record, license, sha256, declared_coverage, coordinate_system, normalization_version}`.

Expected relations: region parent is its country; pilot district parent is its designated oblast. Region IDs are stable under repeated import of the same manifest. Spatial coverage must be complete against the selected reference inventory, and omissions/ambiguities must fail coverage verification. Distinct administrative **districts**, municipal entities and city jurisdictions must not be merged without an explicitly approved equivalence.

**Unresolved external prerequisite:** the dated and legally reusable RU/BY catalogs and boundary sources have not yet been verified in the current scaffold. Selecting source(s), their administrative interpretation, licensing and coverage is an approval gate before claiming `MVP-01.A06/A09`. The implementation must not invent names, counts, geometry, or missing regions.

### 2.2. Evidence and sources

- `SourceKind`: `CARTOGRAPHY`, `PUBLIC_WEB`, `SATURN`.
- `SourceMode`: `REFERENCE`, `FIXTURE`, `UNAVAILABLE` in `MVP-01`. `LIVE` is reserved for a later stage and must never be advertised as available in this release.
- `EvidenceKind`: `ADMIN_BOUNDARY`, `FORAGE_WINDOW`, `CANDIDATE_SITE`, `DEMO_RESTRICTION`, `DEMO_PRECAUTION`, `PUBLICATION_SAMPLE`, `SATURN_SAMPLE`.
- `EvidenceRecord`: stable ID, evidence kind, origin category/source ID, source mode, `synthetic` flag, effective interval, geographical scope, retrieval/snapshot timestamp, reference version and meaningful uncertainty.
- `SourceDescriptor`: source ID, kind, applicable country set, mode and supported evidence kinds. Saturn is never applicable to `BY`.

The API differentiates **real reference geography** from **synthetic planning facts**, even if they share a map. A publication fixture is neither an observed pesticide application nor a verified legal restriction. A Saturn fixture is not evidence that live access is permitted. Fixture source execution must perform **zero outbound provider requests**.

### 2.3. Planning domain

- `ApiaryStart`: proposed private starting coordinate, synthetic in the demo; never returned in an unrestricted production export by implication.
- `CandidateSite`: stable fixture ID, WGS84 coordinate, territory ID and optional display label.
- `TimeWindow`: inclusive date interval with `start <= end` and an explicit planning season.
- `ForageOpportunity`: site ID, window, qualitative level (`LOW`, `MEDIUM`, `HIGH`), provenance and synthetic flag.
- `SiteAssessment`: site ID, `ELIGIBLE`, `EXCLUDED` or `CAUTION`; evidence IDs, rule ID, reasons and unknowns. `EXCLUDED` requires an applicable **explicit synthetic demo rule**; proximity alone must not create a purported legal prohibition.
- `SeasonStop`: site ID, proposed time window, rationale and linked evidence IDs.
- `SeasonPlan`: ordered stops (minimum two for the successful demo), at least one transition, excluded candidates, optional alternatives and warnings; no numeric honey yield.
- `DecisionTrace`: initial candidate/order, evidence-requested check, observed assessment, revision or bounded termination, and final rationale.

Plan windows must fit the requested season, be chronologically ordered and must not overlap in ways the MVP cannot justify. A plan with fewer than two valid stops is **not a supported recommendation**: complete the analysis with an explicit insufficient/no-alternative outcome and causes, rather than reporting a technical execution error. Deterministic tie-breaking is required for repeatable tests.

### 2.4. Jobs and persistence

- `InvestigationStatus`: `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`; describes technical execution and persistence, not whether a viable seasonal plan was found.
- `InvestigationOutcomeKind`: `PLAN_FOUND`, `INSUFFICIENT_EVIDENCE`, `NO_FEASIBLE_ALTERNATIVE`. A technically completed investigation may have any of these outcomes. `FAILED` is reserved for execution or persistence failure; an unsupported recommendation is never fabricated.
- `InvestigationRequest`: country, canonical selected territory ID, season window, fixture scenario ID, optional synthetic apiary starting point.
- `InvestigationSnapshot`: opaque UUID, status, validated request, timestamps, optional plan, decision trace, evidence summaries, geography/reference version and diagnostics.
- Store completed result transactionally, including the planned stops and geometries necessary to reopen the result.
- A completed investigation is immutable as a historical record; a new run creates a new ID.
- In-process execution is acceptable for the initial MVP. Do not promise recovery of in-flight jobs after process termination. A terminal status must not falsely indicate success if saving failed.

## 3. Public backend operations

The endpoint names below are the approved **normative external contract for the MVP-01 Web client**. The existing territory routes and their HTTP contract are authoritative for already implemented behavior; source and investigation operations are not yet implemented. Additive changes require contract review before the Web client depends on them.

| ID | HTTP operation | Required behavior |
| --- | --- | --- |
| `BE-API-01` | `GET /api/v1/territories/countries` | Return available `RU` and `BY` codes and display metadata. |
| `BE-API-02` | `GET /api/v1/territories/regions?country=RU\|BY` | Return complete first-order regions for the selected dated reference. |
| `BE-API-03` | `GET /api/v1/territories/districts?region_id=...` | Return full Smolensk/Vitebsk district catalogs; other regions explicitly indicate `not_supported`, never an invented empty-completeness claim. |
| `BE-API-04` | `GET /api/v1/territories/geometry/{territory_id}` | Return valid GeoJSON geometry and provenance, or a structured error/diagnostic if absent. |
| `BE-API-05` | `GET /api/v1/sources?country=RU\|BY` | List applicable source descriptors, modes and fixture limitations; never list Saturn for BY. |
| `BE-API-06` | `GET /api/v1/scenarios` | Return the approved synthetic demonstration scenarios and supported territories. |
| `BE-API-07` | `POST /api/v1/investigations` | Validate and start a bounded synthetic investigation; return a stable ID and initial/current status. |
| `BE-API-08` | `GET /api/v1/investigations/{id}` | Return status, optional completed plan, trace, evidence limitations, and deterministic error envelope. |
| `BE-API-09` | `GET /health` | Confirm that the API process is responding; no claim that all external providers are live. |

### 3.1. Boundary validation and error model

- JSON requests/responses use typed schemas; unsupported country, invalid dates, unknown canonical territory, unsupported district depth, wrong scenario/country, impossible window, invalid coordinates and malformed geometry are rejected or reported explicitly.
- Coordinates use GeoJSON `[longitude, latitude]` order; latitude is within `[-90,90]`, longitude within `[-180,180]`. Never calculate meter distances directly on raw degrees.
- Responses distinguish HTTP validation (`400`/`422`), absence (`404`), unsupported capability (`409`), unprocessable investigation (`422`), internal failures (`500`), and a still-running investigation (`200` status payload or appropriately documented `202` on creation).
- All failure responses use `{error: {code, message, details?}}`; error codes are a finite enum. No stack traces, database details, exact private coordinates or credentials are included in client errors.
- Completed analysis without a supported plan is a domain outcome (`INSUFFICIENT_EVIDENCE` or `NO_FEASIBLE_ALTERNATIVE`), not an execution failure. The investigation response includes that outcome separately from the technical status.
- OpenAPI must expose schemas for the operations and enums; internal Python objects are not serialized ad hoc.

## 4. Requirement-to-umbrella mapping

| Backend requirement | Observable obligation | Umbrella anchors | Feature IDs |
| --- | --- | --- | --- |
| `MVP01-BE-R01` | App starts, validates and serves versioned OpenAPI. | `MVP-01.R01`, `A04` | `WEB.INVESTIGATIONS` (API surface only) |
| `MVP01-BE-R02` | Both complete first-order catalogs plus Minsk city use dated references. | `R10`, `A06` | `GEOGRAPHY.RU_REGIONS`, `GEOGRAPHY.BY_REGIONS` |
| `MVP01-BE-R03` | Complete Smolensk/Vitebsk district catalogs and explicit unsupported depth elsewhere. | `R11`, `R14`, `A06` | `GEOGRAPHY.PILOT_DISTRICTS` |
| `MVP01-BE-R04` | Valid WGS84 boundary geometries, provenance and repeatable imports. | `R12`, `A07`, `A09` | `MAP.BASEMAP`, `DATA.PROVENANCE` |
| `MVP01-BE-R05` | Country-specific source registry; no live publication/Saturn I/O. | `R13`, `A08` | `SOURCES.CATALOG`, `SOURCES.PUBLIC_WEB_RU`, `SOURCES.PUBLIC_WEB_BY`, `SOURCES.SATURN_RU` |
| `MVP01-BE-R06` | Three or more synthetic candidate sites and dated forage fixtures. | `R02`, `R05` | `SOURCES.SYNTHETIC` |
| `MVP01-BE-R07` | Typed Source/Analyzer registry and validated dependency graph. | `R03`, `A04` | `ENGINE.TYPED_CAPABILITIES`, `ENGINE.DAG_EXECUTION` |
| `MVP01-BE-R08` | Deterministic additional evidence check and causally recorded replanning. | `R04`, `A02` | `AGENT.DETERMINISTIC_REPLAN`, `AGENT.EVIDENCE_TRACE` |
| `MVP01-BE-R09` | Synthetic restriction excludes; precaution qualifies, never prohibits by itself. | `R05`, `A03` | `ECOLOGY.RESTRICTIONS`, `ECOLOGY.ALTERNATIVES` |
| `MVP01-BE-R10` | Ordered two-stop plan and at least one relocation; explain outcomes. | `R06`, `A01` | `PLANNING.SEASONAL_STOPS` |
| `MVP01-BE-R11` | Completed records persist in PostGIS and reopen by stable ID. | `R07`, `A01`, `A04` | `DATA.PERSISTENCE` |
| `MVP01-BE-R12` | Bounded, observable investigation execution with failure diagnostics. | `R09`, `A04` | `JOBS.EXECUTION` |
| `MVP01-BE-R13` | Typed REST contract exposes territory, source, investigation and plan reads. | `R08`, `R14`, `A07` | `WEB.INVESTIGATIONS`, `WEB.MAP_TIMELINE` (API surface only) |
| `MVP01-BE-R14` | Synthetic versus real reference status and traceability survive serialization. | `R02`, `R13`, `A05` | `DATA.PROVENANCE`, `AGENT.EVIDENCE_TRACE` |
| `MVP01-BE-R15` | Unknown, missing, mismatched and malformed inputs yield explicit failures or uncertainty. | `R09`, `SYS-02`, `SYS-07` | `ENGINE.TYPED_CAPABILITIES` |
| `MVP01-BE-R16` | No provider internals cross modules; resources are injected and closed. | `SYS-16`, `SYS-17` | `ENGINE.TYPED_CAPABILITIES` |
| `MVP01-BE-R17` | Architecture, contracts, database and boundary tests run from project checks. | `A04`, `A06`–`A09` | All backend capabilities above |

**Interpretation:** backend requirements do not claim completion of umbrella `MVP-01.R08` or browser acceptance `MVP-01.A01/A07`. Those remain dependent on the future MVP-01 Web sub-spec.

## 5. Required acceptance evidence

| Acceptance ID | Testable observation |
| --- | --- |
| `MVP01-BE-A01` | Versioned API starts and its OpenAPI schemas match the documented request, result and error shapes. |
| `MVP01-BE-A02` | Data manifest and independent reference inventory confirm every RU/BY first-order region and every district in Smolensk/Vitebsk; repeat import keeps identifiers stable and identifies missing entries. |
| `MVP01-BE-A03` | Map boundaries are valid, attributed and linked to canonical territories; unknown geometries give diagnostics and never fake polygons. |
| `MVP01-BE-A04` | Source registry for RU/BY exposes geography/public web; Saturn only in RU; fixture web/Saturn attempts make zero outbound calls. |
| `MVP01-BE-A05` | Engine orders dependencies, rejects cycles, missing operators and incompatible artifact types, and propagates failures. |
| `MVP01-BE-A06` | At least one scenario initially favors a later-excluded candidate, triggers a separate restriction check, and records an evidence-caused alternative decision without a hardcoded candidate-ID rule. |
| `MVP01-BE-A07` | A precautionary finding remains non-binding; unknown condition is explicit; missing viable stops terminates without fabricated recommendation. |
| `MVP01-BE-A08` | A valid run with sufficient evidence returns an ordered seasonal plan with two stops, one transition, bounded decisions, evidence references and explicit synthetic disclaimers; a completed but unsupported plan reports its distinct domain outcome. |
| `MVP01-BE-A09` | A completed plan with geometry and trace can be retrieved from a fresh API/database session; failed transaction cannot appear completed. |
| `MVP01-BE-A10` | Country/territory/geometry/date/scenario errors, engine faults and step limits produce stable, sanitized diagnostics. |
| `MVP01-BE-A11` | Automated tests enforce allowed module dependencies, public API imports, acyclic graph and provider/transport isolation. |
| `MVP01-BE-A12` | Backend's external schemas, fixture outputs and limitations are documented for the dependent frontend sub-spec; the stage itself remains incomplete until Web acceptance. |

## 6. Test and quality constraints

- Every public module contract requires positive, boundary and negative API tests. Each test must cite at least one `MVP01-BE-Rxx` and an observable outcome, not merely that the call returned without exception.
- Tests must be initially failing after public API stubs exist and before logic is implemented; no placeholder `assert False`, skipped assertions, or tests based solely on mocked persistence/HTTP semantics.
- Pure tests may use isolated fixtures. PostGIS geometry, migration, SQL and persistence claims require a real PostgreSQL/PostGIS test database. Real RU/BY catalog completeness requires verified source snapshots and their independent inventories; a tiny mock catalog is insufficient.
- No automated test may call live public-web, Saturn, or uncontrolled map-provider endpoints. Controlled fixtures must make the distinction apparent in response payloads and test names.
- Runtime dependencies and relaxation of approved enforcement constraints require explicit approval. Task-scoped development tooling may be justified and added without weakening checks. Changes to `AGENTS.md` require an explicit developer request.
- The dependent frontend stage must separately test browser navigation, map overlays, timeline and saved-investigation behavior.

## 7. Outstanding decisions / approval gates

The following remain **task-specific approval gates** even though the backend workstream is authorized:

1. Select the reference-date, license-compatible and complete territory/boundary datasets for Russia and Belarus, including how the source represents administrative boundaries or contested/ambiguous units; record coverage statements rather than political or administrative assumptions.
2. Select the exact synthetic season, Smolensk/Vitebsk scenario sites, forage fixture intervals and demonstration-only exclusion/precaution rules; ensure fictional values are never presented as real environmental restrictions.
3. Approve runtime dependency additions, supported Python version, database access/migration tooling and geometry validator. Justify task-scoped development/test tooling without weakening existing checks.
4. Approve the exact API request/response envelope and whether MVP-01 runs synchronously or through a bounded in-process task queue. Both must preserve stable investigation identifiers and completed-result retrieval.
5. Confirm local PostGIS startup/testing mechanism and how licensed boundary datasets are acquired and pinned without packaging runtime/private data into patches.

**Authorization checkpoint:** Developer-approved backend requirements and implementation authorization are in effect for the active `MVP-01` backend workstream. This authorization does not approve missing reference sources, licenses, runtime dependencies, or database arrangements listed above. Steps 1 and part of 2 have implementation; no full backend acceptance criterion is verified. The `MVP-01` stage remains unaccepted until the separate Web workstream and browser checks are complete.

