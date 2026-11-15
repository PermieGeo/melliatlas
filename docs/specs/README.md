# MelliAtlas Specification Index

## Product-level specification

- [Umbrella Specification](umbrella_spec_melliatlas.md) — the product mission, cross-cutting requirements, stage sequence, and acceptance outcomes. **Working roadmap; the selected `MVP-01` Web W01 slice is authorized; backend remains approved but paused. Other workstreams are not authorized.**

## Active Web workstream

- **Requirements approval:** APPROVED — W01 Web sub-spec; backend sub-spec remains approved.
- **Implementation authorization:** AUTHORIZED — selected W01 Web slice; backend implementation is paused while UI begins.
- **Acceptance:** PENDING — Web, backend and umbrella `MVP-01` remain unaccepted.

Implementation is in progress. External source, license, infrastructure, and runtime-dependency decisions remain task-specific gates. The first step supplies FastAPI health/OpenAPI and architecture checks. Territory contract APIs, fail-closed offline reference validation, and HTTP reads are implemented as part of step 2; independently approved complete RU/BY catalogs and PostGIS import are pending; no full backend acceptance criterion or browser MVP is complete. The React/Web workstream is now selected for the first runnable synthetic-browser slice; backend work is preserved, not marked accepted. The V04-04 offline Saturn treatment parser and conservative screening are implemented. V04-05 connects fictional treatment notices to a provisional investigation plan and typed HTTP findings; V04-06 adds a joint synthetic scenario requiring both ecological and treatment findings before the final selection. Live provider approval, weather effects and the full typed execution graph remain pending.

- [MVP-01 Backend sub-specification](active/subspecs/subspec-01-backend-planning.md) — active normative requirements for RU/BY geography, fixture sources, typed analysis, the deterministic agent, PostGIS, and HTTP.
- [MVP-01 Backend implementation plan](active/subspecs/subspec-01-backend-planning_implementation_plan.md) — active implementation guidance with current code inventory, a bounded next task, vertical-slice backlog, architecture policy, and requirement-linked acceptance tests.
- [`STATE.json`](STATE.json) — selected `mvp-01-web` workstream in `READY_FOR_IMPLEMENTATION`; backend workstream is paused, not accepted.

## Selected Web implementation

- [MVP-01 Web sub-spec](active/subspecs/subspec-01-web-mvp.md) — source-neutral treatment and ecology study UI, explicit synthetic data and one client without Admin.
- [W01 implementation plan](active/subspecs/subspec-01-web-mvp_implementation_plan.md) — browser contracts, current boundaries, test inventory and follow-on work.

W01 introduces a runnable UI and test sources. It remains **partial** until installed frontend dependencies, strict checks and browser interaction tests pass in a supported local environment; its implementation does not authorize live collection or certify safety. The backend workstream is paused but retains its existing active specs and planned technical backlog.

## How specification work progresses

The active sub-spec states observable requirements and acceptance criteria; its separate implementation plan describes the next bounded task, relevant contracts, and tests. Requirements approval, authorization to implement, and acceptance of completed work are separate decisions. Once the developer accepts a completed workstream, its sub-spec and plan move together to the archive and the checkpoint is updated.

The [feature cross-reference](feature-cross-ref.yaml) tracks implementation maturity separately from those decisions: `planned` has no registered implementation owner, `partial` has code and tests without completed feature acceptance, and `verified` denotes a feature with a documented developer acceptance. Acceptance records reside in [`STATE.json`](STATE.json). No feature is marked accepted until those records and criteria are approved.

`archive/` currently has no completed stage documents.

## How specification work progresses

The active sub-spec states observable requirements and acceptance criteria; its separate implementation plan describes the next bounded task, relevant contracts, and tests. Requirements approval, authorization to implement, and acceptance of completed work are separate decisions. Once the developer accepts a completed workstream, its sub-spec and plan move together to the archive and the checkpoint is updated.

The [feature cross-reference](feature-cross-ref.yaml) tracks implementation maturity separately from those decisions: `planned` has no registered implementation owner, `partial` has code and tests without completed feature acceptance, and `verified` denotes a feature with a documented developer acceptance. Acceptance records reside in [`STATE.json`](STATE.json) and identify the criteria, evidence, and approval reference. The current `featureAcceptances` list is empty, so no feature is marked accepted. The implemented health endpoint and territory validation do not imply that investigation UI or map rendering are available.

The [feature catalog](../FEATURES.md) lists stable IDs and descriptions; the [cross-reference](feature-cross-ref.yaml) records their specification, implementation, and test links. The [checkpoint schema](state.schema.json) defines the structure of `STATE.json`.
