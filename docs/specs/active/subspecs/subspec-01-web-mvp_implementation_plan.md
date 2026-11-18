# MVP-01 Web — Current Integration Plan

- **Status:** IN PROGRESS — existing W01 implemented in part; acceptance pending.
- **Normative source:** [Web sub-spec](subspec-01-web-mvp.md).
- **Parent:** [Umbrella MVP-01](../../umbrella_spec_melliatlas.md#mvp-01--working-sustainable-beekeeping-mvp).
- **Requirements approval:** APPROVED — original W01 browser scope.
- **Implementation authorization:** AUTHORIZED — original W01 scope only; the new saved-place task remains design-only until explicit approval.
- **Acceptance:** PENDING.
- **Selected bounded task:** [Saved place and editable bbox](../tasks/web-saved-place-bbox/task.md) with [task plan](../tasks/web-saved-place-bbox/task-plan.md); backend read-only geography and the unsaved React preview are implemented; the owner-scoped storage adapter remains disconnected.

This document is a stable entrypoint for the selected Web workstream, not a chronology of completed increments. For the selected bounded task read only its task/plan, shared normative requirements and the explicitly listed module contracts and code. Do not re-open previous task history by default.

## 1. Existing public integration boundaries

| Boundary | Current implementation and constraints |
| --- | --- |
| Territory catalog | `GET /api/v1/territories/countries`, `/regions`, `/districts`, `/geometry/{territory_id}`; names and validated outlines may be unavailable; never invent administrative coverage. |
| Spatial point resolver | `POST /api/v1/territories/resolve-point` returns one canonical containing location when PostGIS data supports it. |
| Read-only rectangle lookup | `POST /api/v1/territories/intersecting-districts` returns all imported ADM2 positive-area overlaps with **unverified** coverage; it stores no places. Requires imported PostGIS geometry. |
| Synthetic investigations | `GET /api/v1/investigations/scenarios`, `POST /api/v1/investigations`, `GET /api/v1/investigations/{id}`; results remain separate from live observations. |
| Live notice preview | Explicit opt-in RU-only Saturn source discovery and manual district-mapped page reads; at most 100 source records/10 pages per bounded read, with no completeness claim. Source date intervals may cover up to **one calendar year**. |
| Weather | Explicit opt-in, database-configured Open-Meteo provider; current contract supplies 24 UTC hours for a validated point. It does not provide a 15-day weather analysis or drift calculation. |
| Web transport | `web/src/api/client.ts`, `types.ts`, `validation.ts`, [contract](../../../../web/src/api/contract.md); backend OpenAPI and Pydantic DTOs own wire declarations. |

Source-of-truth contracts: [HTTP API contract](../../../../backend/src/melliatlas/api/contract.md), [territory port](../../../../backend/src/melliatlas/territories/api.py), [territory contract](../../../../backend/src/melliatlas/territories/contract.md), [sources port](../../../../backend/src/melliatlas/sources/api.py), [sources contract](../../../../backend/src/melliatlas/sources/contract.md). Database migration and operator setup details belong in [installation instructions](../../../INSTALLATION.md).

## 2. Current implementation and unmet guarantees

`web/src/App.tsx` coordinates country, region, selected territory/point, the opt-in live source previews and the separate synthetic investigation. `WorkspaceHeader`, `PlaceSearchToolbar`, `MapPanel`, `ReferenceControls`, `LiveAreaAnalysis`, `WeatherPanel` and `Timeline` display the existing workflow in a place-first shell. Country/settings sit in the header, region/coordinate entry above the map, analysis/weather to its right and an honest disconnected saved-places area below the map. Browser code does not store private selected points. Viewport and validated public territory preferences have separate local persistence. The Web OpenStreetMap basemap loads immediately and discloses third-party viewport sharing with an opt-out; there is no offline basemap or regional thematic dataset yet.

The UI offers an **unsaved** editable 15–30 km analysis rectangle, region-verified manual WGS84 coordinate entry and an explicit read-only lookup of imported districts, without claiming complete ADM2 coverage. It does **not** yet save private analysis places, load a complete regional thematic dataset, render all district boundary overlays, or persist analytic snapshots locally. Browser and live PostGIS verification, external-source access/reuse rights, feature acceptance and production authentication remain open gates.

The existing server/client code permits a one-calendar-year source filter; documentation or operator hints must not silently restore the obsolete 31-day limit. API date filtering, source completeness, and evidence validity are distinct claims.

## 3. Selected next task and contract-first design

**Selected task:** `WEB-PLACE-01`, [requirements](../tasks/web-saved-place-bbox/task.md) and [integration design](../tasks/web-saved-place-bbox/task-plan.md).

The read-only rectangle/district contract and unsaved Web preview are implemented. Owner-scoped private place values, an optional storage adapter and migration are prepared, but **not wired to any HTTP route or startup path**. Activation and the UI workflow remain gated by explicit approval of user ownership/security, CRUD transport contracts, real PostGIS verification and available regional map coverage. Do not create a Tauri runtime dependency, general workflow engine or new country/provider registry as part of this slice.

## 4. Current TDD evidence and verification

Existing browser component/API tests include `web/tests/{workflow,reference-navigation,reference-geometry,weather,saturn,live-area-analysis,place-workspace}.test.tsx` where present, plus the project Playwright scenario `web/e2e/workspace.spec.ts`. Relevant backend contracts include `backend/tests/contract/{test_territory_http,test_administrative_geometry,test_saturn_district_scope,test_open_meteo_live_http}.py`. The selected task plan lists **new** tests required before its implementation, without pretending they exist.

TDD is required for new behavior: a failing behavior test, then implementation, then the relevant unit/contract/integration checks and canonical `run-tests.sh`. A passing mocked suite does not prove a migrated PostGIS or live browser startup. Acceptance still requires developer review and verification of the actual storage and map behavior.

## 5. Next dependencies (not authorized implementation tasks)

1. Geographical context: region-scoped settlements or coordinate lookup, roads, rivers, protected areas, forests and fields with source licensing and coverage metadata; no assumption that the existing ADM1/ADM2 dataset contains these layers.
2. Timeline and evidence: date-aware treatment geometry, distinct planned/confirmed activity, source completeness and weather uncertainty; wind effects and safety reports require independently validated methods.
3. Desktop storage: React + Tauri with SQLite for large cached geospatial/analysis data, keeping small user-owned places server-backed and synchronizable; defer runtime dependency selection and security review until the desktop slice.

Do not interpret this dependency list as accepted requirements, completed stages or permission to read provider data.
