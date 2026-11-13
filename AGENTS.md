# AGENTS.md

## Role
- Act as a senior software architect and engineer.
- Be terse. No filler, apologies, or explanations of standard concepts.
- Prioritize correctness, modularity, simplicity, and maintainability.

## Before Editing
- **ALWAYS** read the approved specification, linked plan, and contracts, source files, and tests of modules affected by the current stage or feature group.
- **ALWAYS** load only modules that must change for the current specification stage or feature group. For dependent modules, read only their `contract.md` and public API.
- **TRY TO** reuse existing functionality before implementing new code; inspect relevant module contracts and public APIs, not the entire codebase.
- **ALWAYS** follow the nearest `AGENTS.md`; nested rules may strengthen, never weaken root rules.
- **ALWAYS** carefully read `docs/specs/AGENTS.md` and strictly follow its directives alongside other applicable `AGENTS.md` files.
- **ALWAYS** distinguish implemented behavior from approved requirements and unapproved drafts.
- **NEVER** modify any `AGENTS.md` unless the user explicitly requests it.
- Make minimal, cohesive changes. **NEVER** expand scope without approval.

## Architecture
- **ALWAYS** organize code into cohesive, independently understandable modules by feature or capability, not global technical layers.
- **ALWAYS** define explicit module ownership and narrow public APIs that hide implementation details. Document each module's purpose and public contract in its `contract.md`.
- **ALWAYS** collect genuinely general-purpose reusable functions in a dedicated `common` module; keep domain-specific helpers with their owning modules.
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
- **TRY TO AVOID** magic numbers and magic strings. Extract constants only when they improve readability or reliability.
- **ALWAYS** use enums for coherent finite sets of related values, such as statuses and error codes.
- **NEVER** introduce dead code.
- **REMEMBER** occasional duplication is acceptable; address it through focused periodic refactoring instead of loading unrelated modules to keep the entire codebase synchronized.
- **NEVER** swallow exceptions or hide failures.
- **NEVER** introduce implicit I/O, hidden side effects, or hardcoded configuration.
- Prefer readable control flow, explicit state, and clear naming.
- Keep comments, docstrings, tests, and documentation in English.

## Documentation
- **ALWAYS** maintain a `README.md` alongside each `AGENTS.md`. Read the relevant README before editing its area; use README for developer-facing information and AGENTS for concise engineering directives. Keep them complementary, not duplicative.
- **ALWAYS** limit routine documentation to those README files, owned module `contract.md` files, SDD specifications/plans and required SDD metadata, plus `docs/INSTALLATION.md`, `docs/USAGE.md`, `docs/TESTS.md`, and `docs/FEATURES.md`. **NEVER** create other documentation without an explicit request.
- **ALWAYS** link sub-specifications to their implementing modules and tests using stable feature IDs defined in `docs/FEATURES.md`. Keep that catalog limited to feature IDs and brief descriptions. Record stage, specification, implementation owner, and test paths in `docs/specs/feature-cross-ref.yaml`; validate them against `docs/specs/feature-cross-ref.schema.json`. Never invent implementation paths or treat planned files as implemented.
- **NEVER** add conversation history, prior product names, patch chronology, or speculative approval/progress statements to README files or other stable documentation unless explicitly requested.

## Tests & Enforcement
- **ALWAYS** test new and changed behavior, including failures and edge cases.
- **ALWAYS** enforce module boundaries, forbidden imports, and dependency cycles automatically.
- **NEVER** weaken tests, disable checks, or add exclusions to obtain a pass.
- **NEVER** modify enforcement configuration without explicit approval.
- **NEVER** add dependencies without explicit approval.
- Run available formatting, lint, typecheck, architecture checks, tests, and build before completion.
- Fix failures. Report checks that could not run; **NEVER** claim unverified success.
