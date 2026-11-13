# Web AGENTS.md

Extends `../AGENTS.md`. Applies to React and TypeScript code under `web/`.

## Architecture
- **ALWAYS** organize code by user-facing capability and colocate related components, hooks, and tests.
- **ALWAYS** expose narrow feature entry points; keep implementation details private.
- **ALWAYS** access remote services through typed, validated client boundaries.
- **NEVER** import backend implementation modules into browser code.
- **NEVER** introduce shared state, reusable abstractions, or additional layers without demonstrated need.

## React & TypeScript
- **ALWAYS** use strict TypeScript and explicit types at component and network boundaries.
- **NEVER** use `any`, `@ts-ignore`, non-null assertions, or unchecked casts to evade type safety.
- **ALWAYS** keep render logic predictable; extract substantial effects and transformations into named functions or hooks.
- **ALWAYS** handle request failures, cancellation, and stale asynchronous responses.
- **ALWAYS** model loading, empty, and error states explicitly.
- **ALWAYS** keep state local unless multiple consumers require shared ownership; avoid redundant copies of server state.
- **NEVER** expose credentials or sensitive values in browser bundles, URLs, logs, or telemetry.

## UI & Verification
- **ALWAYS** use semantic controls and support keyboard, touch, and responsive layouts.
- **ALWAYS** test interactions and failure states rather than component internals.
- **ALWAYS** use configured component and browser tests for affected behavior.
- **ALWAYS** run configured lint, TypeScript, test, and build checks; report unavailable checks.
