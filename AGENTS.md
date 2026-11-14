# AGENTS.md

## Engineering scope
- Prefer correct, cohesive, maintainable changes over additional process or abstraction.
- Read the active requirements, relevant plan section, applicable module contracts, implementation, and tests before editing. Read only affected code; for dependent modules, normally read their public APIs and contracts.
- Follow applicable nested `AGENTS.md` files. Keep requirements, authorized work, implemented behavior, and accepted outcomes distinct.
- Do not edit any `AGENTS.md` without an explicit developer request. Do not expand the authorized task without approval.

## Architecture
- Organize by cohesive capabilities with clear owners and small public boundaries. Do not introduce a package or abstraction solely to satisfy a diagram.
- Import other modules through declared public APIs, not private implementations. Keep dependency direction explicit, acyclic, and enforceable in tests.
- Keep domain decisions independent of HTTP frameworks, database adapters, and external transport. Inject I/O collaborators at composition boundaries.
- Avoid global mutable registries, service locators, hidden side effects, speculative wrappers, and generic `common` modules. Extract shared code only when concrete consumers justify it.
- Prefer clear names, readable control flow, and explicit failure states. Some local duplication is acceptable when premature sharing would obscure ownership.

## Type safety and behavior
- Use strict typing and boundary validation; never introduce `Any`, casts, suppressions, or exceptions solely to bypass a check.
- Model meaningful public states and domain categories with enums when this improves correctness; simple local values do not require enums.
- Fix root causes of lint/type errors and exception failures. Do not hide unexpected exceptions or perform implicit I/O.
- Comments and docstrings should clarify non-obvious decisions or constraints, not repeat identifiers. Write all code comments and repository documentation in English.

## Documentation and SDD
- Read the relevant README for project context; keep AGENTS concise and README developer-facing. Maintain a README next to each existing AGENTS, but do not create extra documentation without a concrete need.
- Write `contract.md` for stable cross-module boundaries with meaningful invariants, errors, and interoperability concerns; do not duplicate a trivial typed implementation in prose.
- Keep the active sub-spec, implementation plan, feature cross-reference, and checkpoint consistent with real code. Never invent implementation paths or treat planned features as implemented.
- Do not record conversation provenance, patch history, or speculative acceptance in repository documentation.

## Checks and dependencies
- Verify changed behavior with positive, negative, and boundary tests. Enforce critical module imports and dependency direction automatically, with tests showing that invalid dependencies are rejected.
- Never weaken tests, disable checks, or add exceptions merely to obtain a pass. Changes to enforcement must preserve or strengthen required invariants and include regression evidence; relaxing an approved invariant requires explicit approval.
- New runtime dependencies require justification and developer approval. A task-scoped dev/test dependency may be added with a recorded rationale when it does not change runtime behavior or weaken checks.
- Run applicable formatting, lint, strict type, architecture, test, and build checks. Report exactly what ran and any environment limitations; never claim unverified results.
