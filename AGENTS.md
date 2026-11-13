# MelliAtlas Agent Rules

Applies repository-wide. A nearer `AGENTS.md` **adds** domain-specific requirements; it does not relax these rules.

## Read before changing anything

- Read `README.md`, `docs/specs/README.md`, the nearest `AGENTS.md`, and any active spec, linked plan, owner contract, implementation, and relevant tests. **Code proves current behavior; approved specs define intended behavior; drafts are not approval.**
- Treat `melliatlas_v01` as **reference-only**: inspect proven concepts or test cases, but never assume its TS server, Admin app, endpoints, database schema, or patch chain belongs here.
- Make the smallest coherent, testable change. Do not silently expand scope, implement a draft, alter developer-controlled checkpoints, or perform Git/deployment operations.

## Architecture

- Maintain one **Python modular monolith** (`backend/`) and one **thin React client** (`web/`). Keep API, Engine, Agent, source adapters, analysis, jobs, and persistence responsibilities distinct; do not introduce microservices or a separate Admin app.
- Organize by **capability and ownership**, not global `controllers/`, `services/`, and `repositories/` buckets. Expose narrow public interfaces; prohibit dependency cycles and imports of another module's internals.
- Engine must be usable **without an LLM**. Agent plans, observes, and replans through registered, bounded tools; neither user input nor model output may execute arbitrary code, SQL, or network calls.
- Keep server persistence, credentials, external-source retrieval, source policy, and private apiary coordinates off the client. Public APIs must be versioned, validated, implementation-neutral, and usable by future non-React clients.

## Code quality

- Maximize cohesion and minimize coupling. Apply DRY to **duplicated business rules**, not harmless syntax; abstract only for an actual second use or verified boundary. Prefer clear names, composition, and explicit dependencies over frameworks and layers for their own sake.
- **Hard ceiling: 500 nonblank, noncomment lines per hand-written source file.** Aim for focused functions (roughly 40 lines) and React components (roughly 150 lines); split by responsibility, not arbitrary line counts. Generated code, data fixtures, and migrations require separate review.
- Eliminate repeated or obscure **domain magic values**; use named constants/configuration. Obvious local values and externally mandated protocol literals may remain inline. Never hardcode countries, provider IDs, region codes, source URLs, model names, timeouts, or policy thresholds in business logic.
- Validate untrusted data at boundaries. Fail explicitly; never silently swallow errors, conceal unavailable evidence, or turn an unknown state into success.
- Use type-safe structures and descriptive finite states. Do not use unguarded `Any`/`any`, unchecked assertions, or suppression directives to bypass validation.

## Evidence, safety, and delivery

- Preserve provenance, acquisition time, source permissions, versions, geometry precision, uncertainty, and the distinction between **declared**, **observed**, **inferred**, and **synthetic** data. Never invent real observations, risk scores, certainty percentages, or safety verdicts.
- Keep precise private apiary positions and secrets out of public API payloads, model prompts, logs, telemetry, URLs, and third-party map requests. Require server-side authorization before disclosing sensitive data.
- Test intended behavior, failure paths, boundaries, regressions, and relevant persistence/restart behavior independently of implementation details. No live provider calls in routine tests. Never weaken a valid test to obtain green checks.
- Write **all repository documentation, specs, code comments, docstrings, configuration comments, and test descriptions in English**. Comments explain invariants or non-obvious reasons, not each operation. Update owner contracts/docs when public behavior changes.
- Run available format, lint, type, test, and build checks before claiming completion. State exactly what ran, what failed, and what is not yet configured. Never imply the empty scaffold has passing runtime tests.
