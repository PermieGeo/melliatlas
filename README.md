# MelliAtlas

**Agentic geospatial analysis for beekeepers.**

This repository is an **empty architecture scaffold**, not a functioning application. Its initial purpose is to establish ownership boundaries and agent guidance before implementation. No API, web app, worker, database schema, data provider, agent, or analysis workflow is implemented.

## Target architecture

- `backend/`: Python modular monolith with a FastAPI boundary, a typed analysis engine, an adaptive agent, and a separately executed worker.
- `web/`: one minimal mobile-friendly React, TypeScript, Vite, Tailwind CSS, and Leaflet client. No separate Admin application.
- `config/`: planned country-specific source and analysis profiles. Russia and Belarus are initial target configurations; none is installed yet.
- `docs/specs/`: forthcoming normative specifications and their separate implementation plans.

Engine owns typed Sources/Analyzers interfaces, artifacts and DAG execution. Agent owns **Goal -> Plan -> Execute -> Observe -> Evaluate -> Replan / Finish**. The agent may use rules or an LLM but can invoke only registered, bounded tools. The future worker will execute durable jobs independently of HTTP. PostgreSQL/PostGIS will store cache, jobs, evidence, analysis runs, and geographic results. React will access only versioned HTTP APIs and will not depend on Engine internals.

The first MVP will exercise adaptive behavior using **explicitly synthetic sources**. Real providers, safety conclusions, and claims of live coverage require later approved specifications and validation.

## Source and specification status

- The prior `melliatlas_v01` repository and its concatenated snapshot are **reference-only**. Reuse proven ideas, algorithms, and test cases selectively; do not copy its runtime architecture, migrations, API routes, or patch history.
- The supplied *BeeGeoTrace draft v0.1* is a discussion input, with the product renamed **MelliAtlas**. It is **not** a developer-approved normative specification or evidence of implemented behavior.
- `docs/specs/active/` is intentionally empty. Create a normative sub-specification and a **separate linked implementation plan** when a workstream is approved.

## Layout

```text
backend/
  src/melliatlas/
    api/           # FastAPI transport, later
    engine/        # Typed artifacts, registries, DAG runtime, later
    agent/         # Adaptive decision loop, later
    sources/       # Source implementations, later
    analyzers/     # Analyzer implementations, later
    territories/   # Country and territory models, later
    jobs/          # Durable job orchestration and worker, later
    persistence/   # PostGIS and cache adapters, later
  tests/
web/
  src/
  tests/
config/
  countries/
docs/
  specs/active/
  specs/archive/
```

`AGENTS.md` at the root and within owning directories defines rules for future work. Empty directories are retained using `.gitkeep` files. There are deliberately **no dependency manifests, installed packages, generated sources, running services, or configured test commands** in this bootstrap.

## Planned work order

1. **A - Python Engine Core:** source/analyzer registries, typed artifacts, RU/BY configuration, deterministic DAG, isolated tests.
2. **B - Agentic Layer:** bounded adaptive planning, observable trace, fixed pipeline comparison, deterministic tests plus an optional LLM adapter.
3. **C - Persistence and Jobs:** PostGIS, cache, durable jobs, restart recovery, independent worker.
4. **D - Minimal React UI:** territory selection, analysis launch and progress, map, report, history.
5. **E - Synthetic competition demonstration:** an explainable, reproducible, agent-led district investigation.

These are roadmap headings, **not approved implementation stages**. No Git changes, deployments, or old-version migrations are implied by the scaffold alone.
