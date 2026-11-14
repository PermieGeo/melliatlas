# MVP-01 Backend — Implementation Plan

- **Status:** Active; implementation partially complete
- **Requirements approval:** Active backend sub-spec approved
- **Implementation authorization:** Backend workstream authorized; external approvals are task-specific
- **Acceptance:** Pending; no full backend acceptance criterion has been signed off
- **Stage/workstream:** `MVP-01` / `mvp-01-backend`
- **Normative sub-spec:** [MVP-01 Backend requirements](subspec-01-backend-planning.md)
- **Parent:** [MelliAtlas umbrella](../../umbrella_spec_melliatlas.md)

The normative sub-spec defines obligations; this advisory plan organizes small deliverable tasks. Existing code and its public module contracts supersede any historical design sketch. Do not generate the entire module graph from this plan. Backend APIs needed by the dependent React client must be verified before the corresponding Web implementation; the first browser slice must not wait for every backend capability to be complete.

## 1. Current implementation evidence

| Capability | Verified implementation boundary | Remaining acceptance work |
| --- | --- | --- |
| HTTP bootstrap | [`api/app.py`](../../../../backend/src/melliatlas/api/app.py) and [`api/contract.md`](../../../../backend/src/melliatlas/api/contract.md); health, OpenAPI, injected settings and territory catalog | Investigation/source routes, complete OpenAPI and error contracts (`MVP01-BE-A01`, `A12`) |
| Territory model and catalog | [`territories/api.py`](../../../../backend/src/melliatlas/territories/api.py), [`territories/contract.md`](../../../../backend/src/melliatlas/territories/contract.md); offline validation, in-memory catalog and versioned reads | Approved complete RU/BY references, verified topology/precision, PostGIS adapter (`A02`, `A03`) |
| Architecture guard | [`backend/tests/architecture/test_module_boundaries.py`](../../../../backend/tests/architecture/test_module_boundaries.py) | Runtime no-network, DI and integration enforcement (`A11`) |
| Planning, Sources, Analyzers, Engine, Agent, Jobs, Persistence, Web | Not implemented as product capabilities | All associated acceptance evidence pending |

Implemented APIs are defined by their linked Python source and `contract.md`, **not** by future design notes. `create_app(*, settings=..., territories=...)` remains backwards compatible. Territory URLs include `/api/v1/territories/districts?region_id=...` and `/api/v1/territories/geometry/{territory_id}`. No real complete geography has been imported. No acceptance test may infer complete regional coverage from the synthetic fixtures.

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

## 3. Domain and interface invariants for future tasks

These are **constraints**, not prescribed dataclass files or approved implementation signatures. Define concrete typed public interfaces and executable contract tests only when the task first needs them.

| Boundary | Required semantics |
| --- | --- |
| `territories` | Preserve the implemented `TerritoryCatalog` and `TerritoryImport(snapshot, inventory)` protocols; retain source/date/reference identity and explicit missing/unsupported geometry. Precision/unknown accuracy and real PostGIS topology still need reviewed decisions. |
| `planning` | WGS84 points, inclusive valid season windows, stable candidate IDs, forage opportunities and ordered stops. An `EXCLUDED` demo site cannot appear in a recommended plan; `CAUTION` is not a prohibition; missing evidence is not proof of safety. No honey-yield prediction. |
| `sources` | Country-aware descriptors: cartography in RU/BY, fixture public-web in RU/BY, fixture Saturn only in RU. Evidence must retain source ID, kind, verified kind/payload pairing, synthetic/mode, collection time, **effective interval**, geographic/reference scope and meaningful **uncertainty**. Missing interval/coverage is unknown, not a permissive default. No fixture network requests. |
| `analyzers` | Pure calculations receive typed inputs; dispatch checks analyzer kind/input/output compatibility. Spatial exclusion uses geometry and explicit fictional rule evidence, never candidate-name matching. |
| `engine` | A small bounded execution sequence or typed DAG, as required by actual operations. Distinguish `SourceStep(source_id)` from `AnalyzerStep(analyzer_kind)`, validate dependency ordering, artifact bindings, duplicates, cycles and limits. Do not build a universal workflow engine. |
| `agent` | Deterministic observe/replan/stop decisions, limited steps and time, trace with triggering evidence IDs and revised candidates. Do not label unsupported plans as successful. |
| `jobs` | Technical `QUEUED/RUNNING/COMPLETED/FAILED` is distinct from domain `PLAN_FOUND/INSUFFICIENT_EVIDENCE/NO_FEASIBLE_ALTERNATIVE`. A completed analysis may lack a plan; an execution failure is not successful completion. Request includes an optional private starting point. Snapshot retains reference version, evidence summaries, diagnostics and decision trace. |
| `persistence` | PostGIS adapters implement domain-owned ports rather than inheritance-only wrappers; transactional complete-result save, stable UUID, immutable history, spatial SRID/topology checks and fresh-connection reopen. No claim of durable in-flight job recovery. |
| `api` | Preserve the current `create_app` keyword parameters; inject new dependencies additively. Typed HTTP inputs/outputs, validated WGS84 and dates, stable sanitized `{error: {code, message, details?}}` responses, synthetic disclaimer, result/trace and evidence summary. Public route changes require contract review. |

The approved HTTP operations and details remain in the [active backend sub-spec](subspec-01-backend-planning.md). Once a module exists, its public API and `contract.md` are the source of truth. Avoid predeclaring speculative protocols; record only the decision a bounded implementation task cannot safely make itself.

## 4. Next bounded delivery task

- **Task ID:** `MVP01-BE-V01`
- **Status:** Proposed; no implementation or acceptance claimed
- **Goal:** First runnable *backend* investigation path using explicitly synthetic evidence: accepted API request → bounded analysis → typed domain outcome → read by stable investigation ID.
- **Requirement IDs:** `MVP01-BE-R06`, `MVP01-BE-R10`, `MVP01-BE-R12`, `MVP01-BE-R13`, `MVP01-BE-R14`, `MVP01-BE-R15`
- **Test inventory IDs:** `BE-T019`, `BE-T020`, `BE-T026`, `BE-T027`, `BE-T045`, `BE-T047`, `BE-T052`, `BE-T053`
- **Scope:** One controlled fixture scenario, explicit synthetic/source limitations, basic valid/invalid request paths, stable result ID and readable interim result. Use only the domain and orchestration interfaces genuinely necessary to deliver this path. Implement a minimal deterministic execution path first; elaborate it into typed DAG/Agent only when evidence-driven replanning is added.
- **Not in scope:** Live providers, approved RU/BY geometry, durable PostGIS completion/reopen, full ecological replanning, browser UI or claiming `MVP01-BE-A08/A09` acceptance.
- **Existing interfaces:** `backend/src/melliatlas/api/app.py`, `backend/src/melliatlas/api/contract.md`, `backend/src/melliatlas/territories/api.py`, `backend/src/melliatlas/territories/contract.md`.
- **Proposed additions:** `backend/src/melliatlas/planning/api.py`, `backend/src/melliatlas/sources/api.py`, `backend/src/melliatlas/jobs/api.py`, `backend/src/melliatlas/api/routes_investigations.py`, focused implementation files and corresponding contract/unit/HTTP tests **only as needed**. Add only meaningful cross-module `contract.md` files. No changes to existing public HTTP routes.
- **Approval gates:** Approve the fixture scenario and whether an explicitly *non-durable development-only* result store may be used before the PostGIS task. A provisional store is not MVP-01 persistence acceptance. New production dependencies require separate approval.
- **Test-first sequence (TDD):** Verify existing boundary contracts → add failing positive/negative API tests and independent synthetic scenario oracles → implement minimal typed model and deterministic path → run relevant pytest, architecture, Ruff, Pyright and full `run-tests.sh` → review API diff, dependency direction, traceability and data limitations.
- **Exit evidence:** Runnable POST/GET contract tests for successful and evidence-limited outcomes, rejected invalid inputs with no side effects, deterministic repeatability, no network, explicit synthetic labels and no false persistence/coverage claims. Mark the task implemented only after actual tests run; do **not** advance stage acceptance.

This task is a **proposed next slice**, not permission to silently choose an unapproved external dataset or weaken the normative MVP-01 acceptance requirements. The next implementation patch must select its concrete test cases from the inventory and report which assertions actually passed.

## 5. Follow-on vertical slices and external gates

| Slice | Product result | Verification and open decisions |
| --- | --- | --- |
| `V02` — persistence and reopen | Persist complete investigations and selected geography in PostGIS; reopen from a new connection | Real database, migration/rollback tests (`BE-T040`–`BE-T044`); approve DB driver/test environment |
| `V03` — complete geography | Approved dated RU/BY regions, two pilot district catalogs and valid provenance/topology | Independent inventories, licensing, geometry accuracy and PostGIS validation (`BE-T001`–`BE-T012`, `BE-T058`); existing fail-closed routes remain |
| `V04` — evidence-driven replanning | Explicit restriction/precaution, source modes, typed dependencies, bounded agent and alternate sites | No outbound calls, kind/payload validation, actual geometry intersection, bounded replan and trace (`BE-T013`–`BE-T039`, `BE-T054`–`BE-T059`) |
| `V05` — backend/Web contract handoff | Full typed source/investigation API, frozen fixtures and documented client states | OpenAPI and route checks (`BE-T048`–`BE-T053`, `BE-T060`), separate React sub-spec then first browser E2E |

These are *work-order groupings*, not additional normative MVP stages. Reorder small tasks if dependencies require, but do not remove existing acceptance requirements. A small backend-to-Web contract can be verified early, so the separate Web sub-spec may start after its actual API dependency is accepted rather than after every backend module is finished. Preserve the existing developer-controlled workstream and do not mark umbrella `MVP-01` complete until backend, real geography, PostGIS and browser acceptance evidence exist.

### Persistent storage considerations

Proposed PostGIS entities include versioned reference/territory/inventory, investigations, plans, evidence, decisions and site geometries. Required constraints: immutable reference identity, independent expected inventory, foreign keys, transactional completed-result persistence, SRID 4326, appropriate spatial indexing, and reviewable migrations. Choose concrete table definitions when building the persistence slice; do not invent a generalized storage abstraction now. In-flight task durability is not part of MVP-01.

### Geographic reference approval

A complete reference requires an independently sourced dated RU/BY inventory, separate Smolensk/Vitebsk district inventories, documented licensing/attribution, full normalized payload hash, canonical ID mappings and reviewed topology/precision. Do not infer completeness from imported rows or OSM-only data. Large licensed reference downloads remain outside PATCH archives. `backend/scripts/import_reference.py` currently **validates local normalized files only**; it does not populate PostGIS or approve the source.

### Tooling and dependencies

The project check command is `bash ./run-tests.sh`; `sh ./run-format.sh` is the mutating formatter. Existing backend tests, Ruff and Pyright checks are configured in `backend/pyproject.toml`. PostGIS, Shapely/pyproj, GeoPandas/pyogrio, and Import Linter/Grimp are candidates only where a task demonstrates value and approval conditions are met. Never describe proposed commands, dependencies or reference sources as already installed.

## 6. Acceptance test inventory

The 60 `BE-Txxx` entries below are the **full planned inventory**, not 60 tests to implement in a single task. `U` = unit; `C` = public contract; `I` = real integration; `A` = architecture; `N` = negative; `B` = boundary. Each task selects a relevant subset and records independent oracles and actual execution evidence.


This matrix is a **target acceptance inventory**, not a claim that its named tests have run. `U` = unit; `C` = public contract; `I` = real PostGIS/HTTP integration; `A` = architecture; `N` = negative; `B` = boundary. Expected results are independent of the implementation's private algorithms.

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

Perform a bounded diff review against the task's requirement and test IDs, public contracts and architecture policy. Record:

1. **Scope:** Every added file and dependency has a task purpose; no unrelated requirements or API changes appeared.
2. **Behavior:** Positive, negative, boundary and failure results are supported by executed tests. Explicitly identify acceptance tests still unrun.
3. **Contracts:** Existing Python imports, HTTP routes and error envelopes remain compatible; any approved change is reflected in contracts and tests.
4. **Architecture:** Review import-policy checks, actual dependencies, duplication of domain rules, I/O ownership and speculative interfaces.
5. **Traceability:** Match current task → requirements → test inventory → implemented paths → `feature-cross-ref.yaml`; do not promote `planned`/`partial` to `verified` on test existence alone.
6. **Evidence and provenance:** Differentiate real geography from synthetic evidence, missing information from safety, and implementation authorization from acceptance.
7. **Delivery:** Report exact checks/results, unavailable tools, unresolved approvals and recovery steps. A ZIP or a commit is not implementation acceptance.

The repository tests check machine-verifiable consistency and detect several deliberately introduced contradictions; they cannot replace critical architectural review or validate the real-world completeness of RU/BY geography.

## 8. Risks and recovery

| Risk | Mitigation |
| --- | --- |
| Unapproved or incomplete source geography | Keep real-reference acceptance blocked; record license/date/accuracy/inventory decisions, never fabricate shapes or counts |
| Fictional ecology mistaken for legal restriction | Preserve fixture provenance and applicability in every result; restriction is demo-only |
| Untyped evidence or unbounded execution | Validate kind/payload pairing, artifact compatibility, limits and errors at owned boundaries |
| Failed database transaction interpreted as success | Atomic persistence and real PostGIS integration tests before `A09` |
| Architectural drift despite passing tests | Negative import-policy tests plus change-focused convergence review |
| API changes disrupting downstream Web work | Preserve accepted routes and add contract/regression tests before altering public schemas |

**Implementation status:** FastAPI bootstrap and partial territory contracts/API are implemented; complete RU/BY datasets, PostGIS, fixture investigation execution, Agent and Web are not. No full backend or product acceptance has been claimed.
