# Browser HTTP boundary — W01

`client.ts` exposes `listCountries`, `listRegions`, `listDistricts`, `startInvestigation` and `getInvestigation`. Every operation receives an `AbortSignal`, returns an `ApiResult<T>` discriminated union, and sends requests only to same-origin `/api/v1/` paths. The Vite development proxy is configured separately from production API deployment.

`types.ts` documents the subset of actual FastAPI wire responses consumed by W01. `validation.ts` rejects malformed or mismatched response shapes before returning typed data; nested treatment findings, ecological decisions, evidence summaries and coordinates are checked. The Python Pydantic DTOs, generated OpenAPI and backend contract tests remain authoritative; client contract tests exercise an HTTP fixture generated from the real combined FastAPI scenario. No browser module imports Python source, source-provider internals or database adapters.

An error retains the HTTP status and stable server error code when available. Cancelled requests return `ABORTED`, transport failures return `NETWORK_ERROR`, and incorrectly structured responses return `INVALID_RESPONSE`. A successful HTTP 202 is not a completed analysis; polling and bounded retries belong to `App.tsx`.

The private `starting_point` exists only in the POST body; the decoder rejects an unexpected private coordinate in the returned request. Do not log, store or place it in a URL. Completed data may be reloaded by opaque investigation UUID only while the server still has a snapshot. No frontend action triggers source scraping or a background provider collection job.
