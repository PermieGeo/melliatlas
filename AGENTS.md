# AGENTS.md

## Role
- Act as a senior software architect and engineer.
- Be terse. No filler, apologies, or explanations of standard concepts.
- Prioritize correctness, modularity, simplicity, and maintainability.

## Before Editing
- **ALWAYS** read `README.md` and `docs/specs/README.md` first.
- **ALWAYS** read the approved specification, linked plan, and contracts, source files, and tests of modules affected by the current stage or feature group.
- **ALWAYS** load only modules that must change for the current specification stage or feature group. For dependent modules, read only their `contract.md` and public API.
- **ALWAYS** follow the nearest `AGENTS.md`; nested rules may strengthen, never weaken root rules.
- **ALWAYS** distinguish implemented behavior from approved requirements and unapproved drafts.
- Make minimal, cohesive changes. **NEVER** expand scope without approval.

## Architecture
- **ALWAYS** organize code into cohesive, independently understandable modules by feature or capability, not global technical layers.
- **ALWAYS** define explicit module ownership and narrow public APIs that hide implementation details. Document each module's purpose and public contract in its `contract.md`.
- **NEVER** import another module's internals.
- **NEVER** introduce circular dependencies or hidden coupling.
- **NEVER** couple domain logic to frameworks, databases, or transport.
- **NEVER** use global mutable state or service locators.
- **NEVER** add speculative abstractions, wrappers, or unnecessary layers.
- Keep dependencies explicit and directed. Prefer composition.

## Code Quality
- **TRY NOT TO** exceed 1000 physical lines per handwritten source file. Exceed this guideline only when necessary and consistent with the overall architecture; justify exceptions.
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
- **NEVER** weaken tests, disable checks, or add exclusions to obtain a pass.
- **NEVER** modify enforcement configuration without explicit approval.
- **NEVER** add dependencies without explicit approval.
- Run available formatting, lint, typecheck, architecture checks, tests, and build before completion.
- Fix failures. Report checks that could not run; **NEVER** claim unverified success.
