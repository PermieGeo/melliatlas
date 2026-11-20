# MelliAtlas Specification Index

## Authority and checkpoint

- [Umbrella product specification](umbrella_spec_melliatlas.md) — roadmap and invariant semantics.
- [`STATE.json`](STATE.json) — the selected workstream/task and developer acceptance record, not execution authorization by itself.
- [Feature cross-reference](feature-cross-ref.yaml) and [feature catalog](../FEATURES.md) — ownership and partial versus accepted capability tracking.
- [Development workflow](../DEVELOPMENT_WORKFLOW.md) — four-part snapshots, one branch per sub-spec and the final-only verification/`apatch` gate.

**Original requirements approval:** APPROVED for W01 Web and MVP-01 backend. **Implementation authorization:** original W01 browser slice only; backend workstream is PAUSED. **Feature acceptance:** PENDING (`featureAcceptances` is empty). New private-place API behavior and external provider permissions require explicit authorization.

## Active workstreams

- [Web MVP sub-spec](active/web-mvp/subspec.md) — normative, selected `mvp-01-web` workstream.
- [Web integration plan](active/web-mvp/impl_plan.md) — cross-task dependencies and existing public contracts.
- [Web task decomposition](active/web-mvp/subspec.md#task-decomposition) — ten flat task/implementation-plan pairs, each with one change partition.
- [Backend sub-spec](active/subspecs/subspec-01-backend-planning.md) and [backend plan](active/subspecs/subspec-01-backend-planning_implementation_plan.md) — PAUSED legacy layout, retained until separately selected. Its original normative scope is not automatically widened by Web work.

## Selected task

- [`WEB-PLACE-01` — unsaved area draft](active/web-mvp/task_03_area_draft.md).
- [Paired task implementation plan](active/web-mvp/task_impl_plan_03_area_draft.md).

This preserves the prior stable task ID while separating its frontend draft scope from the still-blocked [backend saved-place API](active/web-mvp/task_07_saved_places_service.md) and later [saved-place UI](active/web-mvp/task_08_saved_places_client.md). The `selectedTaskPath` pointer is not evidence of accepted task completion. The proposed browser and Python endpoint [E2E preparation task](active/web-mvp/task_09_manual_e2e.md) is **not implemented** by the documentation change; all tests are deferred until the end-of-sub-spec [review and execution task](active/web-mvp/task_10_test_suite_review.md).

## Current process boundary

The `frontend`, `backend`, `tests` and `docs` snapshots are independently addressable. A task and its PATCH may change only its named partition. All tasks in the selected sub-spec share one unfinished feature branch; no tests run or task merges occur before the final test phase. The current repository still has a monolithic snapshot generator and legacy test-path assumptions; snapshot-tooling and test-runner adaptations are separate follow-up tasks. Do not claim a four-part generator, new endpoint E2E runner or unchecked Git commits exist already.

The [checkpoint schema](state.schema.json) accepts the current Web flat structure and the untouched paused backend legacy path. Material changes to acceptance, API privacy, requirements, source rights or `apatch` gates need developer decisions. Historical notes in `archive/` are not implementation authority.
