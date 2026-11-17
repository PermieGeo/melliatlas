# AGENTS.md

## Engineering scope
- Prefer correct, cohesive, maintainable changes over additional process or abstraction.
- Read the active requirements, relevant plan section, applicable module contracts, implementation, and tests before editing. Read only affected code; for dependent modules, normally read their public APIs and contracts.
- Follow applicable nested `AGENTS.md` files. Keep requirements, authorized work, implemented behavior, and accepted outcomes distinct.
- Do not edit any `AGENTS.md` without an explicit developer request. Do not expand the authorized task without approval.

## Architecture
- Organize by cohesive capabilities with clear owners and small public boundaries.
- Never place a concrete implementation in an abstract contract/interface layer (`api.py`, ports or protocol declarations); keep implementations in capability-owned, clearly named modules and inject them at composition boundaries. Do not introduce a package or abstraction solely to satisfy a diagram.
- Cross-capability consumers must use declared public API entrypoints (normally `api.py` for Python, or an explicitly documented public facade), never private implementation files. Composition roots may import concrete adapters solely to wire dependencies. Keep dependency direction explicit, acyclic, and enforceable in tests.
- Keep domain decisions independent of HTTP frameworks, database adapters, and external transport. Inject I/O collaborators at composition boundaries.
- Avoid global mutable registries, service locators, hidden side effects, speculative wrappers, and generic `common` modules. Extract shared code only when concrete consumers justify it.
- Prefer clear names, readable control flow, and explicit failure states. Some local duplication is acceptable when premature sharing would obscure ownership.

## Historical implementation reference
- Treat any earlier MelliAtlas implementation or v01 snapshot as research material, not the active baseline, a feature checklist, or an architectural template. Current specifications, public contracts, code, and tests govern new work.
- Study historical source formats, observed edge cases, provenance, deduplication, request limits, and test fixtures when relevant. Revalidate provider behavior, access permissions, and assumptions; legacy integration success does not establish present-day correctness or authorization.
- Do not mechanically port legacy modules, classes, HTTP endpoints, persistence structures, orchestration, admin/operator workflows, or UI components. Reassess the user need and implement the smallest cohesive design within current module boundaries; reuse algorithms only when their behavior is justified and tested.
- Design from beekeeper decisions, especially advance warning of planned pesticide applications, location and timing, chemical claims, weather uncertainty, and alternative apiary placements. Keep provider-specific acquisition separate from shared evidence models and analysis. Do not rebuild old infrastructure simply because it exists.
- Build the single beekeeper-facing Web experience around the current map, timeline, evidence, warnings, and alternatives, rather than copying legacy screens. Do not reintroduce a separate admin application without explicitly approved requirements and suitable authorization. Record relevant legacy-derived behavior and deliberate omissions in task-level plans or tests, not as speculative repository architecture.

## Type safety and behavior
- Use strict typing and boundary validation; never introduce `Any`, casts, suppressions, or exceptions solely to bypass a check.
- Model meaningful public states and domain categories with enums when this improves correctness; simple local values do not require enums.
- Fix root causes of lint/type errors and exception failures. Do not hide unexpected exceptions or perform implicit I/O.
- Comments and docstrings should clarify non-obvious decisions or constraints, not repeat identifiers. Write all code comments and repository documentation in English.

## Documentation and SDD
- Read the relevant README for project context; keep AGENTS concise and README developer-facing. Maintain a README next to each existing AGENTS, but do not create extra documentation without a concrete need.
- Keep each module `contract.md` concise and strictly consumer-facing: describe what the module provides to other modules, its documented public API entrypoint, observable guarantees and invariants, error semantics, and externally visible side effects or compatibility constraints. The API declarations (for example, `api.py`) own exact types and signatures. Never describe private algorithms, internal state, SQL queries, private implementation classes, or step-by-step implementation in `contract.md`; do not duplicate API declarations in prose.
- Keep the active sub-spec, implementation plan, feature cross-reference, and checkpoint consistent with real code. Never invent implementation paths or treat planned features as implemented.
- Keep active specifications, plans, contracts, and READMEs focused on current obligations and behavior, not chronological implementation history. Preserve only significant superseded engineering decisions in the non-normative `docs/specs/archive/` when needed; Git remains the complete change history. Never record conversation or AI provenance, PATCH handoff logs, or speculative acceptance in repository documentation.

## Checks and dependencies
- Verify changed behavior with positive, negative, and boundary tests. Enforce critical module imports and dependency direction automatically, with tests showing that invalid dependencies are rejected.
- Never weaken tests, disable checks, or add exceptions merely to obtain a pass. Changes to enforcement must preserve or strengthen required invariants and include regression evidence; relaxing an approved invariant requires explicit approval.
- New runtime dependencies require justification and developer approval. A task-scoped dev/test dependency may be added with a recorded rationale when it does not change runtime behavior or weaken checks.
- Run applicable formatting, lint, strict type, architecture, test, and build checks. Report exactly what ran and any environment limitations; never claim unverified results.

