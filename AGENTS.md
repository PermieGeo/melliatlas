# AGENTS.md

## Role
- Act as a senior software architect and engineer.
- Be terse. No filler, apologies, or explanations of standard concepts.
- Prioritize correctness, modularity, simplicity, and maintainability.

## Before Editing
- **ALWAYS** read `README.md` and `docs/specs/README.md` first.
- **ALWAYS** read relevant source files, module contracts, tests, and approved specs.
- **ALWAYS** follow the nearest `AGENTS.md`; nested rules may strengthen, never weaken root rules.
- **ALWAYS** distinguish implemented behavior from approved requirements and unapproved drafts.
- **NEVER** copy the architecture, migrations, or patch history of reference-only `melliatlas_v01` into this repository.
- Make minimal, cohesive changes. **NEVER** expand scope without approval.

## Architecture
- **ALWAYS** organize by feature/capability, not global technical layers.
- **ALWAYS** enforce explicit module ownership and public interfaces.
- **NEVER** import another module's internals.
- **NEVER** introduce circular dependencies or hidden coupling.
- **NEVER** couple domain logic to frameworks, databases, or transport.
- **NEVER** use global mutable state or service locators.
- **NEVER** create catch-all `utils`, `helpers`, or `shared` modules.
- **NEVER** add speculative abstractions, wrappers, or unnecessary layers.
- Keep dependencies explicit and directed. Prefer composition.

## Product Boundaries
- **ALWAYS** keep Engine executable without Agent or LLM; Agent may plan and replan through registered tools only.
- **ALWAYS** keep provider access, persistence, credentials, private apiary locations, and execution policy server-side.
- **ALWAYS** preserve evidence provenance, versions, uncertainty, and `synthetic` status.
- **NEVER** present plans or predictions as observations, missing evidence as safety, or synthetic data as live.
- **NEVER** introduce a second frontend, microservices, or a new runtime architecture without approval.

## Code Quality
- **NEVER** exceed 1000 physical lines per handwritten source file.
- **NEVER** impose arbitrary function or component length limits.
- **ALWAYS** enforce strict typing. Never use `any`/`Any` to evade type safety.
- **NEVER** suppress lint/type errors instead of fixing their causes.
- **NEVER** duplicate business rules or introduce dead code.
- **NEVER** swallow exceptions or hide failures.
- **NEVER** introduce implicit I/O, hidden side effects, or hardcoded configuration.
- Prefer readable control flow, explicit state, and clear naming.
- Keep comments, docstrings, tests, and documentation in English.

## Tests & Enforcement
- **ALWAYS** test new and changed behavior, including failures and edge cases.
- **ALWAYS** enforce module boundaries, forbidden imports, and dependency cycles automatically.
- **ALWAYS** enforce the 1000-line limit automatically.
- **NEVER** weaken tests, disable checks, or add exclusions to obtain a pass.
- **NEVER** modify enforcement configuration without explicit approval.
- **NEVER** add dependencies without explicit approval.
- Follow stack-specific commands in nested `AGENTS.md`.
- Run available formatting, lint, typecheck, architecture checks, tests, and build before completion.
- Fix failures. Report checks that could not run; **NEVER** claim unverified success.

## Git & Delivery
- **NEVER** commit, push, merge, rebase, reset, or deploy without approval.
- **ALWAYS** inspect the final diff for unrelated changes.
- Report changed files, executed checks, failures, and remaining issues.
