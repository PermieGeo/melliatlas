# MVP-01 Backend — Implementation Plan

- **Status:** Active; implementation partially complete
- **Requirements approval:** APPROVED — active backend sub-spec
- **Implementation authorization:** AUTHORIZED — backend workstream; external approvals are task-specific
- **Acceptance:** PENDING — no full backend acceptance criterion has been signed off
- **Stage/workstream:** `MVP-01` / `mvp-01-backend`
- **Normative sub-spec:** [MVP-01 Backend requirements](subspec-01-backend-planning.md)
- **Parent:** [MelliAtlas umbrella](../../umbrella_spec_melliatlas.md)

The [active backend sub-spec](subspec-01-backend-planning.md) owns normative behavior and acceptance; this plan records **current implementation choices, public-boundary design, task sequencing, and test oracles**. The [specification guidance](../../AGENTS.md) governs contract-first design and approval. Section 4.1 records the V04-01 pure fictional ecology boundary; implemented code and contract tests, not this plan, remain authoritative.

## 1. Current implementation evidence

| Capability | Verified implementation boundary | Remaining acceptance work |
| --- | --- | --- |
| HTTP bootstrap and investigations | [`api/app.py`](../../../../backend/src/melliatlas/api/app.py), [`api/routes_investigations.py`](../../../../backend/src/melliatlas/api/routes_investigations.py), and [`api/contract.md`](../../../../backend/src/melliatlas/api/contract.md); health, OpenAPI, injected dependencies, synthetic POST/GET and typed investigation errors | Planned source routes and full MVP OpenAPI/contract acceptance (`MVP01-BE-A01`, `A12`) |
| Territory model and catalog | [`territories/api.py`](../../../../backend/src/melliatlas/territories/api.py), [`territories/contract.md`](../../../../backend/src/melliatlas/territories/contract.md); offline validation, in-memory catalog and versioned reads | Approved complete RU/BY references, verified topology/precision, PostGIS adapter (`A02`, `A03`) |
| Architecture guard | [`backend/tests/architecture/test_module_boundaries.py`](../../../../backend/tests/architecture/test_module_boundaries.py) | Runtime no-network, DI and integration enforcement (`A11`) |
| Synthetic planning, fixture source, and jobs | [`planning/api.py`](../../../../backend/src/melliatlas/planning/api.py), [`sources/api.py`](../../../../backend/src/melliatlas/sources/api.py), [`jobs/api.py`](../../../../backend/src/melliatlas/jobs/api.py); synthetic V01 and optional completed-result store port | Real ecology, agent, typed DAG, durable in-flight jobs, Web and full acceptance remain pending |
| Completed-snapshot persistence (partial) | [`persistence/api.py`](../../../../backend/src/melliatlas/persistence/api.py), [`persistence/contract.md`](../../../../backend/src/melliatlas/persistence/contract.md), [migration](../../../../backend/migrations/0001_completed_investigations.sql) | Real PostGIS migration, rollback, geometry and fresh-connection tests (`MVP01-BE-A09`) |

Implemented APIs are defined by their linked Python source and `contract.md`, **not** by future design notes. `create_app(*, settings=..., territories=..., investigations=...)` retains its earlier `settings`, `territories` and `investigations` keyword arguments. Opt-in reference-file paths are configured through `AppSettings` and validated on startup. Territory URLs include `/api/v1/territories/districts?region_id=...` and `/api/v1/territories/geometry/{territory_id}`. No real complete geography has been imported. No acceptance test may infer complete regional coverage from the synthetic fixtures.

## 2. Ownership and dependency constraints

| Module | Responsibility | Permitted peer-module dependencies |
| --- | --- | --- |
| `territories` | Canonical territory IDs, reference provenance, geometry | None |
| `planning` | Site/season models, planning invariants and policy | `territories` |
| `sources` | Source descriptors, fixture acquisition, evidence normalization | `territories`, `planning` |
| `analyzers` | Pure deterministic calculations and evaluations | `territories`, `sources`, `planning` |
| `engine` | Typed dependency ordering and artifact validation | `sources`, `analyzers`, `planning` |
| `agent` | Bounded evidence-triggered decisions and replanning | `engine`, `planning`, `sources` |
| `jobs` | Investigation request, status, results and lifecycle | `agent`, `engine`, `planning`, `territories` |
| `persistence` | Concrete database stores and migrations | `jobs`, `territories` |
| `api` | HTTP DTOs, routes, errors, composition | Public APIs of other modules |

The automated import matrix lives in `backend/tests/architecture/import_policy.py`. Peer modules may import only exposed `api.py` interfaces or deliberate public package facades. Domain logic must not import FastAPI, SQL implementations or network clients; `api` is a composition boundary. No cycles, hidden service locators, arbitrary submitted DAG definitions or live public-web/Saturn I/O in `MVP-01`. Explicitly inject I/O collaborators. For the names `forage`, `ecology` and `season`, **planning owns domain policy**, **analyzers owns calculations**, and **agent owns decisions about re-evaluation**. Do not create a `common` package without independently identified consumers.

## 3. Technical decisions for upcoming slices

The [normative information model](subspec-01-backend-planning.md#2-information-model-and-invariants), [HTTP obligations](subspec-01-backend-planning.md#3-public-backend-operations), and [approval gates](subspec-01-backend-planning.md#7-outstanding-decisions--approval-gates) live in the sub-spec. Do not redefine their enumerations, evidence fields, exclusion rules, persistence guarantees or acceptance thresholds here. Use the relevant requirement IDs when selecting a task.

The remaining **technical choices** should be reviewed at the task that first needs them:

- **Execution (`V04`):** start with a bounded typed sequence; introduce a dependency DAG only if actual operations need it. If a DAG becomes necessary, distinguish `SourceStep(source_id)` from `AnalyzerStep(analyzer_kind)` and test artifact binding, ordering and cycle rejection instead of building a generic workflow platform.
- **Ecology and replanning (`V04`):** place eligibility policy in `planning`, pure spatial evaluation in `analyzers`, and decisions about additional evidence in `agent`. Use the actual geometry evaluation output to trigger replanning; do not couple policy to candidate labels. Select exact typed contracts only when `V04` becomes current.
- **Geographic import (`V03`):** choose the catalog-loading and reference-version selection boundary when approved datasets exist. The existing [`import_reference.py`](../../../../backend/scripts/import_reference.py) validates normalized files offline. V03 now also supports explicit local-file loading at ASGI startup; neither path writes to PostGIS or verifies supplier approval.

## 4. Next bounded delivery task

- **Task ID:** `MVP01-BE-V04`
- **Status:** Implemented; acceptance pending
- **Goal:** Provide a typed, offline and deterministic first ecology screening boundary: find explicit fictional zone overlaps for candidate points, then classify their significance in planning without granting real-world eligibility or changing the current V01 workflow.
- **Requirement IDs:** `MVP01-BE-R09`, `MVP01-BE-R15`
- **Test inventory IDs:** `BE-T023`, `BE-T024`, `BE-T025`
- **Scope:** Pure WGS84 point-in-polygon calculations with GEOS, typed demonstration-only overlap evidence and policy results, stable evidence/rule identity, deterministic ordering, negative and boundary cases. No new dependency.
- **Not in scope:** Agent replanning, exclusion filtering in the V01 plan, source registry/transport, provider ingestion, verified real habitat boundaries, real legal interpretation or declaring any site safe.
- **Existing interfaces:** `backend/src/melliatlas/planning/api.py`, `backend/src/melliatlas/territories/api.py`, `backend/src/melliatlas/sources/api.py`.
- **Implemented files:** `backend/src/melliatlas/analyzers/api.py`, `backend/src/melliatlas/analyzers/contract.md`, `backend/src/melliatlas/planning/api.py`, `backend/src/melliatlas/planning/contract.md`, `backend/tests/unit/test_ecology_screening.py`.
- **Approval gates:** The authoritative demo zone choice, real-world datasets, license/source provenance and any legal interpretation remain developer-controlled under sub-spec section 7. No fictional geometry is approved as an actual protected area; real V03 geography and real V02 PostGIS acceptance remain open.
- **Exit evidence:** Pure tests establish `DEMO_RESTRICTION` → `EXCLUDED`, `DEMO_PRECAUTION` → `CAUTION`, missing/non-overlapping evidence → `UNKNOWN`, geometric boundary matches, candidate-ID-independent decisions, precedence, deterministic ordering and invalid-input rejection. No end-to-end replanning or full `MVP01-BE-A06/A07` acceptance is claimed.

### 4.1 Public contracts and integration design

This completed first V04 increment introduces only the typed geometry-to-policy seam needed now. The normative obligations are owned by [sub-spec section 2.3](subspec-01-backend-planning.md#23-planning-domain). Reviewed code, module contracts and executable tests are authoritative; the signatures below describe the implemented boundary and are not a second source of truth.

#### Public types and signatures

| Owner | Implemented typed declaration | Authoritative source |
| --- | --- | --- |
| `planning` | `EcologyEvidenceKind(StrEnum)` with `DEMO_RESTRICTION`, `DEMO_PRECAUTION`; `EcologyZone(evidence_id: str, rule_id: str, kind: EcologyEvidenceKind, geometry: GeometryWgs84)` | [`planning/api.py`](../../../../backend/src/melliatlas/planning/api.py) |
| `planning` | `EcologyOverlap(evidence_id: str, rule_id: str, kind: EcologyEvidenceKind)`; `EcologyStatus(StrEnum)`; `SiteAssessment(site_id: str, status: EcologyStatus, evidence_ids: tuple[str, ...], rule_ids: tuple[str, ...], reasons: tuple[str, ...], unknowns: tuple[str, ...], synthetic: Literal[True])` | [`planning/api.py`](../../../../backend/src/melliatlas/planning/api.py) |
| `analyzers` | `find_ecology_overlaps(site: CandidateSite, zones: tuple[EcologyZone, ...]) -> tuple[EcologyOverlap, ...]` | [`analyzers/api.py`](../../../../backend/src/melliatlas/analyzers/api.py) |
| `planning` | `assess_ecology(site_id: str, overlaps: tuple[EcologyOverlap, ...]) -> SiteAssessment` | [`planning/api.py`](../../../../backend/src/melliatlas/planning/api.py) |

#### Module interactions

1. A caller passes an existing `planning.CandidateSite` and explicit demo-only `EcologyZone` inputs to the pure `analyzers.find_ecology_overlaps`. The analyzer validates coordinates/topology and uses `Shapely/GEOS` point coverage, returning sorted typed observations, not policy decisions.
2. `planning.assess_ecology` consumes those observations and deterministically classifies the demo evidence. It cannot promote an absence of overlaps to `ELIGIBLE` because no complete independent ecological coverage has been verified. Its output records evidence IDs, rule IDs, reasons and unknowns.
3. Existing `jobs.InMemoryInvestigationService`, `planning.build_season_plan`, source fixture data, HTTP DTOs and PostGIS snapshots are **unchanged**. Later V04 increments must review the agent/job integration contracts before connecting actual replanning.

#### Failure contracts

- Invalid/non-finite site WGS84 coordinates, invalid zone topology or out-of-range geometry coordinates → `ValueError` at the pure analyzer boundary; this is not an HTTP error contract.
- Missing evidence/rule identifiers → explicit `ValueError`, never silent exclusion.
- No matching zone or no ecological observations → `UNKNOWN` with an explicit coverage limitation. `CAUTION` is never a binding exclusion. An explicit `DEMO_RESTRICTION` match takes precedence over caution **only within the fictional demonstration**.
- Real legal restrictions, real species impact, and external completeness are not inferred from synthetic polygons or absent evidence.

#### Compatibility

- No modifications to the V01 `CandidateSite`, `SeasonPlan`, `InvestigationService`, `create_app`, HTTP routes, PostGIS schema or persisted codec.
- Dependency direction: `analyzers -> planning, territories` (via public types), `planning -> territories`. The analyzer does not import planning private modules or perform I/O.
- Existing Shapely is reused; no new runtime package, registration framework or implicit source access.

#### Contract-first tests

- [`backend/tests/unit/test_ecology_screening.py`](../../../../backend/tests/unit/test_ecology_screening.py) proves explicit polygon overlap, boundary inclusion, caution/non-binding status, unknown coverage, precedence, ID rename independence, invalid geometry and missing evidence metadata (`BE-T023`–`BE-T025` partial).
- The architecture suite continues to check allowed module dependencies. These are not evidence of agent replan behavior (`BE-T035`–`BE-T039`), approved datasets, real legal exclusions or full ecological acceptance.

### 4.2 Implementation sequence (TDD)

1. Identify the two public ownership boundaries in the current sub-spec and dependency matrix; first add precise positive/negative/boundary tests using only explicit fictional polygons.
2. Implement a small pure GEOS point-overlap analyzer and domain-owned classification without data-provider access or automatic claims of site eligibility.
3. Run selected ecological tests, existing V01 regression tests, architecture and SDD checks; use local `FMT,CHK` for Ruff and strict Pyright. Report any unavailable tools.
4. Keep V04 behavior unconnected to V01 jobs until a further task selects the approved fictional scenario, validates the agent/investigation integration contract and includes deterministic end-to-end replan tests.

## 5. Upcoming vertical slices

The V04-01 pure ecology screening task is in section 4; the V03 runtime loader is already implemented but real geographic coverage remains incomplete. V02 real PostGIS verification remains an **independent pending acceptance gate**; completion of startup wiring does not discharge `BE-T040`–`BE-T044`. These later slices identify **implementation work**, not new requirements or approved designs. Their normative scope and external gates remain in [sub-spec sections 4–7](subspec-01-backend-planning.md#4-requirement-to-umbrella-mapping). Select and review public interfaces only when each slice becomes current.

| Slice | Implementation decision to make when selected | Planned test IDs |
| --- | --- | --- |
| `V03` — approved real geography (remaining) | Finish independent RU/BY inventories, verify full real coverage, and decide whether persistent multi-version reference storage is needed. The opt-in local runtime loader is implemented but not accepted as complete geography. | `BE-T001`–`BE-T012`, `BE-T058` |
| `V04` — evidence-driven replanning (remaining) | Connect the newly implemented pure overlap/policy boundary to an approved fictional scenario and a bounded decision loop; review agent/job interfaces first. | `BE-T013`–`BE-T039`, `BE-T054`–`BE-T059` |
| `V05` — backend/Web contract handoff | Verify source/investigation response schemas and fixture examples before the separately scoped Web slice consumes them. | `BE-T048`–`BE-T053`, `BE-T060` |

## 6. Acceptance test inventory

The 60 `BE-Txxx` entries are a **planned inventory**, not claims that each test has run. `U` = unit; `C` = public contract; `I` = real integration; `A` = architecture; `N` = negative; `B` = boundary. Each bounded task selects relevant IDs with independent oracles and records actual execution evidence.

| Test ID | Category | Module/API | Input / observable assertion | Requirement |
| --- | --- | --- | --- | --- |
| `BE-T001` | C | TerritoryCatalog.list_regions | RU inventory equals approved reference IDs, including all first-order types | R02 |
| `BE-T002` | C | TerritoryCatalog.list_regions | BY reference includes every oblast and Minsk city | R02 |
| `BE-T003` | C | TerritoryCatalog.list_districts | Smolensk districts match independent inventory and parent | R03 |
| `BE-T004` | C | TerritoryCatalog.list_districts | Vitebsk districts match independent inventory and parent | R03 |
| `BE-T005` | C/N | TerritoryCatalog | Nonpilot region reports unsupported detail, not empty-complete | R03 |
| `BE-T006` | C/N | TerritoryCatalog | Unknown territory returns missing diagnostic | R15 |
| `BE-T007` | C/I | TerritoryImport | Same manifest twice leaves stable keys and counts | R04 |
| `BE-T008` | I/N | TerritoryImport | Missing region/district inventory member fails completeness check | R02–R04 |
| `BE-T009` | I/N | TerritoryImport | Duplicate provider mapping or invalid parent is rejected | R03 |
| `BE-T010` | I/B | TerritoryGeometry | WGS84 Polygon/MultiPolygon geometry valid and SRID 4326 | R04 |
| `BE-T011` | I/N | TerritoryGeometry | Invalid ring, latitude, axis order or CRS produces explicit failure | R04 |
| `BE-T012` | I | ReferenceManifest | Reference checksum, date, origin, attribution persist | R04 |
| `BE-T013` | C | SourceRegistry.list_for_country | RU shows geography/web/Saturn with correct source modes | R05 |
| `BE-T014` | C | SourceRegistry.list_for_country | BY shows geography/web but no Saturn | R05 |
| `BE-T015` | C/N | Source.fetch | BY call to Saturn rejected without outgoing I/O | R05 |
| `BE-T016` | C/N | Source.fetch | Fixture web/Saturn scenarios make zero external requests | R05 |
| `BE-T017` | C | EvidenceRecord | Synthetic label, version, mode, timestamp, origin survive | R06/R14 |
| `BE-T018` | C/N | SourceRegistry.get | Unknown source ID gets typed error | R05/R15 |
| `BE-T019` | U/B | TimeWindow | Reversed/out-of-season dates rejected; a same-day inclusive interval is valid | R10/R15 |
| `BE-T020` | U | Planning candidate inputs | Input iteration order cannot change deterministic result | R10 |
| `BE-T021` | U | Forage analyzer | Known windows yield independently calculated opportunity overlaps | R06/R10 |
| `BE-T022` | U/B | Forage analyzer | Missing/partial flowering window stays unknown, not favorable | R09/R15 |
| `BE-T023` | U | Ecology analyzer | Explicit fictional exclusion intersecting site is binding **only** in demo | R09 |
| `BE-T024` | U | Ecology analyzer | Precautionary overlap yields caution, not legal rejection | R09 |
| `BE-T025` | U/N | Ecology analyzer | Unavailable ecology evidence does not default to safe | R09/R15 |
| `BE-T026` | U | Season analyzer | Two ordered stops and a relocation within one season | R10 |
| `BE-T027` | U/N | Season analyzer | Fewer than two usable stops returns insufficient outcome | R09/R10 |
| `BE-T028` | C | AnalyzerRegistry | Correct kind dispatches to declared input/output types | R07 |
| `BE-T029` | C/N | AnalyzerRegistry | Wrong input kind fails contract before execution | R07/R15 |
| `BE-T030` | C | DagExecutor | `SourceStep` invokes a registered source by ID, then `AnalyzerStep` invokes the declared analyzer kind once, in dependency order | R07 |
| `BE-T031` | C/N | DagExecutor | Cycle, duplicate ID, unknown dependency rejected | R07 |
| `BE-T032` | C/N | DagExecutor | Unknown `source_id`, unavailable `analyzer_kind`, or missing dependency artifact fails explicitly | R07/R15 |
| `BE-T033` | C/B | DagExecutor | Step/time limits terminate with typed diagnostic | R12/R15 |
| `BE-T034` | C/N | DagExecutor | Failing source/analyzer does not become successful artifact | R07/R15 |
| `BE-T035` | U | DeterministicPlanner | Exclusion evidence causes replan and alternative selection | R08/R09 |
| `BE-T036` | U/N | DeterministicPlanner | Candidate-ID rename does not bypass exclusion rule | R08 |
| `BE-T037` | U/N | DeterministicPlanner | No viable alternative yields no fabricated plan | R08/R15 |
| `BE-T038` | U | DeterministicPlanner | Precaution retains caution and evidence in trace | R08/R09 |
| `BE-T039` | U/B | DeterministicPlanner | Bounded replan stops and reports limit | R08/R12 |
| `BE-T040` | I | InvestigationStore | Completed result, evidence, decisions and geometry survive reconnect | R11 |
| `BE-T041` | I/N | InvestigationStore | Database failure rolls back; no completed state leaked | R11/R12 |
| `BE-T042` | I | InvestigationStore | Same result ID read twice returns identical historical snapshot | R11 |
| `BE-T043` | I | Migrations | Fresh PostGIS migration creates expected relations/spatial index | R11 |
| `BE-T044` | I/B | PostGIS query | Spatial geometry test uses valid SRID and metric-safe operation | R04/R11 |
| `BE-T045` | C | InvestigationService | Submit/get reaches terminal state with stable UUID | R12 |
| `BE-T046` | C/N | InvestigationService | Fault/timeout maps to FAILED with actionable code | R12/R15 |
| `BE-T047` | C/N | InvestigationService | Invalid request rejected before provider or DB side effects | R12/R15 |
| `BE-T048` | I | FastAPI OpenAPI | All nine public operations have typed request/response schemas | R01/R13 |
| `BE-T049` | I/N | FastAPI territories | Unsupported country/depth/unknown geometry maps to stable errors | R02–R04/R13 |
| `BE-T050` | I | FastAPI sources | RU/BY availability and synthetic mode serialized correctly | R05/R14 |
| `BE-T051` | I | FastAPI investigations | POST + GET returns two-stop plan, evidence and replan trace | R08/R10/R13 |
| `BE-T052` | I/N | FastAPI input | Bad dates, coordinates and scenario/country mismatch -> sanitized 4xx | R13/R15 |
| `BE-T053` | I/N | FastAPI failure | No traceback/credentials/private start coordinate in error body | R14/R15 |
| `BE-T054` | A | Dependency graph | No import cycles or private-module imports between peer modules | R16 |
| `BE-T055` | A | Pure domain | `territories`, `planning`, `analyzers`, `engine`, `agent` have no FastAPI/SQL imports | R16 |
| `BE-T056` | A | Provider boundary | Only `persistence` touches database; fixture sources have no outbound clients | R05/R16 |
| `BE-T057` | A | Runtime wiring | All I/O collaborators injected; no global mutable registry or service locator | R16 |
| `BE-T058` | I | Full authorized seed | Independent RU/BY+pilot reference coverage/integrity report passes | R02–R04 |
| `BE-T059` | I/N | Source descriptors | No source advertises a live Saturn/web integration in MVP-01 | R05/R14 |
| `BE-T060` | C | Handoff fixture | OpenAPI examples distinguish real geography and synthetic investigation | R13/R14 |

**Oracles:** independently captured approved reference inventories for `T001`–`T004/T058`; fixed expected geometry fixtures for `T010/T044`; manually reviewed synthetic scenarios for `T021`–`T027/T035`–`T039`; real test PostGIS instance for `T040`–`T044`; externally visible HTTP payloads for `T048`–`T053`; import graph results for `T054`–`T057`. A test against a mock repository is not evidence for database correctness.


## 7. Convergence review after each task

Apply the shared [SDD convergence rules](../../AGENTS.md) to the selected task; record only **task-specific evidence** here:

1. Link the task's requirement IDs, reviewed public boundaries and selected `BE-Txxx` cases to the actual changed paths, contract tests and results; report unrun integration checks explicitly.
2. Compare changed public signatures, HTTP errors, module imports and storage behavior with the source-of-truth code, OpenAPI and approved requirements; record justified deviations and any required review.
3. For V03, record the exact normalized reference and independent inventory identities, the failed-startup tests, runtime HTTP results and remaining external source/license approvals. Synthetic inventory success does not establish real RU/BY completeness.
4. Keep V02 PostGIS acceptance pending until `BE-T040`–`BE-T044` run against a real approved database. Update feature traceability only after implementation review, with separate human acceptance decisions.
5. If an actual reference validation or database check fails, record the offending input/migration, failing assertion and recovery before claiming any acceptance evidence.
