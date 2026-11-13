# Specification AGENTS.md

Extends `../../AGENTS.md`. Keep normative requirements separate from advisory implementation plans.

## Umbrella & Active Scope
- **ALWAYS** create the umbrella specification upfront. Describe every planned stage with its goal, scope, dependencies, and acceptance outcomes; defer file-level design to the selected sub-spec.
- **ALWAYS** select a stage before preparing its implementation. Create its focused sub-spec and a separate linked implementation plan in `docs/specs/active/` before coding.
- **NEVER** create an implementation plan for a sub-spec that is not active. **NEVER** pre-generate plans for future stages.
- **ALWAYS** keep future stages in the umbrella until selected; avoid loading unrelated workstreams into the current context.

## Requirements
- **ALWAYS** write specs and plans in English; use stable, distinct stage, requirement, and test IDs.
- **ALWAYS** state scope, non-goals, actors, observable behavior, failure and boundary cases, and independently verifiable acceptance criteria.
- **ALWAYS** distinguish approved requirements, drafts, planned work, and verified implementation.
- **NEVER** smuggle implementation decisions into normative requirements unless they are approved constraints.
- **ALWAYS** obtain developer approval for material requirements and changes before implementing them.

## Implementation Plans & TDD
- **ALWAYS** name each active sub-spec's implementation plan `<spec_stem>_implementation_plan.md`, using the exact sub-spec filename stem; keep it beside the sub-spec and archive both together.
- **MAY** record material specification or plan changes in `<spec_stem>_implementation_plan_history.md`; the current sub-spec and plan remain authoritative.
- **ALWAYS** link each active sub-spec to its own advisory plan and keep both aligned when requirements change.
- **ALWAYS** list proposed additions, edits, and removals by file; distinguish verified paths from proposed ones. Describe ownership, public contracts, dependencies, ordered steps, migrations, and recovery where relevant.
- **ALWAYS** plan TDD: write executable tests that initially fail because the specified behavior is missing, implement the behavior, then refactor with those tests passing. **NEVER** use dummy failing assertions, skipped tests, or tests that merely mirror the implementation.
- **ALWAYS** enumerate functional tests with requirement IDs, inputs/fixtures, expected observable outcomes, failure and boundary cases, and how each test is run and verified.
- **ALWAYS** include architecture tests for applicable invariants: public API boundaries, forbidden imports, dependency cycles, and other constraints established by approved specifications.
- **ALWAYS** identify checks and commands supported by the verified repository; label unavailable tooling or proposed checks explicitly.
- **TRY TO** make plans implementation-ready with concise file-level steps and pseudocode for non-obvious flows; **NEVER** overload them with speculative detail.
- **NEVER** invent existing code, executed checks, validated APIs, or accepted stages.

## STATE.json & Lifecycle
- **ALWAYS** maintain `docs/specs/STATE.json` as the developer-controlled checkpoint once the first workstream is selected. Track the selected workstream, active sub-spec path, stage ID, and phase; validate it against `docs/specs/state.schema.json` and keep it consistent with the umbrella, plan, and spec index.
- **ALWAYS** validate checkpoint consistency and links with repository tooling when available. **NEVER** copy legacy checkpoint values into a fresh repository or assume an uninitialized checkpoint exists.
- **NEVER** advance the selected workstream, stage, phase, or acceptance status without an explicit developer decision; passing tests, creating a ZIP, or committing code is not acceptance.
- **ALWAYS** move the completed sub-spec and its linked plan together from `active/` to `archive/` after implementation and explicit developer acceptance; update the index, umbrella, references, and checkpoint consistently.
- **NEVER** read `docs/specs/archive/` during ordinary implementation or spec authoring; consult it only when the user explicitly requests historical investigation.
