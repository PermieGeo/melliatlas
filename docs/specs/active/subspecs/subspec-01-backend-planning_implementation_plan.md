# MVP-01 Backend — Implementation Plan

**Status:** Advisory draft; no implementation authorized  
**Stage/workstream:** `MVP-01` / `mvp-01-backend`  
**Normative sub-spec:** [MVP-01 Backend requirements](subspec-01-backend-planning.md)  
**Parent:** [MelliAtlas umbrella](../../umbrella_spec_melliatlas.md)  
**Execution order:** backend contract and tests first; dependent React sub-spec/plan next, after backend verification

This document defines **proposed** source files and executable API designs. There is currently no `backend/pyproject.toml`, Python runtime package, API implementation, PostGIS migration or product test suite in the verified scaffold. Nothing in the code examples below is an existing implementation. The developer must approve this plan, its dependencies, geography reference, and any outstanding decisions before coding.

## 1. Architecture decision and scope control

### 1.1. Minimal vertical slice

```text
POST /api/v1/investigations
          |
          v
    jobs.InvestigationService --(port)--> persistence.PostgresInvestigationStore
          |
          v
    agent.DeterministicPlanner
          |
          v
    engine.DagExecutor ----> sources.SourceRegistry ----> fixture-only Source
          |                         |
          +----------------------> analyzers.AnalyzerRegistry
                                        |
                               planning: forage / ecology / stops

GET /api/v1/territories/... --> territories.TerritoryCatalog <-- persistence.PostgresTerritoryCatalog
GET /api/v1/sources?...     --> sources.SourceRegistry
GET /api/v1/investigations/{id} --> jobs.InvestigationService
```

Backend exposes a **fixed, tested application workflow** for `MVP-01`; neither the browser nor an LLM may submit arbitrary execution graphs. PostgreSQL/PostGIS is a real MVP-01 dependency, but an in-process runner is permitted. Avoid a general plugin system, a broker/worker, full OAuth, a dynamic workflow DSL, and extra architectural layers.

### 1.2. Module boundaries and dependency direction

| Module (proposed public owner) | Responsibility | Allowed outgoing dependencies | Forbidden dependency |
| --- | --- | --- | --- |
| `territories` | Canonical RU/BY administrative hierarchy and geometry contracts | Python stdlib; geometry library only inside owned validation adapter | `api`, `agent`, `jobs`, database implementation |
| `planning` *(new capability)* | Synthetic candidate sites, windows, assessments, proposed stops | `territories` public API | FastAPI, PostGIS, engine internals |
| `sources` | Country-aware source descriptor, fixture evidence and acquisition contract | `territories`, `planning` public API | concrete persistence, FastAPI |
| `analyzers` | Pure forage screening, ecological evaluation and plan assembly | `territories`, `sources`, `planning` public APIs | database/HTTP clients, `agent` |
| `engine` | Validate and execute a small typed dependency graph | `sources`, `analyzers`, `planning` public APIs | `agent`, persistence, FastAPI |
| `agent` | Bounded observe/replan/finish policy and decision trace | `engine`, `planning`, `sources` public APIs | SQL, FastAPI, source private adapters |
| `jobs` | Investigation lifecycle, orchestration, store port and status contract | `agent`, `engine`, `planning`, `territories` public APIs | concrete database classes, FastAPI |
| `persistence` | Concrete PostGIS repositories, migrations and reference import | `jobs`, `territories` public interfaces | API route internals, agent internals |
| `api` | Pydantic HTTP DTOs, routes, errors and composition root | public APIs of modules above; FastAPI/Pydantic | private module implementation imports from routes |

A module's `api.py` (or `__init__.py` facade when justified) is the importable boundary. Internal `models.py`, `repository.py`, `fixtures.py`, `executor.py`, etc. are not imported by peer modules. The central composition function is the **single justified place** that instantiates concrete adapters. Avoid a catch-all `common` package until truly general-purpose functions exist.

**Architecture constraints to enforce automatically:** no import cycles; domain modules independent of FastAPI/SQL; `analyzers` do not call network; `engine` never imports agent; public-only peer imports; immutable input/output models or independently copied DTOs; provider I/O disabled in fixture mode.

### 1.3. Interface lifetime and compatibility

- API route paths and DTO JSON shapes are the backend-to-frontend contract; preserve them once accepted. Prefer backwards-compatible fields or explicit version upgrades.
- Module public contracts are designed for `MVP-01`; future live adapters in `MVP-02` should implement existing `Source` protocols, not retroactively require the engine to know provider details.
- All domain types should use finite enums, explicit IDs, timezone-aware timestamps where relevant and typed uncertainty/status fields. Never introduce broad `Any` or dynamically typed dictionaries as a shortcut.
- No new dependency or enforcement configuration can be introduced without developer approval. All listed third-party libraries are **candidates**, not authorized installations.

## 2. Proposed public API declarations

The declarations below are intended for the **named files**. Import statements, enums, parameters and return types are part of the proposed contract; implementation bodies are omitted intentionally. The plan's subsequent TDD steps require adding minimal compiling stubs, then initially failing executable tests before any actual logic. Add short English comments only where a type, value, or field has non-obvious semantics, constraints, or units. Do not repeat information already clear from identifiers or types.

### 2.1. `territories/api.py`

```python
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Protocol, TypeAlias, TypedDict, Literal

class CountryCode(StrEnum):
    RU = "RU"
    BY = "BY"

class TerritoryKind(StrEnum):
    COUNTRY = "country"
    REGION = "region"
    DISTRICT = "district"

class GeometryStatus(StrEnum):
    AVAILABLE = "available"
    MISSING = "missing"
    INVALID = "invalid"

Position: TypeAlias = tuple[float, float]  # Longitude, latitude

class PolygonWgs84(TypedDict):
    type: Literal["Polygon"]
    coordinates: list[list[Position]]

class MultiPolygonWgs84(TypedDict):
    type: Literal["MultiPolygon"]
    coordinates: list[list[list[Position]]]

GeometryWgs84: TypeAlias = PolygonWgs84 | MultiPolygonWgs84

@dataclass(frozen=True)
class GeoPoint:
    longitude: float
    latitude: float

@dataclass(frozen=True)
class Territory:
    id: str
    country: CountryCode
    kind: TerritoryKind
    name: str
    parent_id: str | None
    reference_id: str
    valid_on: date
    geometry_status: GeometryStatus

@dataclass(frozen=True)
class ReferenceManifest:
    reference_id: str
    snapshot_date: date
    retrieved_at: datetime
    source_uri: str
    license_id: str
    checksum_sha256: str
    coordinate_system: str
    # Documented geographic coverage, not verified completeness.
    declared_scope: str
    normalization_version: str

@dataclass(frozen=True)
class TerritoryGeometry:
    territory_id: str
    geometry: GeometryWgs84
    reference_id: str
    coordinate_system: Literal["EPSG:4326"]

class CatalogDepthUnsupported(ValueError):
    pass

class TerritoryCatalog(Protocol):
    async def list_regions(self, country: CountryCode) -> tuple[Territory, ...]: ...
    async def list_districts(self, region_id: str) -> tuple[Territory, ...]: ...
    async def get(self, territory_id: str) -> Territory | None: ...
    async def get_geometry(self, territory_id: str) -> TerritoryGeometry | None: ...

class TerritoryImport(Protocol):
    async def validate_reference(self, manifest: ReferenceManifest) -> None: ...
    async def apply_reference(self, manifest: ReferenceManifest) -> None: ...
```

**Proposed `territories/contract.md` v1:** owns canonical territory identity, RU/BY hierarchy, source manifest integrity, geometry boundary semantics, and complete/incomplete coverage diagnostics. No internal adapter/provider ID becomes public territory identity. `list_districts()` on an unsupported region raises a typed `CatalogDepthUnsupported` error instead of returning an unjustified empty *complete* list. Invalid coordinates, self-intersecting rings, unclosed polygons, unknown parents, duplicate provider mappings and missing reference entries fail validation. Imported data is immutable by reference version; repeated same-version import is idempotent.

### 2.2. `planning/api.py`

```python
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from melliatlas.territories.api import GeoPoint

class ForageLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class SiteDisposition(StrEnum):
    # No known exclusion; this is not a safety guarantee.
    ELIGIBLE = "eligible"
    # A fictional exclusion rule applies in the demo scenario.
    EXCLUDED = "excluded"
    # Requires review; not an automatic prohibition.
    CAUTION = "caution"

@dataclass(frozen=True)
class TimeWindow:
    start: date
    end: date

@dataclass(frozen=True)
class CandidateSite:
    id: str
    territory_id: str
    location: GeoPoint
    label: str

@dataclass(frozen=True)
class ForageOpportunity:
    site_id: str
    window: TimeWindow
    level: ForageLevel
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class SiteAssessment:
    site_id: str
    disposition: SiteDisposition
    # Applied demo rule, if any; not an inferred legal ban.
    rule_id: str | None
    evidence_ids: tuple[str, ...]
    explanation: str
    unknowns: tuple[str, ...]

@dataclass(frozen=True)
class SeasonStop:
    site_id: str
    window: TimeWindow
    evidence_ids: tuple[str, ...]
    rationale: str

@dataclass(frozen=True)
class SeasonPlan:
    stops: tuple[SeasonStop, ...]
    rejected_sites: tuple[SiteAssessment, ...]
    alternatives: tuple[str, ...]
    warnings: tuple[str, ...]
    synthetic: bool
```

**Proposed `planning/contract.md` v1:** defines candidate-site, season, forage and ecological-screening semantics without databases or map clients. Excluded candidates cannot appear as valid stops. Precautionary evidence remains `CAUTION`, not `EXCLUDED`. Windows must fall inside the requested season; stop ordering and deterministic tie breaks are independent of input insertion order. `SeasonPlan` intentionally has **no honey-yield estimate**.

### 2.3. `sources/api.py`

```python
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Protocol, TypeAlias
from melliatlas.territories.api import CountryCode, GeometryWgs84
from melliatlas.planning.api import CandidateSite, ForageLevel, SiteDisposition, TimeWindow

# Classifies source data, not DAG execution steps.
class SourceKind(StrEnum):
    CARTOGRAPHY = "cartography"
    PUBLIC_WEB = "public_web"
    # Russia-only Saturn evidence source.
    SATURN = "saturn"

class SourceMode(StrEnum):
    # Verified versioned reference data.
    REFERENCE = "reference"
    FIXTURE = "fixture"
    UNAVAILABLE = "unavailable"

class EvidenceKind(StrEnum):
    ADMIN_BOUNDARY = "admin_boundary"
    FORAGE_WINDOW = "forage_window"
    CANDIDATE_SITE = "candidate_site"
    # Fictional binding exclusion.
    DEMO_RESTRICTION = "demo_restriction"
    # Fictional non-binding concern.
    DEMO_PRECAUTION = "demo_precaution"
    PUBLICATION_SAMPLE = "publication_sample"
    SATURN_SAMPLE = "saturn_sample"

@dataclass(frozen=True)
class SourceDescriptor:
    # Registry key for this source instance, not its category.
    id: str
    kind: SourceKind
    countries: frozenset[CountryCode]
    mode: SourceMode
    evidence_kinds: frozenset[EvidenceKind]

@dataclass(frozen=True)
class CandidatePayload:
    site: CandidateSite

@dataclass(frozen=True)
class FloweringPayload:
    site_id: str
    window: TimeWindow
    level: ForageLevel

# Contains fictional screening geometry, not a legal boundary.
@dataclass(frozen=True)
class EcologyPayload:
    rule_id: str
    geometry: GeometryWgs84
    disposition: SiteDisposition

@dataclass(frozen=True)
class PublicationSamplePayload:
    title: str
    published_on: date
    url: str

@dataclass(frozen=True)
class SaturnSamplePayload:
    record_id: str
    note: str

EvidencePayload: TypeAlias = (
    CandidatePayload | FloweringPayload | EcologyPayload
    | PublicationSamplePayload | SaturnSamplePayload
)

@dataclass(frozen=True)
class EvidenceRecord:
    id: str
    source_id: str
    kind: EvidenceKind
    synthetic: bool
    mode: SourceMode
    collected_at: datetime
    reference_id: str
    # Territory scope when known; not proof of local applicability.
    territory_id: str | None
    description: str
    payload: EvidencePayload

@dataclass(frozen=True)
class SourceQuery:
    country: CountryCode
    territory_id: str
    # Deterministic fixture scenario, not a live provider query.
    scenario_id: str

@dataclass(frozen=True)
class SourceResult:
    descriptor: SourceDescriptor
    evidence: tuple[EvidenceRecord, ...]
    warnings: tuple[str, ...]

class Source(Protocol):
    @property
    def descriptor(self) -> SourceDescriptor: ...
    async def fetch(self, query: SourceQuery) -> SourceResult: ...

class SourceRegistry(Protocol):
    def list_for_country(self, country: CountryCode) -> tuple[SourceDescriptor, ...]: ...
    def get(self, source_id: str) -> Source: ...
```

**Proposed `sources/contract.md` v1:** owns source capability, applicable countries, fixture/reference/unavailable mode and evidence provenance. Cross-country requests fail with a typed `SourceCountryUnsupported`; `SATURN` is RU-only, public-web RU/BY. No outbound website or Saturn client may be initialized in MVP-01. Source results are evidence records, **not** verified treatment events or legal rulings. Each evidence kind has a matching **typed payload**; analyzers must validate this pairing, never cast arbitrary metadata into a forage window or ecological rule. Ecology fixtures carry explicit geometry and disposition; the site-screening algorithm evaluates actual spatial intersection rather than site ID. Future live source payload contracts may be added compatibly after source access verification.

### 2.4. `analyzers/api.py`

```python
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, TypeAlias
from melliatlas.planning.api import (
    CandidateSite, ForageOpportunity, SeasonPlan, SiteAssessment, TimeWindow
)
from melliatlas.sources.api import EvidenceRecord

class AnalyzerKind(StrEnum):
    FORAGE = "forage"
    ECOLOGY = "ecology"
    SEASON_PLAN = "season_plan"

@dataclass(frozen=True)
class ForageRequest:
    sites: tuple[CandidateSite, ...]
    evidence: tuple[EvidenceRecord, ...]
    season: TimeWindow

@dataclass(frozen=True)
class EcologyRequest:
    sites: tuple[CandidateSite, ...]
    evidence: tuple[EvidenceRecord, ...]
    season: TimeWindow

@dataclass(frozen=True)
class PlanRequest:
    sites: tuple[CandidateSite, ...]
    forage: tuple[ForageOpportunity, ...]
    assessments: tuple[SiteAssessment, ...]
    season: TimeWindow

AnalyzerInput: TypeAlias = ForageRequest | EcologyRequest | PlanRequest
AnalyzerOutput: TypeAlias = (
    tuple[ForageOpportunity, ...] | tuple[SiteAssessment, ...] | SeasonPlan
)

class Analyzer(Protocol):
    @property
    def kind(self) -> AnalyzerKind: ...
    def analyze(self, request: AnalyzerInput) -> AnalyzerOutput: ...

class AnalyzerRegistry(Protocol):
    def get(self, kind: AnalyzerKind) -> Analyzer: ...
    def kinds(self) -> frozenset[AnalyzerKind]: ...
```

**Proposed `analyzers/contract.md` v1:** owns pure, deterministic transformation of declared inputs to declared outputs. MVP-01 analyzers use synthetic forage-window matching, explicit spatial overlap with a **fictional** prohibition, and a separate precautionary rule. Registry dispatch must validate input variant vs analyzer kind before execution (the union alone is insufficient). Test algorithms against independent fixture oracles. Do not infer legal restrictions from an unlabeled protected-area polygon.

### 2.5. `engine/api.py`

```python
from dataclasses import dataclass
from typing import Protocol, TypeAlias
from melliatlas.sources.api import SourceResult, SourceQuery
from melliatlas.analyzers.api import AnalyzerKind, AnalyzerOutput
from melliatlas.planning.api import TimeWindow

@dataclass(frozen=True)
class SourceStep:
    id: str
    # Exact SourceRegistry key, not SourceKind.
    source_id: str
    depends_on: tuple[str, ...]

@dataclass(frozen=True)
class AnalyzerStep:
    id: str
    analyzer_kind: AnalyzerKind
    depends_on: tuple[str, ...]

StepSpec: TypeAlias = SourceStep | AnalyzerStep

@dataclass(frozen=True)
class ExecutionGraph:
    steps: tuple[StepSpec, ...]

@dataclass(frozen=True)
class ExecutionContext:
    source_query: SourceQuery
    season: TimeWindow

@dataclass(frozen=True)
class ExecutionLimits:
    max_steps: int
    max_duration_seconds: float

ArtifactPayload: TypeAlias = SourceResult | AnalyzerOutput

@dataclass(frozen=True)
class ExecutionArtifact:
    step_id: str
    payload: ArtifactPayload

@dataclass(frozen=True)
class ExecutionResult:
    artifacts: tuple[ExecutionArtifact, ...]
    executed_steps: tuple[str, ...]
    diagnostics: tuple[str, ...]

class DagExecutor(Protocol):
    async def execute(
        self, graph: ExecutionGraph, context: ExecutionContext, limits: ExecutionLimits
    ) -> ExecutionResult: ...
```

**Proposed `engine/contract.md` v1:** owns graph validation, unique step IDs, known dependencies, deterministic topological ordering, registered source IDs/analyzer kinds and maximum step/deadline enforcement. `SourceStep` invokes a `Source` identified by `source_id`; `AnalyzerStep` invokes an `Analyzer` selected by `AnalyzerKind`. These are **execution step variants**, not kinds of source or analyzer components. The `StepSpec` union allows dispatch by concrete variant without interpreting a generic `capability_id`. Validate source/analyzer registration, prerequisite artifact types and analyzer input compatibility before invocation. The implementation may use a small **internal typed binding from dependency artifacts to analyzer input**; it must be declared and tested rather than relying on untyped positional casts. No arbitrary submitted DSL, eval, LLM code or transport-level types. Failures preserve source causes in server diagnostics while sanitizing HTTP responses. Cancellation releases owned resources.

### 2.6. `agent/api.py`

```python
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from melliatlas.engine.api import ExecutionResult, ExecutionGraph
from melliatlas.planning.api import SeasonPlan, TimeWindow

class AgentAction(StrEnum):
    OBSERVE = "observe"
    REPLAN = "replan"
    FINISH = "finish"
    STOP_WITH_LIMITATION = "stop_with_limitation"

@dataclass(frozen=True)
class InvestigationGoal:
    scenario_id: str
    territory_id: str
    season: TimeWindow

@dataclass(frozen=True)
class DecisionEvent:
    action: AgentAction
    reason: str
    triggering_evidence_ids: tuple[str, ...]
    previous_site_ids: tuple[str, ...]
    revised_site_ids: tuple[str, ...]

@dataclass(frozen=True)
class AgentOutcome:
    plan: SeasonPlan | None
    decisions: tuple[DecisionEvent, ...]
    diagnostics: tuple[str, ...]

class DeterministicPlanner(Protocol):
    async def investigate(self, goal: InvestigationGoal) -> AgentOutcome: ...
```

**Proposed `agent/contract.md` v1:** owns bounded decision policy, evidence-triggered explicit ecology check and explainable revision. An initially favorable candidate is rejected **because the analyzer returned applicable evidence**, never because a name or demo ID matched a hardcoded branch. Respect limits for steps, replans and elapsed time. If no qualifying plan exists, return `plan=None` with diagnostics. Agent cannot import SQL or call source internals; it requests registered operations from Engine. The checked `ExecutionResult`/graph become internal collaborators injected through public ports, not browser-supplied instructions.

### 2.7. `jobs/api.py`

```python
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID
from melliatlas.agent.api import AgentOutcome
from melliatlas.planning.api import TimeWindow
from melliatlas.territories.api import CountryCode, GeoPoint

class InvestigationStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass(frozen=True)
class InvestigationRequest:
    country: CountryCode
    territory_id: str
    season: TimeWindow
    scenario_id: str
    starting_point: GeoPoint | None

class InvestigationErrorCode(StrEnum):
    INVALID_REQUEST = "invalid_request"
    NO_VALID_PLAN = "no_valid_plan"
    TIME_LIMIT = "time_limit"
    EXECUTION_FAILED = "execution_failed"

@dataclass(frozen=True)
class InvestigationSnapshot:
    id: UUID
    status: InvestigationStatus
    request: InvestigationRequest
    created_at: datetime
    # Populated only after a terminal lifecycle transition.
    finished_at: datetime | None
    outcome: AgentOutcome | None
    error_code: InvestigationErrorCode | None

class InvestigationStore(Protocol):
    async def save_completed(self, snapshot: InvestigationSnapshot) -> None: ...
    async def get(self, investigation_id: UUID) -> InvestigationSnapshot | None: ...

class InvestigationService(Protocol):
    async def submit(self, request: InvestigationRequest) -> InvestigationSnapshot: ...
    async def get(self, investigation_id: UUID) -> InvestigationSnapshot | None: ...
```

**Proposed `jobs/contract.md` v1:** owns investigation IDs, lifecycle, request validation, bounded in-process scheduling, and the completed-result storage port. **Failure is not completion**. A persistent completed result must survive restart; in-process unfinished work may not. Decide the exact queue/async model before implementation and test response semantics consistently. The service owns a finite concurrent-run limit and does not log sensitive starting points. The `InvestigationErrorCode` enum is the only source of lifecycle error codes; HTTP error mapping is defined at the API boundary.

### 2.8. `persistence/api.py`

```python
from typing import Protocol
from melliatlas.jobs.api import InvestigationStore
from melliatlas.territories.api import TerritoryCatalog, TerritoryImport

# Defines transactional resource ownership for persistence.
class StorageUnitOfWork(Protocol):
    async def __aenter__(self) -> "StorageUnitOfWork": ...
    async def __aexit__(self, exc_type: type[BaseException] | None,
                        exc: BaseException | None, tb: object) -> None: ...

class PostgisInvestigationStore(InvestigationStore, Protocol):
    pass

class PostgisTerritoryStore(TerritoryCatalog, TerritoryImport, Protocol):
    pass
```

**Proposed `persistence/contract.md` v1:** owns PostGIS-backed implementations of `jobs.InvestigationStore` and `territories.TerritoryCatalog/TerritoryImport` plus reviewed migrations. The public contract is the **existing ports**, not inheritance from this illustrative name-only adapter protocol; remove name-only wrappers if they add no value. Store WGS84 geometries with SRID and apply spatial validation/transformations explicitly. Query with parameters, transactionally insert completed plans and traces, handle duplicate IDs and failed transactions, and verify idempotent imports. Do not hide database failures behind successful job states.

### 2.9. `api/public.py` and `api/app.py`

```python
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from fastapi import FastAPI
from pydantic import BaseModel, Field
from melliatlas.jobs.api import InvestigationService
from melliatlas.sources.api import SourceRegistry
from melliatlas.territories.api import TerritoryCatalog, CountryCode

class ApiErrorCode(StrEnum):
    INVALID_REQUEST = "invalid_request"
    UNKNOWN_TERRITORY = "unknown_territory"
    UNSUPPORTED_DEPTH = "unsupported_depth"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CAPABILITY_UNAVAILABLE = "capability_unavailable"
    LIMIT_EXCEEDED = "limit_exceeded"
    EXECUTION_FAILED = "execution_failed"

class ErrorDetail(BaseModel):
    code: ApiErrorCode
    message: str

class ErrorResponse(BaseModel):
    error: ErrorDetail

class CreateInvestigationDto(BaseModel):
    country: CountryCode
    territory_id: str = Field(min_length=1)
    start_date: date
    end_date: date
    # Identifier of the selected synthetic demo scenario.
    scenario_id: str

@dataclass(frozen=True)
class ApiDependencies:
    territories: TerritoryCatalog
    sources: SourceRegistry
    investigations: InvestigationService

def create_app(dependencies: ApiDependencies) -> FastAPI: ...
```

**Proposed `api/contract.md` v1:** owns versioned URL routes, OpenAPI, request/response DTOs, error mapping and composition. Additional typed response DTOs for territories, GeoJSON, source descriptors, status, seasonal plan and decision trace must be fully defined during the API TDD task, with no dynamic arbitrary serialization. Schema changes after Web work begins require deliberate contract review. Routes must not import private domain implementation files or perform spatial operations themselves. `create_app` accepts test-injected implementations; startup/shutdown safely manages adapters.

### 2.10. Contract drafting and real files

The paragraphs headed **Proposed `<module>/contract.md` v1** are the first contract drafts for all nine proposed modules (`territories`, `planning`, `sources`, `analyzers`, `engine`, `agent`, `jobs`, `persistence`, `api`). At implementation time, write the corresponding owned `contract.md` **before** the module's internal implementation, preserving these public contracts or amending this active plan with developer approval. Avoid empty boilerplate or duplicating code line-for-line in the contracts. Explicitly note in each implemented contract the public import path, input/output invariants, errors, invariants and forbidden imports.

## 3. Data schema and import strategy

### 3.1. Proposed PostGIS storage (reviewable migration)

| Table | Key fields | Invariants / index |
| --- | --- | --- |
| `reference_dataset` | `reference_id`, `snapshot_date`, `retrieved_at`, `source_uri`, `license_id`, `checksum_sha256`, `declared_scope` | Unique immutable reference version |
| `territory` | `id`, `country`, `kind`, `name`, `parent_id`, `reference_id`, `valid_on`, `geometry` | FK parent/reference; unique `(reference_id, id)`; SRID 4326; spatial GiST index |
| `reference_inventory` | `reference_id`, `territory_id`, `expected_parent_id` | Independent expected ID set, not derived by querying imported records |
| `investigation` | UUID `id`, request JSONB, `status`, `created_at`, `finished_at`, `reference_id`, `error_code` | Completed status requires completed plan, FK reference |
| `investigation_plan` | `investigation_id`, `version`, plan JSONB, `synthetic` | Read-only completed snapshot, FK investigation |
| `investigation_evidence` | `investigation_id`, evidence ID, source ID, kind, mode, provenance JSONB | No silently missing origin/mode |
| `investigation_decision` | `investigation_id`, ordinal, action, evidence IDs, reason | Immutable ordered trace |
| `investigation_site` | `investigation_id`, site ID, point geometry, decision | Valid WGS84 coordinates; index where needed |

Use database enums or constrained text consistently, not free-form arbitrary status strings. Avoid storing full unbounded provider payloads or private data in logs. Geometry APIs may return validated GeoJSON; persistence may use PostGIS geometry columns. Proposed migrations `0001_reference_catalog` and `0002_investigation_results` must be tested against a fresh database and a migrated one. A separate worker/queue schema is out of scope.

### 3.2. Reference data selection and safeguards

1. Shortlist legally usable **dated** administrative catalogs and boundary sources for RU/BY with declared coverage and provenance; prefer official inventories for completeness checks where appropriate.
2. Evaluate differences among national/official geography, OSM-derived boundaries, district-versus-municipality categories, and contested/ambiguous borders without guessing canonical geography.
3. Record chosen source license, attribution requirement, retrieval date, checksum and normalization rules in an import manifest. Keep provider IDs as mappings, not the canonical primary keys.
4. Load **all RU first-order subjects** from the approved dated inventory and **all BY oblasts plus Minsk city**; load **all administrative districts** for Smolensk and Vitebsk from approved dated inventories. Other regions are region-only.
5. Verify set equality between independently captured inventory keys and imported canonical keys, per parent/country, and fail acceptance on unresolved omissions/duplicates/invalid shapes.
6. Import geometries in EPSG:4326 with validated polygon topology (or record unsupported/invalid geometries explicitly); choose a reviewed reprojection path for upstream CRSs. Do not pretend longitude/latitude differences are distances in meters.
7. Maintain a tiny deterministic test subset in repository fixtures; retain large licensed reference downloads outside incremental PATCH ZIPs. Reproduction must document how to obtain, verify and import the approved complete dataset.

**Blocker:** no RU/BY dataset license or authoritative inventory is verified from the current scaffold. Tests may prove importer behavior on small fixtures, but the `MVP-01` completeness gate cannot be signed off until full authorized sources and manifests are provided and tested.

## 4. Proposed file changes for later implementation

All files below are **proposed**, not verified current files. Existing placeholder directories exist but contain only `.gitkeep` entries. Implementation patches should add source files incrementally and remove placeholder `.gitkeep` only when the owning directory becomes populated, where appropriate.

| Path / pattern | Purpose |
| --- | --- |
| `backend/pyproject.toml` | Python package, declared dependencies, Ruff, pyright and pytest configuration (requires dependency approval) |
| `backend/src/melliatlas/__init__.py`, `main.py` | Package identity and application entry point |
| `backend/src/melliatlas/territories/{api.py,models.py,validation.py,importer.py,contract.md}` | Territory domain contracts, geometry validation, reference import |
| `backend/src/melliatlas/planning/{api.py,forage.py,ecology.py,season.py,contract.md}` | Pure site/season models and deterministic planning rules |
| `backend/src/melliatlas/sources/{api.py,registry.py,fixtures.py,contract.md}` | Typed provider registry and fixture-only samples |
| `backend/src/melliatlas/analyzers/{api.py,forage.py,ecology.py,season.py,contract.md}` | Pure analyzers, typed registry |
| `backend/src/melliatlas/engine/{api.py,dag.py,executor.py,contract.md}` | Topological validation, dependency binding and execution |
| `backend/src/melliatlas/agent/{api.py,deterministic.py,contract.md}` | Bounded decisions and explicit replan events |
| `backend/src/melliatlas/jobs/{api.py,service.py,contract.md}` | Run lifecycle and bounded in-process execution |
| `backend/src/melliatlas/persistence/{api.py,territories.py,investigations.py,contract.md}` | Port implementations, transactional storage |
| `backend/src/melliatlas/api/{public.py,app.py,routes_territories.py,routes_sources.py,routes_investigations.py,contract.md}` | Pydantic DTOs, FastAPI routes, app assembly |
| `backend/migrations/*` | Reviewed PostGIS schema and migration runner/config |
| `backend/tests/conftest.py`, `backend/tests/unit/*`, `backend/tests/contract/*`, `backend/tests/integration/*`, `backend/tests/architecture/*` | Fixtures, pure/contract/PostGIS/import-boundary tests |
| `config/countries/{ru,by}.yaml` | Declarative country and source availability; verified schema required |
| `backend/tests/fixtures/{geography,scenarios,source_responses}/*` | Small controlled fixtures with provenance and explicit synthetic markers |
| `backend/scripts/import_reference.py` | Reproducible reference import, coverage report and checksum verification |
| `docs/INSTALLATION.md`, `docs/TESTS.md`, `docs/USAGE.md` | Actual environment/install/test/demo procedures when executable functionality exists |
| `docs/specs/feature-cross-ref.yaml` | Add **verified** owners/test paths as files are created |
| `run-tests.sh` | Extend the existing fail-fast checks to include real backend dependencies and architecture/integration gates once tooling is approved |

**Removals:** only obsolete `.gitkeep` files inside directories where real files are introduced; no current tracked product files are replaced. **No Web source files** in this backend implementation plan.

## 5. Test-first implementation sequence

For each step: add public declarations and contract draft → write the stated executable tests → observe failures caused by missing behavior → implement the smallest passing behavior → refactor → run architecture checks and the existing `run-tests.sh`. Do not write `pytest.skip`, placeholder `assert False`, or loosen existing lint checks.

1. **Preparation and approved dependencies** — verify current `main`, repository AGENTS, umbrella, this active spec/plan and README. Approve Python version, PostGIS test environment, dependency list and administrative sources. Create minimal package, settings and test runner; write a smoke test that asserts the FastAPI app serves OpenAPI. *Acceptance:* `MVP01-BE-A01`, initial checks can execute.
2. **Territory API and real reference importer** — add typed territory public declarations and `contract.md`; first test wrong parent, unknown IDs, region-only depth, invalid WGS84, repeated imports and incomplete inventory; then implement. After selecting licensed sources, import complete RU/BY catalogs and pilot districts; verify independently. *Acceptance:* `A02`, `A03`.
3. **Planning models** — define immutable site, season, forage and assessment contracts; first test invalid dates, duplicate site IDs, overlapping windows and exclusion precedence; implement deterministic validators. *Acceptance:* `A07`, `A08`.
4. **Sources** — register RU/BY geography, RU/BY public web fixture and RU Saturn fixture; first test source-country compatibility, unsupported modes and zero outbound provider calls; implement descriptors/fixtures. *Acceptance:* `A04`.
5. **Analyzers** — first test independently expected forage overlaps, explicit fictional restriction, precaution-only warning, unknown evidence and stable ordering; implement pure functions and typed dispatch. *Acceptance:* `A07`, `A08`.
6. **Engine DAG** — first test `SourceStep(source_id=...)` fetching from the source registry and `AnalyzerStep(analyzer_kind=...)` consuming typed upstream artifacts; cover dependency ordering, cycles, missing steps/capabilities, incompatible input variants, reused artifacts, timeout and failed nodes. Implement topological execution and explicit artifact binding without a generic operation-kind discriminator. *Acceptance:* `A05`, `A10`.
7. **Deterministic Agent** — first test initially attractive but excluded candidate, evidence-triggered replan, no available alternative, missing ecology result, max-step limit and consistent trace; implement bounded observe/replan policy. *Acceptance:* `A06`, `A07`.
8. **PostGIS migration and storage** — first test transactional completed snapshot, saved geometry with valid SRID, reload via a new connection, rolled-back failed save and stable imported boundaries; implement migrations and adapters. *Acceptance:* `A02`, `A03`, `A09`.
9. **Investigation service** — first test valid submission, status progression, error mapping, duplicate requests, completion only after committed storage, and interruption semantics. Implement minimal bounded in-process runner without pretending to have durable worker recovery. *Acceptance:* `A08`–`A10`.
10. **FastAPI routes** — first test request/response DTOs, OpenAPI, RU/BY region/district navigation, reference-geometry exposure, source catalog and run/reopen behavior. Implement app wiring with injected ports. *Acceptance:* `A01`, `A04`, `A09`, `A10`, `A12`.
11. **Architecture and failure gates** — add import graph tests, transport/DB import restrictions, contract-only peer imports and no-network fixture gates. Check reproducibility with a fresh database and empty caches. *Acceptance:* `A11`, all earlier IDs.
12. **Backend → Web handoff** — freeze the approved API fixture examples and OpenAPI spec, document exact client states (queued/running/completed/failed/insufficient), read-only map geometry and evidence disclaimer. Obtain developer acceptance before activating the separate Web sub-spec. *Acceptance:* `A12`; umbrella `MVP-01` remains open.

### 5.1. Executable TDD skeletons (representative)

These are intended for the future test files **after minimally compiling public stubs and fixtures exist**. They assert behavior and will fail while corresponding stub methods raise `NotImplementedError` or return incomplete results. They are not standalone runnable tests in the current documentation-only scaffold.

`backend/tests/contract/test_source_api.py`:

```python
from melliatlas.sources.api import SourceKind
from melliatlas.territories.api import CountryCode


def test_saturn_is_never_a_belarus_capability(source_registry):
    kinds = {entry.kind for entry in source_registry.list_for_country(CountryCode.BY)}
    assert SourceKind.SATURN not in kinds
    assert SourceKind.PUBLIC_WEB in kinds
    assert SourceKind.CARTOGRAPHY in kinds


def test_russian_source_catalog_has_fixture_saturn(source_registry):
    entries = source_registry.list_for_country(CountryCode.RU)
    saturn = [entry for entry in entries if entry.kind is SourceKind.SATURN]
    assert len(saturn) == 1
    assert saturn[0].mode.value == "fixture"
```

`backend/tests/contract/test_territory_api.py`:

```python
import pytest
from melliatlas.territories.api import CountryCode, TerritoryKind, CatalogDepthUnsupported


@pytest.mark.asyncio
async def test_pilot_districts_have_canonical_parents(catalog, smolensk_id):
    districts = await catalog.list_districts(smolensk_id)
    assert districts
    assert all(item.kind is TerritoryKind.DISTRICT for item in districts)
    assert all(item.parent_id == smolensk_id for item in districts)
    assert all(item.country is CountryCode.RU for item in districts)


@pytest.mark.asyncio
async def test_unsupported_region_district_depth_is_explicit(catalog, other_region_id):
    with pytest.raises(CatalogDepthUnsupported):
        await catalog.list_districts(other_region_id)
```

`backend/tests/unit/test_agent_replan.py`:

```python
import pytest
from melliatlas.agent.api import AgentAction


@pytest.mark.asyncio
async def test_excluded_site_triggers_evidence_driven_replan(
    planner, excluded_candidate_scenario
):
    outcome = await planner.investigate(excluded_candidate_scenario.goal)
    assert outcome.plan is not None
    chosen = {stop.site_id for stop in outcome.plan.stops}
    assert excluded_candidate_scenario.initially_favored_site_id not in chosen
    assert any(event.action is AgentAction.REPLAN for event in outcome.decisions)
    assert any(event.triggering_evidence_ids for event in outcome.decisions
               if event.action is AgentAction.REPLAN)
```

`backend/tests/integration/test_completed_investigations.py`:

```python
import pytest


@pytest.mark.asyncio
async def test_completed_plan_survives_new_postgis_connection(
    investigation_service, reopened_service, valid_demo_request
):
    started = await investigation_service.submit(valid_demo_request)
    await wait_for_terminal_status(investigation_service, started.id)
    reopened = await reopened_service.get(started.id)
    assert reopened is not None
    assert reopened.status.value == "completed"
    assert reopened.outcome is not None
    assert reopened.outcome.plan is not None
    assert len(reopened.outcome.plan.stops) >= 2
```

Each example depends on **future** fixtures/helpers in `backend/tests/conftest.py`, including `wait_for_terminal_status`, which must be declared in the relevant test fixture file during implementation before tests are executed. The spec's actual acceptance tests must additionally cover the matrix below.

## 6. API and architecture test matrix

All IDs below are **planned**, not executed. `U` = unit; `C` = public contract; `I` = real PostGIS/HTTP integration; `A` = architecture; `N` = negative; `B` = boundary. Expected results are independent of the implementation's private algorithms.

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

### 6.1. Contract-test design checklist

For every listed public method: valid representative input; invalid type/value; boundary (empty, max length or time); dependency failure; stable error class/code; deterministic output; no leaked private internals. API tests must additionally verify OpenAPI, status codes, serialization (GeoJSON `Polygon`/`MultiPolygon`, dates, enums), absence of synthetic/live confusion and country-specific availability. Capture request/response golden fixtures for the future React tests.

### 6.2. Architecture enforcement choices

- Baseline: a small read-only `ast` import inspection plus dependency matrix can cover public-only imports, forbidden imports, and simple cycles without adding a dependency.
- Candidate alternative: **Import Linter / Grimp** enforces explicit independence, acyclic siblings and forbidden imports; use only if separately approved as a new development dependency.
- Mutation checks: construct a deliberately forbidden cross-module import in an isolated **temporary fixture**, verify the architecture check fails, then remove it. Never weaken tests or source rules to force a pass.
- Code style/types: Ruff, strict pyright, pytest; run `bash ./run-tests.sh` after the approved backend tooling is installed.

## 7. Open-source and established solution survey

Research conducted for this draft, **not evidence that a library or dataset is already installed or approved**:

| Candidate / source | Existing capability | Fit and trade-off | Decision for MVP-01 |
| --- | --- | --- | --- |
| [FastAPI dependency overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/) | Tests can replace injected collaborators | Strong for HTTP contract tests; does not prove real PostGIS integration | Preferred testing technique after dependency approval |
| [PostGIS](https://postgis.net/docs/) | Spatial types, validated geometry and spatial operators | Appropriate for persisted boundaries; real DB is required for integration tests | Chosen by umbrella |
| [Shapely](https://shapely.readthedocs.io/) / [pyproj](https://pyproj4.github.io/pyproj/stable/) | Geometry validity and coordinate transforms | Avoid inventing spatial math; audit geometry/CRS carefully | Evaluate, request approval |
| [GeoPandas](https://geopandas.org/en/stable/) / [pyogrio](https://pyogrio.readthedocs.io/) | Import/reproject common vector formats | Useful for offline reference import; may add heavy dependency footprint | Optional; avoid in application hot path unless justified |
| [Import Linter](https://import-linter.readthedocs.io/en/stable/) | Forbidden/layered/acyclic import contracts | Mature architecture check; extra tooling to approve | Compare with stdlib AST gate |
| [Geofabrik administrative data](https://www.geofabrik.de/data/admin-polygons.html) | OSM-derived boundary/hierarchy processing | License/coverage/hierarchy may need separate preparation or paid service; not a verified RU/BY reference | Candidate only; **not** approved geography data |

Review authoritative RU/BY administrative inventories and license-compatible GIS polygons separately before claiming coverage. Do not use a generic OSM extract or old Saturn code as proof of full district coverage. Record chosen sources, version, access rights, normalization decisions and justified exclusions in the approved implementation plan prior to import.

## 8. Commands, quality gates and handoff

Verified existing check command (documentation-only scaffold):

```bash
bash ./run-tests.sh
```

Proposed commands **after dependency and tooling approval, not currently runnable**:

```bash
python3 -m pytest -p no:cacheprovider backend/tests/unit backend/tests/contract
python3 -m pytest -p no:cacheprovider backend/tests/integration backend/tests/architecture
python3 -m ruff check --no-cache backend
python3 -m ruff format --check backend
python3 -m pyright backend
bash ./run-tests.sh
```

Check real catalog completeness and PostGIS geometry against **verified authorized fixtures** in the acceptance environment. Add `docs/INSTALLATION.md`, `docs/USAGE.md`, and `docs/TESTS.md` only when actual reproducible commands exist. Do not start live source ingestion or mark synthetic fixtures as real. Preserve the `MVP-01` browser scenario as a dependency of the later frontend sub-spec.

**Backend readiness evidence:** every `MVP01-BE-Axx` checked; OpenAPI and representative JSON fixture examples stable; complete territory reference provenance and coverage report; real PostGIS integration tests; independent agent/ecology scenarios; architecture checks; developer sign-off. **Stage completion remains pending** until the separately planned React sub-spec and browser E2E pass.

## 9. Risks and recovery

| Risk | Prevention / recovery |
| --- | --- |
| Authoritative geography unavailable or license unclear | Block completeness acceptance; record source-gap explicitly; do not replace missing polygons with fabricated shapes |
| Different administrative definitions across datasets | Keep reference version, kind and provider mappings separate; reject ambiguous joins until reviewed |
| Demo ecology mistaken for real prohibition | Distinguish fixture mode, fictional rules, warnings and real map layer provenance in every API output |
| Implicit/unbounded execution | Enforce graph and agent budgets, typed tool registry, deadline, cancellation and explicit failures |
| PostGIS unavailable or migration fails | Stop acceptance, roll back transaction, retain immutable migrations, rerun in fresh test database |
| Dependency creep / circular imports | Preserve proposed module ownership and architecture tests before adding adapters |
| Source unexpectedly calls a live website/Saturn | Offline fixture test forbids outbound calls and fails immediately |
| Complex initialization or partial deployment | Verify `run-tests.sh`, a clean environment and read-only integration checks; keep scaffolding usable |

**No code has been generated or executed by this document.** Plan approval is a separate developer decision.
