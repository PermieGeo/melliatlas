# MVP-01 Web — Workstream Integration Plan

- **Status:** IN PROGRESS — W01 partially implemented; acceptance pending.
- **Normative source:** [sub-spec](subspec.md).
- **Umbrella:** [MVP-01](../../umbrella_spec_melliatlas.md#mvp-01--working-sustainable-beekeeping-mvp).
- **Selected task:** [`WEB-PLACE-01`](task_03_area_draft.md) / [implementation plan](task_impl_plan_03_area_draft.md).
- **Authorization:** original W01 scope only; saved-place activation and new upstream permissions are not granted.

## Existing integration boundaries


| Boundary | Current implementation and constraints |
| --- | --- |
| Territory catalog | `GET /api/v1/territories/countries`, `/regions`, `/districts`, `/geometry/{territory_id}`; names and validated outlines may be unavailable; never invent administrative coverage. |
| Settlement suggestions | `POST /api/v1/sources/geocoding/settlements` performs one explicit bounded GeoNames/Open-Meteo name lookup. Results must pass the existing region-scoped point resolver before selection; the provider is non-commercial and not a complete locality catalog. |
| Spatial point resolver | `POST /api/v1/territories/resolve-point` returns one canonical containing location when PostGIS data supports it. |
| Read-only rectangle lookup | `POST /api/v1/territories/intersecting-districts` returns all imported ADM2 positive-area overlaps with **unverified** coverage; it stores no places. Requires imported PostGIS geometry. |
| Synthetic investigations | `GET /api/v1/investigations/scenarios`, `POST /api/v1/investigations`, `GET /api/v1/investigations/{id}`; results remain separate from live observations. |
| Live notice preview | Explicit opt-in RU-only Saturn source discovery and manual district-mapped page reads; at most 100 source records/10 pages per bounded read, with no completeness claim. Source date intervals may cover up to **one calendar year**. |
| Weather | Explicit opt-in, database-configured Open-Meteo provider; current contract supplies 24 UTC hours for a validated point. It does not provide a 15-day weather analysis or drift calculation. |
| Web transport | `web/src/api/client.ts`, `types.ts`, `validation.ts`, [contract](../../../../web/src/api/contract.md); backend OpenAPI and Pydantic DTOs own wire declarations. |

Source-of-truth contracts: [HTTP API contract](../../../../backend/src/melliatlas/api/contract.md), [territory port](../../../../backend/src/melliatlas/territories/api.py), [territory contract](../../../../backend/src/melliatlas/territories/contract.md), [sources port](../../../../backend/src/melliatlas/sources/api.py), [sources contract](../../../../backend/src/melliatlas/sources/contract.md). Database migration and operator setup details belong in [installation instructions](../../../INSTALLATION.md).

## Existing behavior and missing guarantees

`web/src/App.tsx` coordinates country, region, selected territory/point, the opt-in live-source previews and a developer-only synthetic test route. `WorkspaceHeader`, `PlaceSearchToolbar`, `MapPanel`, `ReferenceControls`, `LiveAreaAnalysis`, `WeatherPanel` and `Timeline` display the existing workflow in a place-first shell. Country/settings sit in the header, settlement-or-coordinate search above the map, analysis/weather to its right and an honest disconnected saved-places area below the map. Browser code does not store private selected points. Viewport, validated public territory preferences and an ordered one-year source date interval have separate local persistence; no user coordinates or queries are saved. The Web OpenStreetMap basemap loads immediately and discloses third-party viewport sharing with an opt-out; there is no offline basemap or regional thematic dataset yet.

The UI offers an **unsaved** editable 15–30 km analysis rectangle, region-verified manual WGS84 coordinate entry or a selected geocoding suggestion and an explicit read-only lookup of imported districts, without claiming complete ADM2 coverage. It does **not** yet save private analysis places, load a complete regional thematic dataset, render all district boundary overlays, or persist analytic snapshots locally. Browser and live PostGIS verification, external-source access/reuse rights, feature acceptance and production authentication remain open gates.

The existing server/client code permits a one-calendar-year source filter; documentation or operator hints must not silently restore the obsolete 31-day limit. API date filtering, source completeness, and evidence validity are distinct claims.

## Dependency and partition order

1. `WEB-MVP-T01`, `T02`, `WEB-PLACE-01`, `T04`–`T06`: audit and complete independent `frontend` behavior against existing public backend contracts. No task edits server files.
2. `WEB-MVP-T07`: separate `backend` task after explicit owner/privacy/transport approval and real PostGIS evidence. No frontend or test edits in this task.
3. `WEB-MVP-T08`: `frontend` saved-place UI only after T07 delivers a verified API contract.
4. After all implementation tasks `WEB-MVP-T01`–`T08` are delivered on **one feature branch**, start the end-of-sub-spec verification phase. `WEB-MVP-T09` prepares/adjusts Playwright browser E2E and Python pytest/httpx real-ASGI endpoint/integration E2E in the `tests` partition only, **without executing any tests yet**.
5. `WEB-MVP-T10` reviews all existing tests, removes unjustified/stale cases with rationale, generates missing independent tests, then runs every required unit/contract/architecture, browser/UI E2E, Python endpoint E2E, PostGIS/integration, lint, typecheck and build gate. Full canonical `CHK` and all required manual suites must PASS before commit/push/PR/merge into `main`. Failures are repaired by partition-scoped follow-up ZIPs **on the same feature branch**; rerun the final gate after every repair.

Read only the selected task, paired plan, public contracts of dependencies, and relevant source modules. See [development workflow](../../../DEVELOPMENT_WORKFLOW.md) for partitioned snapshots and the end-of-sub-spec test gate. No tests run during implementation tasks; the branch is shared across all tasks, and merges happen only after final verification and approval.

## Outstanding gates

- External geodata reuse, real Saturn availability/rights, and production security are not proven.
- Saved-place API activation requires approved ownership, transport and real DB verification.
- A browser E2E test with intercepted responses does not prove external source connectivity or durable storage.
- `apatch` does not permit unchecked commit: use `APL,FMT,STS` only while accumulating task changes on one unfinished feature branch. Do not merge until end-of-sub-spec test preparation, successful UI/E2E/integration and conventional tests, and a valid canonical `CHK`.
- The paused backend workstream retains its legacy sub-spec files until separately selected for decomposition. Its own phase and approvals do not change here.
