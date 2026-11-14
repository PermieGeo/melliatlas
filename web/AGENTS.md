# Web AGENTS.md

Extends `../AGENTS.md`. Applies to React and TypeScript code under `web/`.

## Architecture
- Organize by user-facing capability and colocate related components, hooks, and tests.
- Expose narrow feature entry points, use typed client boundaries, and validate remote responses.
- Do not import backend implementation modules into the browser. Add shared state, abstractions, or layers only for concrete consumers.

## React and TypeScript
- Use strict TypeScript and explicit types at component and network boundaries. Do not bypass type checks with `any`, `@ts-ignore`, or unchecked casts.
- Keep renders predictable and effects explicit; extract nontrivial transformations when they improve comprehension or testing.
- Handle failures, cancellation, stale responses, and loading/empty/error UI states explicitly.
- Prefer local state; avoid redundant copies of remote data. Never expose credentials or private coordinates in browser logs, bundles, or telemetry.

## UI and verification
- Use semantic controls with keyboard, touch, and responsive support.
- Test observable interactions and failure modes, not component internals.
- Run configured lint, type, component, browser, and build checks; report unavailable checks.
