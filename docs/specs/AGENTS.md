# Specification AGENTS.md

Extends `../../AGENTS.md`. Keep normative requirements separate from advisory implementation plans.

## Scope and approval
- Keep the umbrella specification as the product roadmap. Describe future stages at the fidelity supported by current knowledge; only the selected active sub-spec is implementation-ready.
- Select and approve a workstream before implementation. Keep its sub-spec and linked plan in `docs/specs/active/`; do not create plans for unselected workstreams.
- Write specs and plans in English with stable requirement and acceptance IDs, explicit scope, non-goals, observable behavior, negative cases, and testable outcomes.
- Distinguish **requirements approval**, **implementation authorization**, and **acceptance**. A working roadmap does not authorize every future stage. A passing test, commit, or ZIP does not constitute acceptance.
- Require explicit developer approval for material scope/requirement changes or relaxation of an approved constraint. Record external data, license, infrastructure, and runtime-dependency approvals against the particular tasks they block.

## Plans and implementation
- Name a linked plan `<spec_stem>_implementation_plan.md` beside the active sub-spec. Archive both together only after completed work and explicit developer acceptance.
- For features spanning backend and frontend, keep separately scoped sub-specs and plans. Verify the backend contract needed by a frontend slice before implementing the dependent client behavior; avoid delaying all browser validation until the entire backend is complete.
- Keep the implementation plan focused on architecture direction, existing public contracts, a test inventory, the current bounded task, and a concise future backlog. Do not predefine every future class or file.
- For a new public boundary needed by the current task, specify its typed inputs/outputs, invariants, errors and import path; add executable contract tests and a meaningful contract draft where cross-module communication warrants one.
- Prefer an existing maintained library when it demonstrably reduces cost or risk; research alternatives for consequential dependency or algorithm choices, not routine code.
- Track proposed additions, edits and removals; distinguish existing paths from future paths. Keep plans advisory when implementation details can be chosen locally without changing requirements.
- Use TDD for behavior: tests fail for missing functionality, then pass after implementation. Never use dummy failures or skipped assertions to simulate TDD.
- Keep requirement-linked positive, negative, boundary, architecture and integration checks in a test inventory; execute only the relevant subset for each current task, then run required project checks.

## State and consistency
- Maintain `docs/specs/STATE.json` as a developer-controlled workstream checkpoint; validate its schema, selected workstream, paths and phase against the active sub-spec, plan and index.
- Do not advance a workstream, phase or acceptance status without a developer decision. `READY_FOR_IMPLEMENTATION` means work is authorized, not that it has passed acceptance.
- Keep feature IDs and links in `docs/FEATURES.md` and `docs/specs/feature-cross-ref.yaml` accurate for actually implemented behavior.
- After each coherent task, review changes for scope creep, contract drift, unnecessary dependencies, missing tests and false implementation claims.
- Do not read `docs/specs/archive/` during ordinary implementation; consult it for an explicitly requested historical review only.
