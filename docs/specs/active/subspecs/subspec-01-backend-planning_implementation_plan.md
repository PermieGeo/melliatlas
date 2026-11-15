# MVP-01 Backend — Implementation Plan

- **Status:** Active; implementation partially complete
- **Requirements approval:** APPROVED — active backend sub-spec
- **Implementation authorization:** AUTHORIZED — backend workstream; external approvals are task-specific
- **Acceptance:** PENDING — no full backend acceptance criterion has been signed off
- **Stage/workstream:** `MVP-01` / `mvp-01-backend`
- **Normative sub-spec:** [MVP-01 Backend requirements](subspec-01-backend-planning.md)
- **Parent:** [MelliAtlas umbrella](../../umbrella_spec_melliatlas.md)

The [active backend sub-spec](subspec-01-backend-planning.md) owns normative behavior and acceptance; this plan records **current implementation choices, public-boundary design, task sequencing, and test oracles**. The [specification guidance](../../AGENTS.md) governs contract-first design and approval. Section 4.1 designs the V04-03 integration boundary; implemented code and contract tests, not this plan, remain authoritative.

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
- **Current increment:** `V04-03` — opt-in fictional ecology investigations through the existing jobs, HTTP and completed-snapshot contracts. V04-01 pure geometry and V04-02 bounded agent are implemented predecessors.
- **Goal:** Run a distinct synthetic ecology scenario with a reviewable exclusion-driven alternative, expose typed observations and decisions to clients, and preserve completed results through the existing snapshot serialization boundary.
- **Requirement IDs:** `MVP01-BE-R06`, `MVP01-BE-R08`, `MVP01-BE-R09`, `MVP01-BE-R10`, `MVP01-BE-R12`, `MVP01-BE-R13`, `MVP01-BE-R14`, `MVP01-BE-R15`, `MVP01-BE-R16`
- **Test inventory IDs:** `BE-T017`, `BE-T020`, `BE-T023`, `BE-T035`, `BE-T037`, `BE-T039`, `BE-T045`, `BE-T051`, `BE-T052`, `BE-T053`, `BE-T054`
- **Scope:** A new explicit fictional scenario ID, a composition-injected ecology planner for `jobs`, additive typed replanning output on the investigation read contract, codec roundtrip and old-payload compatibility. The existing V01 scenario is untouched.
- **Not in scope:** Real restrictions or verified coverage; source registry, general DAG, new HTTP route, durable queued/running jobs, new PostGIS acceptance, Web implementation or acceptance of the full V04 stage.
- **Existing interfaces:** `backend/src/melliatlas/sources/api.py`, `backend/src/melliatlas/planning/api.py`, `backend/src/melliatlas/agent/api.py`, `backend/src/melliatlas/analyzers/api.py`, `backend/src/melliatlas/jobs/api.py`, `backend/src/melliatlas/api/app.py`, `backend/src/melliatlas/api/routes_investigations.py`.
- **Implemented files:** Existing public interfaces above, `backend/tests/contract/test_ecology_investigations_http.py`, `backend/tests/unit/test_completed_snapshot_codec.py`; linked owning module contracts and feature cross-reference are updated.
- **Approval gates:** All ecological polygons and conclusions in this increment are fictional; the resulting plan cannot imply real legality or ecological suitability. External data, new runtime libraries and real database access remain unapproved.
- **Exit evidence:** One scenario begins with a later-excluded stop, selects a different alternative based on geometry and provenance rather than ID, returns at least two bounded checks and ordered stops, and exposes warnings/typed decisions. No-plan, invalid inputs, inspector failure, existing V01, old stored JSON, and fake-store reopen require separate regressions. Real DB and complete RU/BY evidence remain pending.

### 4.1 Public contracts and integration design

V04-01 and V04-02 declarations in [`planning/api.py`](../../../../backend/src/melliatlas/planning/api.py), [`analyzers/api.py`](../../../../backend/src/melliatlas/analyzers/api.py), and [`agent/api.py`](../../../../backend/src/melliatlas/agent/api.py) are authoritative. This section records the reviewed and implemented **V04-03 boundaries**, with code and contract tests now authoritative; the [normative requirements](subspec-01-backend-planning.md#4-requirement-to-umbrella-mapping) remain in the sub-spec.

#### Public types and signatures

| Owner | Implemented typed boundary | Authoritative declaration |
| --- | --- | --- |
| `planning` / `sources` | Additive `SyntheticScenario.ecology_zones` and `SYNTHETIC_ECOLOGY_SCENARIO_ID` | [`planning/api.py`](../../../../backend/src/melliatlas/planning/api.py), [`sources/api.py`](../../../../backend/src/melliatlas/sources/api.py), [`sources/contract.md`](../../../../backend/src/melliatlas/sources/contract.md) |
| `jobs` / `agent` | Optional `EcologyPlannerFactory`, bounded decisions, and `InvestigationSnapshot.replanning` | [`jobs/api.py`](../../../../backend/src/melliatlas/jobs/api.py), [`agent/api.py`](../../../../backend/src/melliatlas/agent/api.py), [`jobs/contract.md`](../../../../backend/src/melliatlas/jobs/contract.md) |
| `api` | `ReplanSummaryDto`, `SiteAssessmentDto`, `ReplanDecisionDto` and default injected inspector | [`api/routes_investigations.py`](../../../../backend/src/melliatlas/api/routes_investigations.py), [`api/app.py`](../../../../backend/src/melliatlas/api/app.py), [`api/contract.md`](../../../../backend/src/melliatlas/api/contract.md) |

#### Module interactions

1. `sources` returns the requested fictional scenario and its explicit ecology zones; only the distinct V04 scenario requests inspection. No implicit source I/O is introduced.
2. `api.create_app` supplies a factory using `analyzers.find_ecology_overlaps` and `planning.assess_ecology`, which the `agent.DeterministicPlanner` consumes through `SiteInspector`. `jobs` imports `agent.api` and `planning.api` only.
3. `jobs.process` delegates the V04 scenario through the injected planner, stores `ReplanResult` next to the existing plan and outcome, and keeps `COMPLETED/NO_FEASIBLE_ALTERNATIVE` or `COMPLETED/INSUFFICIENT_EVIDENCE` distinct from technical `FAILED`.
4. HTTP presents the typed decisions, observations, evidence/rule IDs, warnings and check counts without exposing the private request starting point. The completed-snapshot codec restores the same typed domain values after a new service instance reopens a stored result.

#### Failure contracts

- Unsupported scenario/country/date inputs reject before job creation. A V04 scenario without its injected evaluator must fail closed, not silently reuse the V01 planner.
- Inspector errors and malformed ecology outputs produce sanitized `FAILED` status and never a successful plan; bounded check exhaustion yields a completed insufficient-evidence outcome with no plan.
- Historical completed JSON without `replanning` decodes as `None`; malformed nested replanning records are rejected as storage errors. Replanning and top-level plans must agree on reconstruction.

#### Compatibility

- The V01 scenario's computation, statuses, trace and persistence remain unchanged; only an optional `replanning` field is added to the HTTP schema, with `null` for V01.
- Existing injectable `create_app` arguments and `InMemoryInvestigationService(provider, completed_store)` positional arguments remain valid. No migration or new runtime dependency is introduced; real PostGIS verification remains independent.
- Preserve the `agent -> planning`, `jobs -> agent/planning`, and `api -> analyzers/agent/sources/jobs` permitted dependency directions.

#### Contract-first tests

- The implemented HTTP contract tests demonstrate explicit V04 scenario selection, geometry-caused revision, structured trace/assessment evidence, warnings, no private coordinates, immutable GET, and V01 backward compatibility (`BE-T017`, `BE-T035`, `BE-T051`–`BE-T053`).
- The extended snapshot codec tests cover V04 roundtrip, old JSON without the new optional key, malformed typed nested values and stored plan divergence. Add negative tests for missing inspector and a bounded/no-plan outcome (`BE-T037`, `BE-T039`, `BE-T045`).
- V04-01/V04-02 unit tests and architecture tests (`BE-T054`) guard the existing layers; real PostGIS and geographic acceptance remain separate.

### 4.2 Implementation sequence (TDD)

1. Review the new `SyntheticScenario` and `InvestigationSnapshot` additive fields, the factory injection and typed HTTP response against the existing public code and contracts.
2. Write failing contract/codec tests for the V04 scenario, observable evidence-based revision, no-plan paths, legacy JSON compatibility and failure isolation.
3. Implement only the reviewed source fixture, API composition, jobs orchestration, HTTP DTO and storage decoder; retain all existing V01 behavior.
4. Run relevant unit, contract, architecture and SDD checks, then local `FMT,CHK`; do not promote acceptance without approved real evidence or PostGIS tests.

## 5. Upcoming vertical slices

The V04-03 investigation integration task is in section 4; the V03 runtime loader is already implemented but real geographic coverage remains incomplete. V02 real PostGIS verification remains an **independent pending acceptance gate**; completion of startup wiring does not discharge `BE-T040`–`BE-T044`. These later slices identify **implementation work**, not new requirements or approved designs. Their normative scope and external gates remain in [sub-spec sections 4–7](subspec-01-backend-planning.md#4-requirement-to-umbrella-mapping). Select and review public interfaces only when each slice becomes current.

| Slice | Implementation decision to make when selected | Planned test IDs |
| --- | --- | --- |
| `V03` — approved real geography (remaining) | Finish independent RU/BY inventories, verify full real coverage, and decide whether persistent multi-version reference storage is needed. The opt-in local runtime loader is implemented but not accepted as complete geography. | `BE-T001`–`BE-T012`, `BE-T058` |
| `V04` — evidence-driven replanning (remaining) | Extend the reviewable fictional investigation scenario with a typed source/agent execution graph and negative evidence-boundary cases after V04-03 integration. | `BE-T013`–`BE-T039`, `BE-T054`–`BE-T059` |
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
