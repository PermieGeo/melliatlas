# React Client Rules

Inherits `../AGENTS.md`. This is the **only frontend**: React + strict TypeScript + Vite + Tailwind CSS + Leaflet.

- Keep the browser a **thin presenter** of server jobs, progress/Agent trace, history, maps, and evidence-linked reports. Never reproduce Engine DAG scheduling, Agent decisions, source-policy checks, or PostGIS logic in React.
- Access server data only through a dedicated typed API boundary; validate untrusted responses and model explicit loading, empty, incomplete, stale, and failure states. No direct provider/LLM calls or client secrets.
- Organize `src/` by user capability (`app/`, `features/`, `shared/`) as features materialize. `shared` never depends on features; features use other features only through narrow public APIs. Do not create a framework for a tiny screen.
- Use strict TypeScript. Avoid `any`, `@ts-ignore`, unchecked casts, and non-null assertions. Prefer discriminated unions and inferred validated wire types; define explicit props for public components.
- Keep state local unless shared intentionally. Extract complex effects, async orchestration, and transformations from JSX into focused hooks/services; do not duplicate server state in an unnecessary global store.
- Keep the map component isolated behind a geographic view interface so a later renderer or Flutter client does not alter API contracts. Render GeoJSON, source/time labels, uncertainties, and **synthetic** status honestly.
- Build responsive, keyboard-accessible and touch-friendly map controls. Cancel or ignore stale async responses after territory/job changes; do not leak precise private locations via tiles, telemetry, URL parameters, or logs.
- Test selection changes, polling and recoverable failures, progress, history, report attribution, map interactions, accessibility, and desktop/mobile layouts with component tests and Playwright when configured.
