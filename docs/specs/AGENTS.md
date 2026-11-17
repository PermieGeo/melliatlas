# Specification AGENTS.md

Extends `../../AGENTS.md`. Keep normative requirements separate from advisory implementation plans.

## Scope and approval
- Keep the umbrella specification as the product roadmap. Describe future stages at the fidelity supported by current knowledge; only the selected active sub-spec is implementation-ready.
- Select and approve a workstream before implementation. Keep its sub-spec and linked plan in `docs/specs/active/`; do not create plans for unselected workstreams.
- Write specs and plans in English with stable requirement and acceptance IDs, explicit scope, non-goals, observable behavior, negative cases, and testable outcomes.
- Distinguish **requirements approval**, **implementation authorization**, and **acceptance**. A working roadmap does not authorize every future stage. A passing test, commit, or ZIP does not constitute acceptance.
- Require explicit developer approval for material scope/requirement changes or relaxation of an approved constraint. Record external data, license, infrastructure, and runtime-dependency approvals against the particular tasks they block.

## Plans and implementation
- Retain the active workstream sub-spec and its `<spec_stem>_implementation_plan.md` as stable normative and navigation entrypoints. Archive a completed workstream only after explicit developer acceptance.
- For features spanning backend and frontend, keep separately scoped sub-specs and plans. Verify the backend contract needed by a frontend slice before implementing the dependent client behavior; avoid delaying all browser validation until the entire backend is complete.
- Keep workstream implementation plans concise: current integration boundaries, authoritative links, the selected task pointer, and the next bounded dependencies. Do not append completed task writeups or predefine every future class or file.
- Before implementing each selected bounded task, include a `Public contracts and integration design` section in its task plan (or the linked workstream plan for legacy tasks). For every new or materially changed public boundary, review exact typed declarations and import paths, inputs/outputs, errors, module interactions, dependency direction, compatibility constraints, and executable contract-first tests **before** generating implementation code. Require developer review for architecture-significant choices, not for routine private details.
- Design public contracts only for the selected task; do not predesign future APIs or dictate private algorithms. Inspect and reuse implemented interfaces rather than redefining them in a second document.
- After implementation, source declarations, module `contract.md`, generated OpenAPI and executable contract tests are authoritative. Replace redundant proposed declarations in the current task plan with links to those interfaces and their verification evidence.
- The sub-spec owns normative requirements and acceptance criteria; the plan owns implementation decisions and requirement-linked test inventory. Use requirement IDs rather than independently restating domain obligations, and route any new or changed obligation through the sub-spec approval process first.
- Prefer an existing maintained library when it demonstrably reduces cost or risk; research alternatives for consequential dependency or algorithm choices, not routine code.
- Track proposed additions, edits and removals; distinguish existing paths from future paths. Keep plans advisory when implementation details can be chosen locally without changing requirements.
- Use TDD for behavior: tests fail for missing functionality, then pass after implementation. Never use dummy failures or skipped assertions to simulate TDD.
- Keep requirement-linked positive, negative, boundary, architecture and integration checks in a test inventory; execute only the relevant subset for each current task, then run required project checks.

## Task-scoped context (selected Web pilot)
- One bounded task is represented by `docs/specs/active/tasks/<task-id>/task.md` and an adjacent `task-plan.md`. The task owns task-specific behavior, non-goals, requirement references and acceptance oracles; the plan owns implementation strategy, affected modules, public contract design, tests and verification gates. Keep stable cross-task requirements in the workstream sub-spec; do not copy them into each task.
- `STATE.json.selectedTaskPath`, when present, is the single pointer to the selected task for context assembly, not evidence of implementation authorization or feature acceptance. Load the umbrella, active workstream sub-spec, selected task and its task plan, plus only applicable AGENTS/READMEs, module contracts/public APIs, and code/tests needed for that task. Never load unrelated task files merely to discover dependencies; use explicit contract links instead.
- Create a new task pair only for a cohesive, independently testable outcome, not for a typo fix or every PATCH. Do not make unselected task plans in advance. Updating the task pointer requires developer authorization and a validated file pair; do not modify acceptance records or workstream phase as a side effect.
- A task may be selected for design without implementation approval. State its authorization gate explicitly. New or revised normative requirements must be approved before code changes, and selected task plans must never override the workstream specification.

## State and consistency
- Treat `docs/specs/STATE.json` as the developer-controlled workstream and feature-acceptance checkpoint. Validate it and `docs/specs/feature-cross-ref.yaml` against their schemas and cross-document consistency checks, including the active sub-spec, plan, and index.
- Do not advance a workstream, phase or acceptance status without a developer decision. `READY_FOR_IMPLEMENTATION` means work is authorized, not that it has passed acceptance.
- Set `implementation_status: verified` only with a matching `STATE.json.featureAcceptances` record identifying acceptance criteria, verifiable evidence paths, and an explicit developer approval reference. Code and passing tests alone do not establish feature acceptance; never invent approval.
- Keep feature IDs and links in `docs/FEATURES.md` and `docs/specs/feature-cross-ref.yaml` accurate for actually implemented behavior.
- After each coherent task, review changes for scope creep, contract drift, unnecessary dependencies, missing tests and false implementation claims.

## Active documents and historical continuity
- MUST keep active sub-specifications, implementation plans, the specification index, and related READMEs as current-state documents. NEVER append chronological PATCH notes, completed-task narratives, superseded proposals, or implementation diaries to them. Replace obsolete plan material with the current next task, concise dependency references, and links to authoritative APIs, contracts, and tests.
- After each bounded task, remove or replace stale implementation-plan text and reconcile changed requirements, public boundaries, documented limitations, feature status, and tests. Preserve approved normative requirements and acceptance criteria until explicitly revised; documentation cleanup never grants approval or acceptance.
- When a past decision is worth retaining, record a brief dated entry in a single optional engineering history under `docs/specs/archive/`: task/requirement reference, decision and rationale, affected public contract, and links to the authoritative current sources. Do not copy full diffs, old plans, conversation content, or generated-PATCH handoff records; use Git for exact history.
- Treat `docs/specs/archive/` as non-normative historical material. NEVER read it in ordinary task implementation, dependency discovery, or context assembly; consult it only for an explicitly requested historical or deep architecture review. Archived records never override active specifications and public contracts.


