# MelliAtlas Specification Index

## Product-level specification

- [Umbrella Specification](umbrella_spec_melliatlas.md) — the product mission, cross-cutting requirements, stage sequence, and acceptance outcomes. **Working roadmap; only the active `MVP-01` backend scope is approved for implementation. Other workstreams are not authorized.**

## Active workstream

`MVP-01` backend requirements are approved and implementation is authorized; backend acceptance and overall `MVP-01` acceptance are pending. External source, license, infrastructure, and runtime-dependency decisions remain task-specific gates. Implementation is in progress. The first step supplies FastAPI health/OpenAPI and architecture checks. Territory contract APIs, fail-closed offline reference validation, and HTTP reads are implemented as part of step 2; independently approved complete RU/BY catalogs and PostGIS import are pending; no full backend acceptance criterion or browser MVP is complete. The separate React/Web sub-spec and plan will be prepared after backend contract verification.

- [MVP-01 Backend sub-specification](active/subspecs/subspec-01-backend-planning.md) — active normative requirements for RU/BY geography, fixture sources, typed analysis, the deterministic agent, PostGIS, and HTTP.
- [MVP-01 Backend implementation plan](active/subspecs/subspec-01-backend-planning_implementation_plan.md) — active implementation guidance with current code inventory, a bounded next task, vertical-slice backlog, architecture policy, and requirement-linked acceptance tests.
- [`STATE.json`](STATE.json) — selected `mvp-01-backend` workstream in `READY_FOR_IMPLEMENTATION`; this is not a completed-stage or accepted-test claim.

`archive/` has no completed stage documents. Do not read archived work during ordinary implementation.

For a selected stage:

1. Write an active normative sub-spec with stable requirement IDs, scope, boundary and failure cases, and independently verifiable outcomes.
2. Create its **separate linked implementation plan** with proposed file changes and test-first steps; do not prepare plans for unselected stages.
3. Record requirements approval and implementation authorization separately. Keep external approval gates attached to affected tasks; successful tests and commits do not constitute acceptance or advance the checkpoint.
4. After completed implementation and explicit acceptance, archive the sub-spec and linked plan together, then update references and the developer-controlled state.

The version 2 feature cross-reference records implementation maturity independently of workstream approval: `planned` means no feature implementation or test owner is registered, `partial` means actual code and tests exist but feature acceptance is not established, and `verified` requires completed feature-level verification. A health endpoint or a geometry validator alone must not be used as evidence that investigation UI or map rendering exists.

Feature identifiers and short descriptions belong in [`docs/FEATURES.md`](../FEATURES.md); specification, implementation, and test links belong in [`feature-cross-ref.yaml`](feature-cross-ref.yaml). Validate the checkpoint against [`state.schema.json`](state.schema.json) when initialized.

