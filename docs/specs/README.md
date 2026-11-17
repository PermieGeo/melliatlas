# MelliAtlas Specification Index

## Authority and checkpoint

- [Umbrella specification](umbrella_spec_melliatlas.md) — product roadmap and cross-cutting invariants.
- [`STATE.json`](STATE.json) — selected `mvp-01-web` workstream and its task context; `READY_FOR_IMPLEMENTATION` applies to the previously approved W01 scope, not automatically to any newly proposed task.
- [Feature cross-reference](feature-cross-ref.yaml) and [feature catalog](../FEATURES.md) — implementation maturity and ownership, separate from acceptance.

**Requirements approval:** APPROVED — original W01 Web and backend sub-specs.

**Implementation authorization:** AUTHORIZED — original W01 Web slice; backend workstream paused.

**Acceptance:** PENDING — `featureAcceptances` is empty. New tasks and external provider/runtime permissions need their own review. Other task-specific requirements and external provider/runtime permissions need their own review.

## Active workstreams

- [Web sub-specification](active/subspecs/subspec-01-web-mvp.md) — normative requirements and acceptance criteria of the current W01 browser slice.
- [Web integration plan](active/subspecs/subspec-01-web-mvp_implementation_plan.md) — concise current boundaries and the selected redesign task.
- [Backend sub-specification](active/subspecs/subspec-01-backend-planning.md) and [backend implementation plan](active/subspecs/subspec-01-backend-planning_implementation_plan.md) — approved but paused; do not advance its checkpoint without authorization.

## Selected task context: saved place and editable bbox

- [Task requirements](active/tasks/web-saved-place-bbox/task.md) — user workflow, scope and observable oracles, currently design-only.
- [Task plan](active/tasks/web-saved-place-bbox/task-plan.md) — public-boundary proposal, persistence/privacy gates and tests before implementation.

The selected task path in `STATE.json` is a **context selector**, not a claim that the new feature has been built or accepted. Ordinary task work must not read other task pairs or `archive/` without a concrete dependency or an explicitly requested historical review. Stable shared behavior stays in the workstream sub-spec and source contracts.

## Completion and history

Implementation does not imply acceptance. Evidence and explicit approval are required before updating a feature to `verified`. The [checkpoint schema](state.schema.json) defines checkpoint structure; [cross-reference schema](feature-cross-ref.schema.json) defines feature entries. Significant superseded decisions may be summarized under the non-normative `archive/`; Git remains the complete implementation history. Archives are not normal working context.
