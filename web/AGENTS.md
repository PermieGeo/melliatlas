# React Web AGENTS.md

Inherits `../AGENTS.md`. This is the only frontend: React, strict TypeScript, Vite, Tailwind CSS, and Leaflet.

## Ownership
- **ALWAYS** keep Web focused on territory selection, server jobs, progress, Agent trace, results, maps, and history.
- **NEVER** implement DAG planning, Agent decisions, provider fetching, or persistence rules in React.
- **ALWAYS** call versioned server APIs through a typed, validated client boundary.
- **NEVER** call real provider/LLM endpoints directly or embed credentials in browser assets.
- **ALWAYS** organize by user capability as features emerge; keep reusable UI generic and feature dependencies explicit.
- **NEVER** import another feature's internal modules or build abstractions without actual reuse.

## State & Presentation
- **ALWAYS** use strict TypeScript and explicit prop/API boundary types.
- **NEVER** use `any`, `@ts-ignore`, unchecked casts, or non-null assertions to evade validation.
- **ALWAYS** model loading, empty, incomplete, stale, and failed states explicitly.
- **ALWAYS** keep state local by default; isolate nontrivial effects, fetching, and transformations from JSX.
- **NEVER** duplicate authoritative server state in an unnecessary global store.
- **ALWAYS** show source/time attribution, uncertainty, and synthetic status for geographic results.
- **ALWAYS** cancel or ignore stale requests after territory/job changes.
- **NEVER** leak private apiary coordinates through maps, URLs, logs, telemetry, or third parties.

## UX & Tests
- **ALWAYS** support responsive mobile/desktop layouts, keyboard access, and usable touch controls.
- **ALWAYS** keep map rendering replaceable without changing server contracts.
- **ALWAYS** test selection changes, polling failures, progress, history, attribution, accessibility, and map interactions.
- **ALWAYS** run configured TypeScript, lint, component, build, and Playwright checks for changed Web behavior.
