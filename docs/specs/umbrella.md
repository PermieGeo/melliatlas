# MelliAtlas — Umbrella Product Specification

**Version:** 0.4 (initial repository draft)  
**Status:** Draft — requires explicit developer approval  
**Product:** Sustainable migratory beekeeping, pollinator conservation, and ecological research  
**Delivery approach:** A functioning vertical-slice MVP in stage `MVP-01`; every later stage incrementally improves the working application.

> **Specification boundary.** This document defines intended product outcomes, cross-cutting constraints, and the ordered stage roadmap. It does **not** assert that any planned feature is implemented, authorize work on a stage, or substitute for its future active sub-specification and separate implementation plan. Technical details marked *to be decided in sub-spec* are deliberately unresolved, not tacit requirements.

## 1. Mission and decision framework

### 1.1. Mission

MelliAtlas helps people plan the seasonal placement and movement of managed honey-bee apiaries while protecting wild pollinators, sensitive habitats, and ecological processes. Its initial user is a beekeeper seeking a productive sequence of nectar and pollen opportunities throughout a honey-flow season. Conservation practitioners and scientists are equally important long-term beneficiaries of the underlying evidence and analysis capabilities.

**Product success is not defined as maximum honey yield alone.** A productive location may be incompatible with a verified legal restriction, may raise a scientifically plausible ecological concern, may be unreachable, or may be too poorly understood to recommend with confidence. MelliAtlas must expose those distinctions and offer alternatives rather than hide them in a single opaque score.

### 1.2. Three connected domains

1. **Migratory beekeeping:** identify candidate stops, interpret seasonal flowering opportunities, build and revise an apiary relocation sequence, consider colony wellbeing and practical constraints.
2. **Conservation and stewardship:** identify legally restricted sites and ecologically sensitive habitats; examine potential competition for floral resources, pressure from concentrated apiaries, and other scientifically supported concerns; support more compatible placement choices.
3. **Scientific research and monitoring:** compare habitats and seasons, examine spatial patterns and uncertainty, reproduce analyses, and eventually collect standardized field observations over multiple years.

These are perspectives on one evidence-backed geographic product, not three separately built applications. The beekeeper scenario establishes the first usable release; conservation is a first-release constraint; dedicated research and longitudinal monitoring arrive in later stages.

### 1.3. Primary product question

For a specified apiary, area, and season:

> Which sequence of candidate placements and time periods could make good use of available flowering resources while respecting verified restrictions, reflecting ecological uncertainty, and remaining practical for the beekeeper?

The result is a **proposed decision-support plan**, not an instruction that a site is legally accessible, safe, ecologically harmless, or guaranteed to produce a quantity of honey.

### 1.4. Product objectives

- Produce understandable, source-backed seasonal placement alternatives instead of isolated map markers.
- Make honey-flow continuity, flowering periods, and gaps visible.
- Consider both managed bee colonies and wild pollinator/habitat interests when screening sites.
- Distinguish observed evidence, model estimates, assumptions, unknowns, and synthetic demonstration data.
- Support investigation and revision when information conflicts or proves insufficient.
- Keep geospatial analyses reproducible to the extent supported by captured inputs, algorithms, and external data versions.
- Extend from one local demonstration to supported territories in Russia and Belarus without embedding particular districts or provider IDs in business logic.
- Support long-term scientific workflows only when their distinct requirements are designed and tested.

### 1.5. Out of scope as a product promise

MelliAtlas must not claim to issue permits, establish binding environmental policy, certify ecological harmlessness, diagnose colony diseases, guarantee harvests, or prove ecological causation from correlations. The application cannot replace field surveys, professional ecological judgment, landowner permission, or legal review. Exact yield forecasts, species-specific ecological thresholds, and safe colony densities require appropriate scientific evidence and separate validation.

## 2. Users and principal workflows

### 2.1. User groups

| User | Main decision or task | Initial availability |
| --- | --- | --- |
| Migratory beekeeper | Compare seasonal stops and consider relocations | Core experience from `MVP-01` |
| Stationary beekeeper | Review surrounding forage and constraints | Limited by the same planning flow; refine later |
| Conservation practitioner / protected-area specialist | Examine protected habitats, restrictions, and placement alternatives | Ecological constraints from `MVP-01`; analytical workspace later |
| Ecologist / entomologist | Compare pollinator observations, habitats, methods, and changes over time | Evidence analysis later; field recording in `MVP-13` |
| Data curator / participating organization | Supply trustworthy datasets, document methods, and manage access | Later stages, not an initial user-management platform |

### 2.2. UC-01 — Seasonal migration planning

**Input:** a geographic study area, a season or planning interval, an apiary starting position, and any supported operating constraints.

**Expected outcome:** an ordered set of candidate stops with proposed time windows, map locations, evidence about forage opportunity, meaningful constraints, an explanation of selection, and alternatives. A plan may be incomplete when evidence is insufficient. The first stage uses synthetic inputs and a deliberately narrow rule set. Smolensk Oblast is the intended initial real-world pilot area, subject to verified data availability; no specific district or provider identifier is hardcoded into product logic.

**Failure behavior:** missing territory, invalid dates/geometry, infeasible constraints, or insufficient usable sites result in explicit diagnostic output, never a fabricated plan.

### 2.3. UC-02 — Ecology-aware alternative selection

A candidate may be attractive for forage yet overlap a verified restriction or raise a documented ecological concern. MelliAtlas must distinguish these cases, reject legally or explicitly constrained placements when the rule applies, qualify scientific concerns, and look for viable alternatives. The reasoning must identify the evidence, its coverage and date, and which rule or interpretation was used.

### 2.4. UC-03 — Evidence-driven re-examination

During an investigation, newly obtained information can invalidate or weaken an initial candidate. The analysis agent may select an additional registered tool, inspect its result, and revise the proposal. If no suitable additional tool or evidence exists, it must stop within configured bounds and explain the unresolved uncertainty.

### 2.5. UC-04 — Previous results and comparisons

A user can reopen completed investigations without silently overwriting previous results. Later releases allow comparison across times, territories, algorithms, data versions, or alternative assumptions. Retention and access restrictions depend on deployment and sensitivity.

### 2.6. UC-05 — Conservation and research analysis

A qualified user examines a location or group of locations, including forage availability, managed-apiary pressure where known, sensitive habitats, pollinator observations, and uncertainties. The application supports comparisons and exports with provenance. It must not infer a causal ecological effect merely because two observations are spatially correlated.

### 2.7. UC-06 — Long-term field observations

A later stage supports structured field records with observation time, geometry, taxon or observation type, identification confidence, sampling method and effort, recorder, permissions, and dataset provenance. Authorized users can revise and analyze observations across years without corrupting original evidence. This workflow is **not** part of the first MVP.

## 3. Domain terms and semantics

The following terms guide future sub-specification design. Exact database schemas and API types belong to the selected stage.

- **Apiary:** a beekeeper-managed group of colonies associated with a location or an intended placement. Private coordinates are sensitive.
- **Colony:** a managed honey-bee family; quantities and condition may affect future planning, but are not inferred without evidence.
- **Candidate stop:** a location considered for placement, without implying access rights or suitability has been established.
- **Stop window:** a proposed period of presence at a candidate stop.
- **Migration plan:** an ordered sequence of stop windows and relocations, with assumptions and alternatives.
- **Honey flow / forage opportunity:** a period and area with potentially useful nectar/pollen resources; an opportunity is not a measured yield.
- **Flowering evidence:** observed, reported, or modeled occurrence and timing of flowering with a source and uncertainty.
- **Habitat sensitivity:** a concern established by ecological evidence, protected-area designation, or expert inputs. It is **not** automatically a legal exclusion.
- **Verified restriction:** a confirmed rule applicable to a location and time, with authority, effective dates, geometry, and interpretation status.
- **Potential ecological conflict:** a plausible adverse interaction requiring consideration, further evidence, or precaution; it is not proof of damage.
- **Research observation:** a time- and place-associated record with method and detection/identification information.
- **Research effort:** details of sampling that allow interpretation of whether an absence of observations is meaningful.
- **Analysis run:** a particular set of inputs, executed operations, versions, and produced artifacts.
- **Artifact:** a typed, attributable input or output of a source, analyzer, or agent decision.

### 3.1. Evidence categories

The product must preserve distinctions between:

1. `SYNTHETIC` — deliberately invented input for testing/demonstration.
2. `OBSERVED` — recorded measurement or field observation with limitations.
3. `REPORTED` — information provided by a source or authority, not independently measured by the system.
4. `DERIVED` — deterministic transformation or computed result.
5. `MODEL_ESTIMATE` — prediction or inference with stated assumptions and validation status.
6. `UNKNOWN` — information absent, conflicting, or unsuitable for a conclusion.

These are conceptual evidence categories. Whether represented as one enum, several linked fields, or another typed model will be decided by sub-specs. Confidence must not be represented as an arbitrary percentage unsupported by calibration.

### 3.2. Constraint categories

- **Binding restriction:** an applicable verified legal/administrative rule or other explicitly required hard placement constraint. Record authority and effective scope.
- **Operational constraint:** access, travel, placement permissions, timing, costs, and beekeeper preferences; may be hard or soft according to its defined semantics.
- **Ecological consideration:** sensitivity or possible competitive pressure; preserve evidence strength and uncertainty rather than inventing universal prohibitions.
- **Unknown:** unverified coverage or unavailable evidence; report it explicitly.

A positive forage assessment must never override a binding restriction. An ecological concern must not silently become a legal ban. Conversely, a site's absence from a protected-area dataset does not establish ecological safety or legal access.

## 4. Product-level system constraints

The requirement IDs below are umbrella-wide anchors. Sub-specs must refine and test those that become relevant to their selected stage; they must not pretend all later features exist from `MVP-01`.

### 4.1. Planning and ecological integrity

- **SYS-01 — Dual objective.** Site and seasonal-plan evaluations must consider forage opportunity and ecological compatibility whenever the corresponding evidence exists. Hard constraints take precedence over comparative ranking.
- **SYS-02 — Uncertainty.** Every recommendation must distinguish established findings, assumptions, potential concerns, and missing evidence. An unknown condition cannot be silently treated as favorable.
- **SYS-03 — Alternatives.** When a candidate is invalidated, the system should investigate alternatives available within the run's scope; if none qualify, it must report that outcome.
- **SYS-04 — No fabricated thresholds.** Numeric distances, foraging radii, colony densities, legal buffers, and impact scores require an explicit basis. Synthetic examples must be labeled as such.
- **SYS-05 — Explainable seasonal sequence.** A plan identifies proposed stops, time windows, transitions, contributing factors, limitations, and reasons for material revisions.

### 4.2. Data provenance and scientific accountability

- **SYS-06 — Provenance.** Preserve origins, retrieval/observation time when available, applicable geography, input versions, transformations, and algorithm versions needed to audit material results.
- **SYS-07 — Evidence separation.** Do not present synthesized results, LLM output, historical reports, and direct observations as interchangeable evidence.
- **SYS-08 — Temporal validity.** Apply evidence within its documented temporal coverage; stale or out-of-period input must be flagged or rejected by explicit policy.
- **SYS-09 — Scientific limits.** Never convert association into causation without justified study design. Avoid unvalidated yield, colony-health, or biodiversity impact verdicts.
- **SYS-10 — Reproducibility.** Store sufficient inputs/versions to review a completed run. An LLM's live response need not be bit-for-bit reproducible; a saved decision and its supporting evidence must be inspectable.

### 4.3. Spatial integrity and rights

- **SYS-11 — Geometry.** Treat coordinates, coordinate reference systems, spatial precision, invalid geometries, and boundaries explicitly. Do not use unqualified geographic-coordinate distances as meters.
- **SYS-12 — Territories.** The territory model must remain independent of one country's provider-specific identifiers. Initially a synthetic demonstration area is allowed; Russia and Belarus are target configurations for later coverage.
- **SYS-13 — Data acquisition.** Integrate real providers only after confirming availability, permitted use, attribution, rate limits, data coverage, and failure handling.
- **SYS-14 — Sensitive locations.** Prevent unauthorized disclosure of private apiary coordinates and sensitive species/habitat records, including through exports, logs, map layers, and cross-user responses.
- **SYS-15 — Permission versus recommendation.** A recommended stop is not proof of landowner consent, access, legal compliance, or absence of ecological impacts.

### 4.4. Execution and user interaction

- **SYS-16 — Typed capabilities.** Sources and analyzers expose clear, testable input/output capabilities. A caller must not rely on a component's private implementation.
- **SYS-17 — Bounded agency.** An automated agent may invoke only registered, validated tools and is subject to finite step, time, and resource limits; error conditions must be visible.
- **SYS-18 — Traceable decisions.** Capture enough intermediate findings to explain when and why an agent revised or ended an investigation.
- **SYS-19 — Durable results.** Completed results remain accessible according to the release's stated persistence guarantees. More advanced job recovery arrives in `MVP-04`.
- **SYS-20 — Continuous usability.** Every completed stage must leave the main browser-based planning scenario runnable and testable, or clearly document a developer-approved migration.

## 5. Technology and component responsibilities

This is the **agreed technical direction**, not a demand to implement all components fully in the first stage.

| Concern | Chosen direction | Boundary |
| --- | --- | --- |
| Backend and API | Python, FastAPI, Pydantic | Typed HTTP interface and application coordination |
| Analysis Engine | Python | Registered Sources/Analyzers, artifacts, DAG/execution primitives |
| Agent | Python; deterministic first, optional LLM later | Goal/plan/observe/replan/finish using bounded registered tools |
| Persistence | PostgreSQL with PostGIS | Geometry, runs, artifacts, plans, history, and later caches |
| Worker | Separate Python process in a later stage | Durable background execution, retries, recovery |
| Web | React, TypeScript, Vite, Tailwind CSS | Browser interaction, map, planning timeline, evidence views |
| Map | Leaflet / React Leaflet | Display layers and site candidates; map basemap need not be server-stored |
| Quality | pytest, pyright, Ruff, Playwright | Contract, behavioral, architectural, integration, UI/E2E checks |

### 5.1. Responsibility boundaries

- **Sources** obtain or provide data under declared capabilities, geography, coverage, and permissions; initial sources are synthetic.
- **Analyzers** transform typed inputs into attributable analytical outputs. Spatial and temporal operations must be independently testable.
- **Engine** validates and executes planned dependencies. It must support a predefined plan without an LLM.
- **Agent** chooses and revises analysis steps based on goals, available capabilities, and evidence. It cannot execute arbitrary generated code or bypass tool validation.
- **Persistence** stores run state and artifacts under explicit lifecycle, version, and sensitivity rules.
- **API** provides stable typed operations without exposing internal classes to the browser.
- **Web** presents the user's workflow, geographic results, explanation, uncertainty, and later scientific tasks.

Module boundaries, file placement, API endpoints, migrations, and implementation algorithms must be refined against the **verified codebase** in the active stage's implementation plan. Do not build speculative general-purpose plugin infrastructure, microservices, separate administration UI, or a universal GIS workflow platform.

### 5.2. Incremental architecture

The first stage deliberately implements the thinnest useful variant of each necessary component. A small in-process executor can be sufficient for the initial demonstration; durable workers and recovery follow later. A simple deterministic planning rule can demonstrate adaptive decisions; generalized re-planning and optional LLMs follow later. Later stages must build on these contracts instead of replacing the application with an unrelated framework.

## 6. Delivery rules, acceptance, and traceability

### 6.1. Vertical-slice rule

`MVP-01` must demonstrate **browser → API → analysis components → saved result → map and timeline**. It cannot be declared complete solely because a Python package, DAG executor, or set of unit tests exists. Later stages preserve that user journey and add observable capabilities. Infrastructure-only work within a stage is acceptable, but the stage gate must demonstrate a product improvement or measurable reliability gain in the running application.

### 6.2. Scope and approval

The stage descriptions below are deliberate **umbrella-level detail**. Only the selected stage receives a normative, detailed sub-spec and a separate advisory implementation plan. Do not generate future plans or claim future implementation paths as existing. All stages remain planned until the developer chooses and approves one.

### 6.3. Requirement identifiers

- Stage identifiers: `MVP-01` through `MVP-13`.
- Umbrella-wide requirement identifiers: `SYS-01` through `SYS-20`.
- Stage requirement identifiers: `MVP-XX.R01`, `MVP-XX.R02`, and so on; acceptance scenarios use `MVP-XX.A01`, etc.
- Future sub-specs may refine these into more granular testable requirements without changing their parent references.
- Stable product capability `feature_id` values belong **only** in `docs/FEATURES.md`, with stage/spec/owner/test associations in `docs/specs/feature-cross-ref.yaml`. Do not use stage or requirement IDs as substitutes for stable feature IDs.

No permanent feature IDs or implementation owner paths are invented in this umbrella draft. Populate cross-references when the corresponding feature and verified code ownership are established.

### 6.4. Test-first and architecture verification

For every active stage, its implementation plan must identify meaningful initially failing tests before implementation, the independent observable expectation of each test, and the changes needed to make tests pass. Include positive, negative, boundary, failure, and regression cases as applicable. Architecture tests should verify established module boundaries, permitted dependencies, public contracts, and import cycles; integration tests should cover PostGIS and durable behavior when relevant; browser flows should use E2E tests. Do not pass tests by skips, dummy assertions, loosened enforcement, or evidence fabricated from simulation.

### 6.5. Stage result requirements

Every completed stage should provide:

1. A repeatable local/demo workflow through the existing web UI.
2. A specifically identified change in user-facing capability, research value, or operational reliability.
3. Test evidence for new scenarios and regression protection for the initial planning flow.
4. Updated provenance, privacy, and uncertainty behavior when new evidence types are introduced.
5. No automatic advancement of `STATE.json`, archival, or acceptance without an explicit developer decision.

## 7. Roadmap overview

| Stage | Product increment | Mandatory predecessor |
| --- | --- | --- |
| `MVP-01` | Full synthetic beekeeper planning slice with ecology-aware alternative and React map | Repository scaffold |
| `MVP-02` | Better forage, flowering intervals, and honey-flow continuity | `MVP-01` |
| `MVP-03` | Evidence-aware adaptive agent and decision-trace comparison | `MVP-02` |
| `MVP-04` | Robust jobs, server caching, recovery, and run history | `MVP-03` |
| `MVP-05` | Country-aware geography and multiple territories (RU/BY) | `MVP-04` |
| `MVP-06` | First verified real geospatial/forage source | `MVP-05` |
| `MVP-07` | Weather-informed phenology and season adjustments | `MVP-06` |
| `MVP-08` | Stronger habitat/protected-area evidence and ecological compatibility | `MVP-07` |
| `MVP-09` | Bee-family conditions, agricultural hazards, site feasibility | `MVP-08` |
| `MVP-10` | Constrained multi-stop seasonal planning and alternatives | `MVP-09` |
| `MVP-11` | Optional validated LLM planning and comparison | `MVP-10` |
| `MVP-12` | Conservation and research comparison workspace | `MVP-10`; LLM not required |
| `MVP-13` | Field observations and long-term ecological monitoring | `MVP-12` |

The table defines a **default logical order**, not an immutable dependency graph: `MVP-11` is optional for research features, and a future approved umbrella revision may reorder a stage without retroactively inventing implemented behavior. The stage IDs remain stable unless the developer approves a normative change.

---

## 8. Stage specifications

### MVP-01 — Working sustainable-beekeeping MVP

**Objective.** Deliver a locally runnable, complete MelliAtlas application with a genuinely usable *demonstration* of apiary relocation planning and ecology-aware site selection. This is a product MVP, not a foundation-only sprint.

**User outcome.** In the browser, a beekeeper selects a demonstration area and season, runs an investigation, sees a proposed sequence of apiary stops on a map and timeline, understands why a promising site was excluded, and can reopen the completed result.

**Required behavior**

- `MVP-01.R01` — Start a Python/FastAPI backend and one mobile-friendly React/TypeScript/Leaflet frontend. The main workflow is accessible through that browser client; do not create a separate admin app.
- `MVP-01.R02` — Supply one clearly **synthetic** study area, one example apiary starting point, at least three candidate sites, and illustrative flowering/forage intervals that can support at least two planned stops and a relocation.
- `MVP-01.R03` — Implement minimal typed Source and Analyzer contracts, a small registry, and execution of several dependent operations. Source, analyzer, and agent behavior must be independently testable; full generic orchestration is not required.
- `MVP-01.R04` — Implement a bounded deterministic agent that proposes a candidate, observes the result of an additional registered ecological check, and revises the plan when the result conflicts with a defined demonstration constraint. This must result from the check's output, not a one-off hardcoded branch on a demo location ID.
- `MVP-01.R05` — Model at least one synthetic **binding-for-the-demo** exclusion zone and one synthetic *precautionary* ecological area. The former excludes a candidate under an explicit synthetic rule; the latter generates an explanation/uncertainty rather than an invented legal ban. The UI must identify both as fictional.
- `MVP-01.R06` — Form a simple ordered seasonal proposal with candidate coordinates, proposed time windows, at least one transition, qualitative forage rationale, selection/rejection reasons, and available alternative(s). No numerical honey-yield forecast.
- `MVP-01.R07` — Persist the completed investigation, chosen alternatives, and relevant geometries in PostgreSQL/PostGIS. Allow the browser to reopen a previously completed result after a page reload.
- `MVP-01.R08` — Display a map with candidate/selected/rejected sites, a simple schedule, progress or completion state, and an evidence/limitations panel. Clearly mark all data and conclusions as demonstrative.
- `MVP-01.R09` — Provide diagnostic errors for invalid inputs, missing data, impossible plans, invalid geometries, failed operations, and exceeded agent limits. A missing viable candidate must not be converted into a recommendation.

**Explicit scope limits.** One synthetic area and one local demonstration scenario; no real weather or land-use integration, real treatment notice, validated ecological impact model, login, multi-tenant access, public apiary sharing, road routing, or production-quality job recovery. An in-process executor is acceptable. Persist **completed results**; a process interrupted mid-run may require a new run until `MVP-04`. The first stage need not install a separate worker or use an LLM.

**Acceptance evidence**

- `MVP-01.A01` — Automated browser E2E: select the area/season, start the run, see at least two ordered stops, show site geometry and a relocation on the map/timeline, reload, and reopen the same completed result.
- `MVP-01.A02` — Agent scenario: an initially attractive site is rejected only after the synthetic restriction tool returns applicable evidence; the final plan selects an available alternative and records why the plan changed.
- `MVP-01.A03` — The precautionary zone produces a qualified warning rather than a fabricated prohibition; an explicit forbidden site is never selected as valid.
- `MVP-01.A04` — Independent unit/contract/integration tests verify typed component calls, dependency order, persistence, invalid inputs, empty outcomes, and finite agent execution.
- `MVP-01.A05` — No page or API output implies that synthetic locations, legal restrictions, flowering intervals, ecological risks, or yields are real.

**Completion gate.** A reviewer can run the application locally, complete the entire scenario through React, inspect the persisted result and agent's reasoning, and obtain passing focused automated checks. No subsequent stage is a prerequisite to declare this **synthetic** MVP complete.

### MVP-02 — Forage and flowering continuity

**Objective.** Improve the agronomic usefulness of the existing seasonal plan without claiming validated nectar production or honey yield.

**Required behavior**

- `MVP-02.R01` — Represent relevant forage categories and flowering evidence using time ranges, spatial extent, source, and evidence type. Distinguish nectar/pollen opportunity from measured harvest.
- `MVP-02.R02` — Support beginning, expected peak, and ending of flowering where known; missing dates remain missing rather than being replaced with arbitrary defaults.
- `MVP-02.R03` — Compare periods across candidate sites, identify overlap and potential gaps, and explain how they affect a proposed relocation sequence.
- `MVP-02.R04` — Compute a transparent, relative demonstration assessment of forage opportunity; make weights/rules inspectable and avoid scientifically unvalidated yields.
- `MVP-02.R05` — Allow a user to compare at least two seasonal alternatives in the existing map/timeline interface, including differences in gap coverage.
- `MVP-02.R06` — Preserve ecological screening from `MVP-01` when forage inputs or the relative ordering of candidate sites changes.

**Non-goals.** Species-complete botanical coverage, predictive climate modeling, universal foraging radii, or an authoritative yield calculator.

**Acceptance evidence**

- `MVP-02.A01` — Fixed synthetic flowering intervals produce correct overlapping/adjacent/gap classifications, including year-boundary and missing-date cases.
- `MVP-02.A02` — Changing flowering evidence can change the plan ranking while a forbidden candidate stays excluded.
- `MVP-02.A03` — UI comparison states the source and limitations of forage assessments; previous `MVP-01` end-to-end behavior remains functional.

**Implementation questions for the later sub-spec.** Which forage taxonomies and temporal granularity are necessary; what relative assessment is meaningful without introducing false precision; how does a user inspect competing flowering claims?

### MVP-03 — Evidence-aware adaptive planning

**Objective.** Generalize the initial agent demonstration into a reusable, bounded decision process for a variety of incomplete or contradictory spatial investigations.

**Required behavior**

- `MVP-03.R01` — The agent discovers available typed capabilities and can form a dependency-aware plan rather than using one predetermined task chain.
- `MVP-03.R02` — Support at least the outcomes `continue`, `request additional evidence`, `revise`, `finish`, and `stop with insufficient evidence`, with explicit reasons and finite execution bounds.
- `MVP-03.R03` — Handle conflicting forage or ecological evidence without silently taking the most favorable value; record which interpretation was chosen or why the question remains unresolved.
- `MVP-03.R04` — Keep an inspectable sequence of material plans, tool choices, observations, and revisions linked to run artifacts.
- `MVP-03.R05` — Provide a comparison harness for a fixed pipeline and the deterministic adaptive agent running against identical input fixtures. Avoid claiming universal agent superiority.
- `MVP-03.R06` — Include independent checks that reject invalid tool parameters, unregistered operations, circular dependencies, repeated fruitless actions, and unbounded replanning.

**Non-goals.** LLM inference, unrestricted natural-language tool creation, or autonomous policy/law interpretation.

**Acceptance evidence**

- `MVP-03.A01` — Contradictory, incomplete, and sufficient-evidence fixtures cause distinguishable, justified behaviors; the agent does not always choose the same branch.
- `MVP-03.A02` — A scenario requiring an additional check produces a more defensible output than the fixed baseline according to an explicitly specified oracle; an unnecessary tool-call scenario penalizes wasteful replanning.
- `MVP-03.A03` — Invalid tools and impossible goals terminate safely with a recorded reason; the browser can display the decision history.

**Implementation questions for the later sub-spec.** Agent/Engine execution boundary, representation of an observation and decision, loop detection, capability discovery, and objective test oracles.

### MVP-04 — Durable execution, cache, and history

**Objective.** Make investigations reliable across browser disconnects and backend/worker interruptions, and avoid unnecessary repeated data collection or analysis.

**Required behavior**

- `MVP-04.R01` — Run long investigations through a separate Python worker with persisted job status and progress, independent of HTTP request lifetime.
- `MVP-04.R02` — Define persisted job lifecycle states and safe state transitions, including cancellation, failure, timeouts, and retryable errors.
- `MVP-04.R03` — Support crash/restart recovery with explicit behavior for interrupted operations; ambiguous execution must not silently duplicate externally visible results.
- `MVP-04.R04` — Introduce cache identities based on relevant input, source, version, geographic/temporal coverage, and algorithm configuration; reuse only suitable entries.
- `MVP-04.R05` — Preserve distinct run versions and decisions; refreshing a plan must not erase the preceding plan or its evidence.
- `MVP-04.R06` — Expose progress, restart/retry outcomes, and previous results through the existing browser without requiring a separate administration interface.

**Non-goals.** Multi-region distributed orchestration, arbitrary workflow plugin marketplace, or cloud-specific queue infrastructure without demonstrated need.

**Acceptance evidence**

- `MVP-04.A01` — Restart a worker during a controlled test: the job resumes safely or reaches a diagnostic terminal state according to the stated policy.
- `MVP-04.A02` — Repeated delivery does not duplicate completed run effects; cancel, timeout, and retry transitions are independently verified.
- `MVP-04.A03` — Cache hit, cache miss, invalidation, and stale-evidence tests produce correct outcomes; browser history contains both original and revised plans.

**Implementation questions for the later sub-spec.** Transaction boundaries, job claiming, cache lifecycle, idempotency keys, locks/leases, and test-environment restart orchestration.

### MVP-05 — Multiple territories and country configurations

**Objective.** Extend the usable planning area beyond a single demonstration polygon while preserving provider independence and reliable spatial behavior.

**Required behavior**

- `MVP-05.R01` — Introduce an explicit territory hierarchy suitable for Russia and Belarus, with country-aware differences in administrative structure and versioned identifiers.
- `MVP-05.R02` — Separate internal territory identity from provider codes and local example-data seeds; no business logic assumes Smolensk Oblast or any one district.
- `MVP-05.R03` — Support selection, inspection, and comparison across multiple districts or neighboring areas in the web interface.
- `MVP-05.R04` — Express each source's actual geographic/temporal coverage and handle partial coverage when a plan crosses boundaries.
- `MVP-05.R05` — Validate coordinate systems, polygon operations, boundary adjacency, and inaccurate or missing geometries.
- `MVP-05.R06` — Preserve prior demonstration plans and histories through migration of territory representations.

**Non-goals.** Exhaustive complete official territory catalogs or real-time availability of country-wide provider data; initial RU/BY configuration does not imply live coverage.

**Acceptance evidence**

- `MVP-05.A01` — Country-specific fixture territories work without provider-bound identifiers; invalid and ambiguous administrative references are rejected.
- `MVP-05.A02` — Spatial tests cover border-crossing, multipolygons, coordinate transformation, invalid geometry, and partial source coverage.
- `MVP-05.A03` — A multi-territory user journey works in React; original single-area scenario remains runnable.

**Implementation questions for the later sub-spec.** Data authority for borders, handling of changing boundaries and disputed designations, coordinate precision, and local seed/import strategy.

### MVP-06 — First verified real data integration

**Objective.** Prove that the planning engine can use a permitted, attributable real-world dataset without losing the ability to distinguish evidence from assumptions and synthetic fixtures.

**Required behavior**

- `MVP-06.R01` — Select a real geospatial, land-cover, forage, or agricultural source based on utility to planning, access terms, geographic coverage, update cadence, and technical feasibility. The specific provider is chosen during the sub-spec's research, not invented here.
- `MVP-06.R02` — Implement a source adapter behind the established Source contract, with configuration-driven location and credentials; never embed a region or provider URL in domain logic.
- `MVP-06.R03` — Retain source identification, applicable license/attribution, acquisition time, original geometry/attributes where permitted, and normalization details.
- `MVP-06.R04` — Handle unavailable/partial responses, pagination where relevant, rate limiting, provider schema changes, inconsistent geometries, and retries within agreed limits.
- `MVP-06.R05` — Separate and visually label real-source records, user-provided records, synthetic fixtures, and derived/model values in result artifacts and the web UI.
- `MVP-06.R06` — Support a mixed investigation: a permitted real dataset may contribute evidence while other required inputs remain synthetic or explicitly unknown. No synthetic fallback is silently presented as live observation.
- `MVP-06.R07` — Preserve previous plan versions and guarantee that a provider failure does not transform unverified or stale evidence into a confident recommendation.

**Non-goals.** Real-time coverage for all territories, guaranteed availability of any named government portal, or automatic bulk harvesting contrary to source terms. Do not assume a source can substantiate flowering or ecological safety merely because it provides crop/land-cover geometry.

**Acceptance evidence**

- `MVP-06.A01` — Recorded/controlled provider fixtures and a permitted smoke test demonstrate parsing, geometry validation, attribution, pagination/partial responses where relevant, and transparent source errors.
- `MVP-06.A02` — Repeated runs reuse stored source versions according to policy; changes in incoming data are traceable and do not rewrite old conclusions.
- `MVP-06.A03` — The UI explicitly displays which parts of the analysis use real data, synthetic data, or unknown inputs. Mixed-evidence runs are not described as fully verified.

**Implementation questions for the later sub-spec.** Provider choice after current research, licensing, caching rights, legal attribution, format coverage, adapter failure policy, and representative integration tests. Never make a live-source assertion without checking it.

### MVP-07 — Weather-aware phenology and seasonal uncertainty

**Objective.** Extend static flowering intervals with justified seasonal variability and weather-related evidence, without introducing an unvalidated yield forecast.

**Required behavior**

- `MVP-07.R01` — Ingest weather observations and/or forecasts from a selected permitted source with clear geographic resolution, time period, units, and forecast validity.
- `MVP-07.R02` — Represent expected flowering windows and their uncertainty separately from recorded flowering observations; update estimates when the inputs or model version change.
- `MVP-07.R03` — Support at least one interpretable, appropriately qualified phenology method established by available evidence; identify its geographical and species limitations.
- `MVP-07.R04` — Recompute forage continuity and potential stop windows when changed weather/flowering evidence materially alters seasonal opportunity.
- `MVP-07.R05` — Explain which new evidence caused a revised seasonal plan and which predicted intervals have not been independently validated.
- `MVP-07.R06` — Keep an auditable distinction between past measurements, near-term forecast, seasonal projections, and unknown values.
- `MVP-07.R07` — Reject malformed units, temporal gaps outside model validity, and incompatible data rather than quietly substituting plausible-looking values.

**Non-goals.** Authoritative forecasts of exact honey yield, universal crop phenology, or scientifically validated climate-impact projections without appropriate datasets and evaluation.

**Acceptance evidence**

- `MVP-07.A01` — Deterministic fixtures yield correct date-window calculations, including missing observations, nonuniform sampling, unit conversions, and boundaries between seasons.
- `MVP-07.A02` — A controlled change in weather/phenology evidence produces an understandable change (or justified no-change) in the browser's proposed schedule.
- `MVP-07.A03` — Source/model limitations and uncertainty are displayed alongside the estimate, not hidden behind a generic precision score.

**Implementation questions for the later sub-spec.** Research-supported phenology method, validation data, model evaluation metrics, temporal granularity, interpolation policy, and permitted weather provider.

### MVP-08 — Protected areas, habitat sensitivity, and ecological compatibility

**Objective.** Move from fictional demonstration constraints to a rigorous, source-backed ecological and legal screening of candidate apiary sites while avoiding unsupported universal risk verdicts.

**Required behavior**

- `MVP-08.R01` — Obtain or import verified boundaries and applicable restrictions for supported protected areas, with authority, source, version, validity dates, and coverage clearly attached to each rule.
- `MVP-08.R02` — Model ecological sensitivity outside legally protected areas when trustworthy evidence supports it; do not equate a sensitive habitat with a legal exclusion.
- `MVP-08.R03` — Screen sites and applicable time windows using documented spatial and temporal operations. Show affected geometry, the rule or concern involved, and the input evidence.
- `MVP-08.R04` — Represent potentially shared floral resources, wild pollinator presence, and possible competitive pressure as **research questions/considerations**, not pre-proven population harms.
- `MVP-08.R05` — Support differentiated outcomes: verified constraint, potential concern, no issue detected within known coverage, conflicting input, and insufficient data. No result is an unconditional ecological-safety certification.
- `MVP-08.R06` — Let the planner search for alternatives when a site is constrained or carries a user-defined precautionary preference. Preserve the original site and reason for comparison.
- `MVP-08.R07` — Keep scientific source interpretations and legal-rule interpretations auditable and independently testable; no invented protected-area buffers or universal stocking limits.
- `MVP-08.R08` — Handle sensitive locations of rare species or habitats according to data access rights; generalized map display must not leak underlying precise coordinates.

**Non-goals.** Automatic designation of protected areas, legally binding ecological permits, universal distance thresholds, quantitative proof that managed apiaries reduce wild pollinator populations, or a nationwide complete restriction register.

**Acceptance evidence**

- `MVP-08.A01` — Officially grounded restriction fixtures enforce their stated spatial/temporal scope; nonapplicable or expired rules do not erroneously block a site.
- `MVP-08.A02` — Sensitivity outside an explicitly restricted area is shown as a concern rather than a fabricated legal ban; a protected-area boundary without an applicable restriction is not automatically treated as prohibited.
- `MVP-08.A03` — Coverage gaps, ambiguous boundaries, and conflicting sources generate qualified results and testable explanations.
- `MVP-08.A04` — A beekeeper can see more than one alternative with the forage/ecological trade-offs, and conservation users can inspect the underlying evidence without accessing private coordinates they are not authorized to see.

**Implementation questions for the later sub-spec.** Which jurisdictions and protection categories are first supported, legal-source update policy, ecological models appropriate to available datasets, handling of seasonal habitat importance, and access-control design for sensitive data.

### MVP-09 — Colony wellbeing, agricultural hazards, and site feasibility

**Objective.** Make candidate selection more practical for beekeepers and more responsible toward their colonies without presenting incomplete hazard information as definitive safety assessments.

**Required behavior**

- `MVP-09.R01` — Represent relevant non-sensitive apiary planning parameters (for example colony count or basic constraints) only when supplied and authorized; never infer private colony health from spatial context alone.
- `MVP-09.R02` — Integrate permitted agricultural treatment notices or other relevant hazard signals after verifying their status, dates, geography, and attribution.
- `MVP-09.R03` — Distinguish a **planned or announced treatment**, an observed application, a report of adverse effects, and an inferred exposure concern; these are different evidence types.
- `MVP-09.R04` — Present weather, accessible forage, water or other site feasibility factors only when supported by available data and documented methods.
- `MVP-09.R05` — Show precautionary reminders and reasons to seek local verification rather than asserting a site is safe because a hazard source reports nothing.
- `MVP-09.R06` — Allow hazard evidence and an apiary's user-defined constraints to trigger re-evaluation and alternative selection, without overriding confirmed ecological restrictions.
- `MVP-09.R07` — Maintain confidential apiary-specific data with explicit access controls before enabling hosted or shared deployment.

**Non-goals.** Veterinary diagnosis, pesticide toxicity certification, guaranteed exposure prediction, farmer enforcement workflows, or a universal regulatory notification service. Named registries are potential sources, not guaranteed integrations.

**Acceptance evidence**

- `MVP-09.A01` — Announced, observed, expired, missing, and contradictory hazard notices produce distinct outputs with provenance.
- `MVP-09.A02` — A changed notice can alter the candidate list and is explicitly referenced in the agent's revised plan.
- `MVP-09.A03` — Unauthorized interfaces, logs, or exports cannot reveal a private apiary's precise coordinates.
- `MVP-09.A04` — The browser clearly separates beekeeper risk considerations from ecological impacts of managed colonies on wild pollinators.

**Implementation questions for the later sub-spec.** Rights to treatment datasets, temporal/spatial matching, false-negative communication, privacy model, and which practical site parameters are genuinely useful.

### MVP-10 — Constrained multi-stop seasonal planning

**Objective.** Turn a basic sequence of candidate stops into a defensible comparison of several seasonal migration strategies with competing practical, forage, and ecological objectives.

**Required behavior**

- `MVP-10.R01` — Support a user-configured planning horizon, more than two possible stops, and constraints on relocation frequency, site availability, stop duration, or total travel when provided.
- `MVP-10.R02` — Evaluate temporal ordering, possible honey-flow gaps, and overlap between flowering resources across selected sites.
- `MVP-10.R03` — Keep binding restrictions as feasibility conditions rather than hiding them in a weighted score. Separate precautionary ecological considerations from verified prohibitions.
- `MVP-10.R04` — Present multiple feasible alternatives or explain why no complete feasible plan exists; partial plans may be returned with explicit unmet constraints.
- `MVP-10.R05` — Distinguish geometric distances from verified road travel time/cost. Use routing services only after a supported source and method have been established.
- `MVP-10.R06` — Explain differences between alternatives, including trade-offs between forage continuity, number of moves, practical burden, and ecological considerations.
- `MVP-10.R07` — Support controlled replanning after new weather, flowering, hazard, permission, or habitat evidence changes an assumption.
- `MVP-10.R08` — Preserve the previous plan and its assumptions so a user can compare an updated proposal against the earlier one.

**Non-goals.** Guaranteed global mathematical optimum, automatic booking of private land, verified road accessibility everywhere, or a single scientifically validated conversion of ecological impact and honey yield into one monetary score.

**Acceptance evidence**

- `MVP-10.A01` — Controlled scenarios distinguish feasible, infeasible, partially feasible, and dominated alternatives without choosing a hard-constraint violation.
- `MVP-10.A02` — Adding a temporal or relocation constraint changes or eliminates a plan with an intelligible explanation.
- `MVP-10.A03` — The UI compares alternatives, visualizes transitions, and identifies which travel estimates are geometric versus route-based.
- `MVP-10.A04` — Old and revised plans remain available and the existing `MVP-01` scenario remains valid.

**Implementation questions for the later sub-spec.** Optimization objective representation (including multi-objective/constraint-first methods), computational complexity, model calibration, partial-plan semantics, and independent test oracles.

### MVP-11 — Optional LLM-assisted agent

**Objective.** Introduce a configurable LLM planner as a bounded alternative to deterministic planning, demonstrating additional utility only where it can be measured.

**Required behavior**

- `MVP-11.R01` — Support a server-side configurable LLM provider through a typed adapter, without requiring the browser or Source/Analyzer code to know provider specifics.
- `MVP-11.R02` — Translate registered tool capabilities into validated, restricted model-facing descriptions and validate every proposed operation before execution.
- `MVP-11.R03` — Enforce limits on tool calls, elapsed time, costs/resources, input size, and replan depth; reject arbitrary code execution or unapproved network access.
- `MVP-11.R04` — Handle malformed model output, timeouts, refusal, irrelevant actions, prompt-injection content in external data, and provider outages without silent success or unbounded retry loops.
- `MVP-11.R05` — Keep deterministic mode fully operational and provide an explicit fallback or failure path according to selected policy.
- `MVP-11.R06` — Compare LLM-assisted behavior with deterministic agent and fixed pipeline on identical scored fixtures: validity, unnecessary actions, completeness, evidence use, and termination.
- `MVP-11.R07` — Store meaningful plan choices, validated tool calls, input/artifact references, model/provider configuration where allowed, and limitations; do not treat generated explanations as proof.

**Non-goals.** An autonomous browser agent with unrestricted tools, model-only ecological verdicts, a general chat platform, or dependency on a particular commercial model.

**Acceptance evidence**

- `MVP-11.A01` — Integration tests with a deterministic model stub cover successful plans, invalid tool names, malformed parameters, loops, timeouts, and adversarial source text.
- `MVP-11.A02` — The LLM can revise a supported planning scenario without bypassing hard ecological/operational constraints or leaking configured secrets.
- `MVP-11.A03` — Comparative evaluation reports both successes and regressions relative to deterministic mode; no unsupported claim that an LLM is categorically better.

**Implementation questions for the later sub-spec.** Provider policy, structured output contract, budgeting, evaluation corpus, data transmission/privacy and retention controls, and whether the LLM has value at the chosen stage.

### MVP-12 — Conservation and scientific comparison workspace

**Objective.** Give ecologists and conservation practitioners a focused way to explore ecological evidence and compare territory/site scenarios using the existing engine, without requiring new field-data collection yet.

**Required behavior**

- `MVP-12.R01` — Provide a research/conservation-oriented workflow within the same web application, distinct from beekeeper relocation planning but sharing maps, sources, and analysis capabilities.
- `MVP-12.R02` — Compare selected territories or time intervals by available pollinator, floral-resource, apiary-pressure, land-use, and habitat evidence; absent data must remain explicit.
- `MVP-12.R03` — Allow inspection of analysis method, input coverage, source quality, time range, and uncertainty for each compared result.
- `MVP-12.R04` — Support hypotheses such as whether observed pollinator indicators differ across sites with varying *known* managed-apiary presence, while clearly distinguishing descriptive association from causal inference.
- `MVP-12.R05` — Support reproducible research exports of permitted data, methodology metadata, results, and limitations; do not include inaccessible private coordinates in exports.
- `MVP-12.R06` — Provide a confidentiality model for multi-user or institutional deployment before permitting access to nonpublic beekeeper or sensitive-species data. Define authorization and safe default sharing explicitly.
- `MVP-12.R07` — Allow conservation users to examine the likely effect of changing permissible apiary locations as **scenarios** without presenting those scenarios as regulatory decisions.

**Non-goals.** Automatic causal scientific conclusions, population viability guarantees, authoritative permits, or a full laboratory information management system. User role names and authentication architecture are specified when real sharing is introduced.

**Acceptance evidence**

- `MVP-12.A01` — Users compare two source-backed areas/time windows and inspect evidence coverage, method, and reasons that an interpretation is limited.
- `MVP-12.A02` — An observational association is never labeled a demonstrated causal effect; an absent pollinator record does not imply species absence without sampling-effort evidence.
- `MVP-12.A03` — Authorized export includes permitted provenance/method metadata; access-control tests prove that sensitive geometry is not exposed to an unauthorized user.
- `MVP-12.A04` — The beekeeper planning UI and ecosystem screening from prior stages continue to work.

**Implementation questions for the later sub-spec.** Scientific datasets and methods, access/security design, permitted export formats, researcher feedback, and indicators that can be defended by available evidence.

### MVP-13 — Field observations and longitudinal ecological monitoring

**Objective.** Extend MelliAtlas into a useful research information system for collecting, validating, retaining, and comparing ecological observations over successive seasons and years.

**Required behavior**

- `MVP-13.R01` — Allow authorized project participants to create and manage research studies, sampling locations, survey sessions, and observation records with explicit ownership and access rights.
- `MVP-13.R02` — Capture observation location and precision, local/UTC time context, observed organism or ecological indicator, taxonomic identification and confidence, sampling protocol, recorder, and supporting evidence where applicable.
- `MVP-13.R03` — Record **sampling effort and method** so missing sightings are not confused with surveyed absence or non-detection; preserve unknown or incomplete measurements without fabrication.
- `MVP-13.R04` — Support quality review, correction history, versioned observations, duplicate detection, and provenance of imported research datasets. Never silently rewrite original field evidence.
- `MVP-13.R05` — Compare observations across dates, years, survey methods, and locations with explicit normalization/limitations; do not equate unequal survey effort to population change.
- `MVP-13.R06` — Provide map/time-series views and controlled export/import of permitted records with enough method metadata for later reproduction. Consider established biodiversity exchange formats when appropriate and verified.
- `MVP-13.R07` — Enforce field-data confidentiality, including rare-species localities, private apiary coordinates, and restricted research records. Generalized public views must not reveal hidden precise locations through metadata or exports.
- `MVP-13.R08` — Support interrupted field-entry recovery and eventual offline/mobile fieldwork **only if selected in the later sub-spec**; do not silently add a separate native client or broad offline synchronization platform.
- `MVP-13.R09` — Allow research datasets to inform ecological analysis only according to their coverage, method, review status, and sharing rights.

**Non-goals.** Automatic confirmation of species identification, one-size-fits-all biodiversity scores, guaranteed longitudinal causal inference, a compulsory mobile app, or compulsory publication of contributed data.

**Acceptance evidence**

- `MVP-13.A01` — An authorized researcher records two survey sessions in distinct seasons, reviews a correction without losing history, and compares them with sampling effort and limitations visible.
- `MVP-13.A02` — Missing detection, confirmed zero under a declared protocol, missing effort, uncertain taxonomy, and duplicate import are represented distinctly and independently tested.
- `MVP-13.A03` — Authorized import/export round-trips preserve required temporal/spatial/method metadata; unauthorized access and coordinate reconstruction attempts are blocked within the specified threat model.
- `MVP-13.A04` — The same data can be used by a conservation analysis while the beekeeper's workflow remains functional and private data stays appropriately protected.

**Implementation questions for the later sub-spec.** Which scientists/organizations will pilot it, minimal sampling protocols, taxonomic reference sources, review roles, consent and contributor rights, retention, offline sync needs, and standards-aligned exchange formats.

---

## 9. Cross-stage quality and validation

### 9.1. Product behavior and negative cases

Every active sub-spec must identify positive, negative, boundary, and recovery scenarios grounded in that stage's responsibilities. At minimum, test how its behavior responds to empty sources, conflicting evidence, out-of-period records, invalid/ambiguous geometry, missing permission or coverage, failed providers, and lack of feasible planning alternatives when relevant. A plan's validity must not depend on hidden UI assumptions or demo-specific constants.

### 9.2. Architecture and change safety

- Test public module interfaces and forbid imports of other modules' internals according to the active architecture.
- Reject dependency cycles and accidental coupling between domain decisions and infrastructure details.
- Check that backend and web use compatible public API contracts and handle invalid responses.
- Maintain performance and resource bounds that are justified by the stage's deployment conditions; prefer measured budgets over invented global targets.
- Ensure all shared rules have a clear owner. Small temporary duplication is acceptable when eliminating it would demand broad unrelated context or unnecessary abstraction; later focused refactoring should remove demonstrated maintenance problems.
- Avoid speculative abstractions introduced solely to serve future stages; evolve the vertical slice using versioned contracts and migrations when needed.

### 9.3. Scientific verification

The presence of code and automated tests does not establish the scientific validity of an environmental impact estimate or phenological model. Before using such outputs to support real decisions, the responsible sub-spec must identify suitable published methods, datasets, validation design, limitations, and circumstances where the model is inapplicable. For nontrivial features, survey existing open-source and scientific approaches before inventing a new one; investigate relevant implementations in other languages when useful.

### 9.4. Legal and ethical handling

Rules differ between jurisdictions, protected-area categories, and times. No stage may assume a legal ban merely from distance to an area labeled protected; check the applicable designation and restriction. Likewise, no stage may claim a surrounding habitat is harmless because a government registry lacks an entry. Restrict access to precise apiary and sensitive-species coordinates, credentials, and nonpublic records according to the deployment's actual threat model. Do not expose personally identifiable or confidential data through debugging or monitoring output.

### 9.5. User interface quality

The primary web experience must remain comprehensible on desktop and mobile browsers, accessible to basic keyboard interactions, and explicit about loading, empty, error, and partial-result states. Maps must provide textual alternatives for critical constraints or conclusions. Explanations and provenance should be accessible without requiring a developer to inspect logs. Research features must not complicate the beekeeper's initial planning journey unnecessarily.

### 9.6. Test families expected to grow with stages

| Test family | Initial focus | Later expansion |
| --- | --- | --- |
| Unit / pure function | Synthetic forage windows, basic geometry rules, planning rules | Phenology, scoring, optimization, statistical methods |
| Source/Analyzer contracts | Typed synthetic inputs/outputs and error behavior | Real-provider normalization, coverage, licensing metadata |
| Agent behavior | Evidence-triggered replanning and safe termination | Tool discovery, conflict resolution, deterministic/LLM comparisons |
| Database integration | Save/reopen planned route and geometries | Caching, versioning, restart, research datasets |
| Architecture | Contract boundaries and dependency direction | Worker isolation, access-control boundaries, data privacy |
| API | Valid/invalid requests and results | Idempotency, auth, pagination, secure export |
| Browser E2E | Run/reopen the complete first plan | Multi-territory comparisons, alternative routes, researcher workflows |
| Scientific validation | Synthetic oracle correctness and disclosure | Independent observational/experimental validation where applicable |

## 10. Future stage preparation and SDD lifecycle

### 10.1. Stage activation

An umbrella stage is **not** an active sub-spec. The developer chooses the next workstream and stage. Only then:

1. Read the approved umbrella and relevant active-stage context; read dependent modules' `contract.md` and public APIs without loading unrelated source trees.
2. Draft an active sub-spec under `docs/specs/active/` with testable requirement IDs, user journeys, input/output contracts, failure cases, security/privacy implications, migration constraints, and independent acceptance criteria.
3. Create **one separate advisory implementation plan** named `<spec_stem>_implementation_plan.md` next to that active sub-spec. It must contain proposed additions/edits/deletions by file, module ownership/contracts, ordered implementation tasks, TDD-first tests, architecture tests, test fixtures, commands, assumptions, recovery strategy, and representative pseudocode where genuinely useful.
4. Research existing open-source or established methods for each nontrivial new capability, recording the findings and trade-offs in the active plan.
5. Obtain explicit developer acceptance of the active requirement scope and implementation authorization before changing product code.

**Do not pre-generate** sub-specs or implementation plans for unselected stages. Plans never authorize implementation by themselves.

### 10.2. Checkpoint and completion

After a stage is selected, `docs/specs/STATE.json` tracks the chosen workstream, active sub-spec path, stage ID, and phase, validated against `docs/specs/state.schema.json`. The developer controls checkpoint progression; passing checks, creating a PATCH, or committing code does not automatically mark a stage complete.

After implementation, verification, and explicit developer approval, archive the sub-spec and its linked plan together under `docs/specs/archive/`, update the index and cross-references, and select the next stage separately. Do not load archived sub-specs during normal development or authoring unless the developer explicitly requests historical investigation. Optional material implementation-plan history uses `<spec_stem>_implementation_plan_history.md`.

### 10.3. Feature-to-code traceability

Maintain stable feature IDs and short descriptions in `docs/FEATURES.md`. Store stage IDs, selected sub-spec paths, verified public owners, and test paths in `docs/specs/feature-cross-ref.yaml`, validated by its JSON Schema. Do not invent code paths that have not been created, and do not claim a future plan is implemented merely because its feature has an identifier.

## 11. Open decisions to resolve at stage activation

These decisions should not block agreement on the product mission or the umbrella-stage sequence, but they must not be silently filled in by an implementation agent.

1. **First-run workflow:** exact API operations, database schema, demonstration fixtures, browser views, and what counts as an agent's observable replan (`MVP-01`).
2. **Ecological demo policy:** which fictional rule defines the excluded demo site and how precautionary and missing information differ (`MVP-01`).
3. **Forage model:** appropriate flora/crop categories, flowering evidence, comparison method, and scientific boundaries (`MVP-02`).
4. **Execution model:** minimal agent/Engine interfaces now versus durable-worker design later (`MVP-01`, `MVP-04`).
5. **Geography:** territory/coordinate dataset choice, permitted use, and versioning for Russia and Belarus (`MVP-05`).
6. **Real sources:** current legal access, completeness, scientific relevance, and operational cost (`MVP-06` onward).
7. **Ecology:** applicable protected-area restrictions, evidence standards, and how to represent possible competition among pollinators without unsupported causal claims (`MVP-08`).
8. **Private data:** roles, secure storage, generalized views, and export rules before any multi-user/public deployment (`MVP-09`, `MVP-12`, `MVP-13`).
9. **Optimization:** how to communicate constraint trade-offs without asserting a guaranteed best harvest or a validated single ecological score (`MVP-10`).
10. **Research engagement:** confirmation of actual researcher/conservation workflows and field methods before detailed observation-system design (`MVP-12`, `MVP-13`).

## 12. Product acceptance milestones

**First MVP (`MVP-01`)** is complete only when the full browser workflow, synthetic ecological constraint, explainable adaptive alternative, persistence, and automated tests pass. Everything is explicitly labeled as demo data.

**Operationally useful planning (`MVP-02`–`MVP-10`)** grows through better forage evidence, dependable jobs, multiple territories, permitted real sources, weather, conservation analysis, bee-related hazards, and constrained route alternatives. Each stage must keep the existing planning workflow intact; no single stage implies scientifically validated real-world recommendations beyond its evidence.

**Optional agent intelligence (`MVP-11`)** may improve task selection but cannot substitute for validated data or safeguards.

**Research and conservation maturity (`MVP-12`–`MVP-13`)** adds comparative analysis, controlled data sharing, field observations, and multi-year monitoring. Its scientific credibility depends on documented methods and evidence, not just software completeness.

**Document status:** Draft. Approval of this umbrella is separate from selecting `MVP-01` and authorizing its implementation. No active sub-spec, implementation plan, checkpoint, or product implementation is created by this document.
