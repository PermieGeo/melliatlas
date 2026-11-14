# MVP-01 Backend — Implementation Plan

- **Status:** Active; implementation partially complete
- **Requirements approval:** APPROVED — active backend sub-spec
- **Implementation authorization:** AUTHORIZED — backend workstream; external approvals are task-specific
- **Acceptance:** PENDING — no full backend acceptance criterion has been signed off
- **Stage/workstream:** `MVP-01` / `mvp-01-backend`
- **Normative sub-spec:** [MVP-01 Backend requirements](subspec-01-backend-planning.md)
- **Parent:** [MelliAtlas umbrella](../../umbrella_spec_melliatlas.md)

The [active backend sub-spec](subspec-01-backend-planning.md) owns normative behavior and acceptance; this plan records **current implementation choices, public-boundary design, task sequencing, and test oracles**. The [specification guidance](../../AGENTS.md) governs contract-first design and approval. Section 4.1 maps the already implemented V02 contracts to code and tests; it is not another source of normative requirements.

## 1. Current implementation evidence

| Capability | Verified implementation boundary | Remaining acceptance work |
| --- | --- | --- |
| HTTP bootstrap and investigations | [`api/app.py`](../../../../backend/src/melliatlas/api/app.py), [`api/routes_investigations.py`](../../../../backend/src/melliatlas/api/routes_investigations.py), and [`api/contract.md`](../../../../backend/src/melliatlas/api/contract.md); health, OpenAPI, injected dependencies, synthetic POST/GET and typed investigation errors | Planned source routes and full MVP OpenAPI/contract acceptance (`MVP01-BE-A01`, `A12`) |
| Territory model and catalog | [`territories/api.py`](../../../../backend/src/melliatlas/territories/api.py), [`territories/contract.md`](../../../../backend/src/melliatlas/territories/contract.md); offline validation, in-memory catalog and versioned reads | Approved complete RU/BY references, verified topology/precision, PostGIS adapter (`A02`, `A03`) |
| Architecture guard | [`backend/tests/architecture/test_module_boundaries.py`](../../../../backend/tests/architecture/test_module_boundaries.py) | Runtime no-network, DI and integration enforcement (`A11`) |
| Synthetic planning, fixture source, and jobs | [`planning/api.py`](../../../../backend/src/melliatlas/planning/api.py), [`sources/api.py`](../../../../backend/src/melliatlas/sources/api.py), [`jobs/api.py`](../../../../backend/src/melliatlas/jobs/api.py); synthetic V01 and optional completed-result store port | Real ecology, agent, typed DAG, durable in-flight jobs, Web and full acceptance remain pending |
| Completed-snapshot persistence (partial) | [`persistence/api.py`](../../../../backend/src/melliatlas/persistence/api.py), [`persistence/contract.md`](../../../../backend/src/melliatlas/persistence/contract.md), [migration](../../../../backend/migrations/0001_completed_investigations.sql) | Real PostGIS migration, rollback, geometry and fresh-connection tests (`MVP01-BE-A09`) |

Implemented APIs are defined by their linked Python source and `contract.md`, **not** by future design notes. `create_app(*, settings=..., territories=..., investigations=...)` retains its earlier `settings` and `territories` keyword arguments. Territory URLs include `/api/v1/territories/districts?region_id=...` and `/api/v1/territories/geometry/{territory_id}`. No real complete geography has been imported. No acceptance test may infer complete regional coverage from the synthetic fixtures.

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
- **Geographic import (`V03`):** choose the catalog-loading and reference-version selection boundary when approved datasets exist. The current [`import_reference.py`](../../../../backend/scripts/import_reference.py) validates normalized files offline; it is not a PostGIS import adapter.

## 4. Next bounded delivery task

- **Task ID:** `MVP01-BE-V02`
- **Status:** Implemented; acceptance pending
- **Goal:** Verify the existing completed-result store and migration against an approved real PostgreSQL/PostGIS test database, including fresh-connection reopening, immutability, rollback and spatial geometry.
- **Requirement IDs:** `MVP01-BE-R04`, `MVP01-BE-R11`, `MVP01-BE-R12`
- **Test inventory IDs:** `BE-T040`, `BE-T041`, `BE-T042`, `BE-T043`, `BE-T044`
- **Scope:** Validate the already implemented jobs-owned store port, injected PostGIS adapter and SQL migration on a real test database. Preserve V01 behavior, HTTP privacy, completed-snapshot immutability and failed-write rollback; make code adjustments only for test-confirmed defects against reviewed contracts.
- **Not in scope:** Approved RU/BY reference ingestion, weather, durable queued/running worker state, background recovery, live providers, Web UI or declaring `MVP01-BE-A09` accepted without actual evidence.
- **Existing interfaces:** `backend/src/melliatlas/jobs/api.py`, `backend/src/melliatlas/persistence/api.py`, `backend/src/melliatlas/api/app.py`, `backend/src/melliatlas/api/routes_investigations.py`.
- **Already implemented files:** `backend/src/melliatlas/persistence/contract.md`, `backend/migrations/0001_completed_investigations.sql`, `backend/scripts/verify_postgis_investigations.py` and isolated codec, SQL adapter and HTTP tests.
- **Approval gates:** Developer approval of PostgreSQL driver, a dedicated PostGIS test database, migration privileges and operational database access. Existing Shapely validation does not replace database acceptance; no unapproved runtime driver is declared.
- **Exit evidence:** Real PostGIS checks prove completed result, evidence, trace and selected-site geometry survive a new connection; duplicate UUIDs cannot overwrite results; failed writes roll back; SRID and geometry constraints are verified. Until these run and pass, V02 remains **partial, not accepted**.

### 4.1 Public contracts and integration design

This section covers **only the current V02 verification task**. The V01 and V02 public APIs already exist, so their source definitions and executable contracts are authoritative; the table below is an interface map, **not** a competing declaration to regenerate. No new public DTO, Protocol, method or error type is proposed for V02 verification. If a real-database test reveals a missing boundary, draft its exact typed declaration here, review its compatibility and obtain the required developer decision **before** generating implementation code. Do not predesign V03/V04 APIs.

#### Public types and signatures

| Layer / owner | Existing typed contract relevant to V02 | Authority |
| --- | --- | --- |
| HTTP boundary (`api`) | `InvestigationCreateDto` -> `InvestigationResponse` on `POST /api/v1/investigations` (202); `UUID` -> `InvestigationResponse` on `GET /api/v1/investigations/{id}` | [`api/routes_investigations.py`](../../../../backend/src/melliatlas/api/routes_investigations.py), [`api/contract.md`](../../../../backend/src/melliatlas/api/contract.md), generated OpenAPI |
| Application factory (`api`) | `create_app(*, settings: AppSettings \| None = None, territories: TerritoryCatalog \| None = None, investigations: InvestigationService \| None = None) -> FastAPI` | [`api/app.py`](../../../../backend/src/melliatlas/api/app.py) |
| Job lifecycle (`jobs`) | `InvestigationService.submit(request: InvestigationRequest) -> InvestigationSnapshot`, `get(identifier: UUID) -> InvestigationSnapshot \| None`, `process(identifier: UUID) -> None`; `InvestigationStatus` and `InvestigationOutcomeKind` remain separate | [`jobs/api.py`](../../../../backend/src/melliatlas/jobs/api.py), [`jobs/contract.md`](../../../../backend/src/melliatlas/jobs/contract.md) |
| Jobs-owned persistence port | `CompletedInvestigationStore.save(snapshot: InvestigationSnapshot) -> None`, `load(identifier: UUID) -> InvestigationSnapshot \| None`; only completed snapshots persist | [`jobs/api.py`](../../../../backend/src/melliatlas/jobs/api.py) |
| DB adapter (`persistence`) | `ConnectionFactory = Callable[[], DatabaseConnection]`, `PostgisCompletedInvestigationStore(connect: ConnectionFactory)` implements the jobs port; DB-API cursor/connection Protocols are already defined | [`persistence/api.py`](../../../../backend/src/melliatlas/persistence/api.py), [`persistence/contract.md`](../../../../backend/src/melliatlas/persistence/contract.md) |
| Storage format | Typed `serialize_completed_snapshot(snapshot: InvestigationSnapshot) -> str` and `deserialize_completed_snapshot(payload: str) -> InvestigationSnapshot`; immutable JSONB snapshot plus SRID-4326 `MULTIPOINT` | [`jobs/api.py`](../../../../backend/src/melliatlas/jobs/api.py), [migration](../../../../backend/migrations/0001_completed_investigations.sql) |

#### Module interactions

1. Application composition explicitly injects an `InvestigationService` into the HTTP router. The default `melliatlas.main:app` uses synthetic in-memory storage; no DB is silently enabled.
2. `POST` validates the DTO and calls `service.submit(...)`; an in-process background task invokes `service.process(id)`. A successful calculation is saved through `jobs.CompletedInvestigationStore` **before** the completed snapshot is published.
3. `persistence.PostgisCompletedInvestigationStore` opens a DB connection through the injected factory, writes JSONB and selected-site geometry in a transaction, commits once and closes resources. It does not own planning rules.
4. `GET` calls `service.get(UUID)`; a completed snapshot absent from process memory is loaded from persistence through a fresh connection. The HTTP boundary maps the domain snapshot to `InvestigationResponse`. Synchronous database access is offloaded from the event loop.
5. No planned `agent` or `engine` API is introduced by this task; full evidence-driven replanning is outside V02.

#### Failure contracts

| Condition | Existing typed/observable outcome | Required real-DB assertion |
| --- | --- | --- |
| Unsupported request | `InvalidInvestigationRequest` / validation error -> sanitized HTTP `422` | No DB write or completed record |
| Unknown investigation UUID | `InvestigationService.get(...)` returns `None` -> HTTP `404` | No synthetic success response |
| DB connection/read failure | `InvestigationStorageError` -> sanitized HTTP `503` on GET | No SQL, credentials or traceback returned |
| Insert/commit failure | `InvestigationStorageError`, rollback; service must not publish `COMPLETED` | Absent or unchanged stored record after failure |
| Duplicate completed UUID | Save fails without `UPDATE`/overwrite | Original payload remains byte-equivalent on reopen |
| Insufficient domain evidence | `COMPLETED` plus `INSUFFICIENT_EVIDENCE`, not `FAILED` | Historical outcome preserved after reopen |

#### Compatibility

- Preserve existing `create_app` keyword arguments (`settings`, `territories`) and additive optional `investigations` injection; do not replace the running V01 HTTP DTOs, routes, statuses or error envelope.
- Preserve the `jobs` -> port <- `persistence` dependency direction; `jobs` must not import DB drivers. Preserve synthetic source provenance, immutable historical IDs and completed-only persistence.
- A proposed new cross-module interface requires exact import path, Python typed declarations (DTOs/enum/Protocol and method signatures), returned errors, dependency direction, contract test examples and an explicit design-review outcome **before implementation**. Remove the draft after implementation and link to its actual code/tests; do not repeat it in the future backlog.

#### Contract-first tests

- **Existing executable contract checks:** [`test_completed_snapshot_codec.py`](../../../../backend/tests/unit/test_completed_snapshot_codec.py) validates typed JSON round trips and corrupt payloads; [`test_postgis_store_unit.py`](../../../../backend/tests/unit/test_postgis_store_unit.py) checks adapter transaction intent; [`test_persistent_investigation_service.py`](../../../../backend/tests/unit/test_persistent_investigation_service.py) checks save-before-completion and failed save; [`test_investigation_reopen_http.py`](../../../../backend/tests/contract/test_investigation_reopen_http.py) checks HTTP reopened results using an injected fake store. These are **not** DB acceptance evidence.
- **Pending independent real-DB contract verification:** run [`verify_postgis_investigations.py`](../../../../backend/scripts/verify_postgis_investigations.py) against a developer-approved test PostGIS after running the reviewed migration. Map `BE-T040` to fresh-connection JSON/evidence/trace/geometry reopen, `BE-T041` to rollback/no false completion, `BE-T042` to immutable duplicate UUID, `BE-T043` to migration/index creation, and `BE-T044` to SRID 4326 and metric-safe spatial operation.
- If a new contract is needed, write failing **positive, negative and boundary** contract tests against its reviewed typed public declaration before implementing it. Confirm the result through actual HTTP/DB checks where relevant. Passing fake-store tests or a generated ZIP never accepts `MVP01-BE-A09`.

### 4.2 Implementation sequence (TDD)

1. Obtain developer approval for the runtime PostgreSQL driver, isolated `_test` database, migration privileges and verification process. Do not install a driver or start database I/O implicitly.
2. Run the existing focused codec, SQL-adapter and HTTP tests; record their limits. Exercise real PostGIS with the migration and independent expected results for `BE-T040`–`BE-T044`.
3. For a real test failure, identify the broken contract, propose a bounded change to the current-task typed design, obtain any required review, then implement against a failing regression test. Avoid speculative new abstractions.
4. Run `sh ./run-format.sh`, `bash ./run-tests.sh`, and the approved real-DB test; record commands, environment, SQL migration identity, failures and recovery. Converge the contract docs and traceability without marking `verified` or advancing workstream acceptance without developer approval.

The V01 investigation slice remains implemented but unaccepted. Its fixed fictional RU/Smolensk scenario, in-process task, typed HTTP contract and temporary default store are covered by `backend/tests/contract/test_investigations_http.py` and `backend/tests/unit/test_synthetic_investigation.py`. V02 adds an opt-in completed-only persistence bridge without changing the default `melliatlas.main:app` configuration. Its typed codec, adapter transaction intentions, and fake-backed HTTP reopen tests are executable, but **none** establishes real PostGIS acceptance. `backend/scripts/verify_postgis_investigations.py` is an explicit real-database check to run only after the open approvals and environment prerequisites have been satisfied.

## 5. Upcoming vertical slices

The active V02 verification task is in section 4; these later slices identify **implementation work**, not new requirements or approved designs. Their normative scope and external gates remain in [sub-spec sections 4–7](subspec-01-backend-planning.md#4-requirement-to-umbrella-mapping). Select and review public interfaces only when each slice becomes current.

| Slice | Implementation decision to make when selected | Planned test IDs |
| --- | --- | --- |
| `V03` — complete geography | Build and inject a versioned territory catalog from approved normalized references, replacing validation-only offline tooling where necessary; choose concrete importer and storage interfaces at task selection. | `BE-T001`–`BE-T012`, `BE-T058` |
| `V04` — evidence-driven replanning | Connect source and analyzer adapters to a bounded execution loop; run geometry-derived eligibility checks and request targeted follow-up analysis. | `BE-T013`–`BE-T039`, `BE-T054`–`BE-T059` |
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
3. For V02, capture the test database/migration identity, executed `BE-T040`–`BE-T044` results, transaction/geometry oracles and open driver/environment approvals. Mock-backed tests do not substitute for real PostGIS evidence.
4. Update feature traceability and draft-plan links only after implementation review. Keep V02 acceptance pending until the required independent evidence and developer decision exist.
5. If a real-DB check fails, capture its migration identity, failing assertion and DB state; fix the bounded defect and rerun the affected integration case before claiming any acceptance evidence.
