# MelliAtlas Specification Index

## Product-level specification

- [Umbrella Specification](umbrella_spec_melliatlas.md) — the product mission, cross-cutting requirements, stage sequence, and acceptance outcomes. **Working roadmap; only the active `MVP-01` backend scope is approved for implementation. Other workstreams are not authorized.**

## Active workstream

- **Requirements approval:** APPROVED — `MVP-01` backend sub-spec only.
- **Implementation authorization:** AUTHORIZED — backend implementation; external approval gates remain task-specific.
- **Acceptance:** PENDING — backend and umbrella `MVP-01` remain unaccepted.

Implementation is in progress. External source, license, infrastructure, and runtime-dependency decisions remain task-specific gates. The first step supplies FastAPI health/OpenAPI and architecture checks. Territory contract APIs, fail-closed offline reference validation, and HTTP reads are implemented as part of step 2; independently approved complete RU/BY catalogs and PostGIS import are pending; no full backend acceptance criterion or browser MVP is complete. The separate React/Web sub-spec and plan will be prepared after backend contract verification.

- [MVP-01 Backend sub-specification](active/subspecs/subspec-01-backend-planning.md) — active normative requirements for RU/BY geography, fixture sources, typed analysis, the deterministic agent, PostGIS, and HTTP.
- [MVP-01 Backend implementation plan](active/subspecs/subspec-01-backend-planning_implementation_plan.md) — active implementation guidance with current code inventory, a bounded next task, vertical-slice backlog, architecture policy, and requirement-linked acceptance tests.
- [`STATE.json`](STATE.json) — selected `mvp-01-backend` workstream in `READY_FOR_IMPLEMENTATION`; this is not a completed-stage or accepted-test claim.

`archive/` currently has no completed stage documents.

## How specification work progresses

The active sub-spec states observable requirements and acceptance criteria; its separate implementation plan describes the next bounded task, relevant contracts, and tests. Requirements approval, authorization to implement, and acceptance of completed work are separate decisions. Once the developer accepts a completed workstream, its sub-spec and plan move together to the archive and the checkpoint is updated.

The [feature cross-reference](feature-cross-ref.yaml) tracks implementation maturity separately from those decisions: `planned` has no registered implementation owner, `partial` has code and tests without completed feature acceptance, and `verified` denotes a feature with a documented developer acceptance. Acceptance records reside in [`STATE.json`](STATE.json) and identify the criteria, evidence, and approval reference. The current `featureAcceptances` list is empty, so no feature is marked accepted. The implemented health endpoint and territory validation do not imply that investigation UI or map rendering are available.

The [feature catalog](../FEATURES.md) lists stable IDs and descriptions; the [cross-reference](feature-cross-ref.yaml) records their specification, implementation, and test links. The [checkpoint schema](state.schema.json) defines the structure of `STATE.json`.

