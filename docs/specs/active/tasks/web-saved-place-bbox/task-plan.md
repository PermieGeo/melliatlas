# WEB-PLACE-01 — Task Implementation Plan

- **Status:** PARTIAL IMPLEMENTATION — read-only geography plus prepared, disconnected owner-scoped PostGIS storage; HTTP CRUD and UI remain pending.
- **Normative context:** [task](task.md), [Web sub-spec](../../subspecs/subspec-01-web-mvp.md), [umbrella](../../../umbrella_spec_melliatlas.md).
- **Task ID:** `WEB-PLACE-01`; proposed criteria `PLACE-A01`–`PLACE-A05`.

## Public contracts and integration design

**Current interfaces to inspect before coding:** `backend/src/melliatlas/territories/api.py` + `contract.md`, `backend/src/melliatlas/persistence/api.py` + `contract.md`, `backend/src/melliatlas/api/contract.md`, `web/src/api/{types,client,validation}.ts` + `contract.md`, and geographic invariants in `backend/src/melliatlas/geography/coordinates.py`. Read concrete `persistence/geography.py`, `api/routes_territories.py`, `web/src/{App,components/MapPanel}.tsx` and their tests **only when changing those modules**. Use public APIs/contracts for remaining dependencies.

**Implemented read-only geographic boundary:** `melliatlas.geography.make_analysis_bounds` and `territories.api.TerritoryAreaDistrictLookup` are public typed entrypoints. `persistence.area_districts.PostgisAreaDistrictLookup` performs positive-area intersection of all imported ADM2 boundaries with the bounded rectangle; `api.routes_territories` exposes the opt-in `POST /api/v1/territories/intersecting-districts` body-only read. Coverage remains `MISSING` or `UNVERIFIED` until independently verified. Tests: `backend/tests/unit/test_{analysis_area_bounds,postgis_area_districts}.py` and `backend/tests/contract/test_area_district_http.py`. PostGIS integration with real source geometries remains outstanding.

**Prepared saved-place boundary (not activated):** `places/api.py` declares immutable `SavedPlaceDraft` and `SavedPlace` values, typed storage errors and an owner-scoped `SavedPlaceRepository` Protocol. `places/validation.py` checks names, country/region association, WGS84 location and 15–30 km area constraints. The optional `persistence/saved_places.py` adapter implements create/read/list/update/delete against `0008_saved_places.sql` using immutable UUID identities, owner filtering and optimistic revision checks; real PostGIS migration/CRUD/ownership checks are added to the **opt-in** `smoke_postgis_startup.py` runner. Its behavior is currently verified only by offline recording-store tests; no production DB verification or API activation is claimed. The saved-place table is not touched by ordinary startup.

**Proposed transport (not implemented):** same-origin `/api/v1/places` CRUD with typed DTO validation and stable error codes, plus read-only bbox/district resolution as an operation with distinct incomplete coverage. Never expose other users' saved coordinates. Until owner authentication/authorization is available, permit persistence only in an explicitly confined single-user/loopback development deployment. A publicly reachable unauthenticated list-by-ID or list-all endpoint is prohibited. Define ownership, access checks, CSRF/cross-origin policy and deletion behavior before choosing concrete API shapes.

**Proposed web boundary:** `SavedPlace` wire values are decoded in `web/src/api/` before use. An isolated place workflow manages one draft, the selected saved ID, pending mutations, cancelled requests and optimistic UI rollback. Map presentation receives typed point/bbox/outline props; it does not know PostGIS, Saturn identifiers or weather provider URLs. Persist private geometry only through approved place actions. Existing synthetic investigations remain separate.

**Area geometry:** construct a rectangle with physical dimensions measured in kilometres around WGS84 point; calculate geodesically or in a justified local projection, including latitude-dependent longitude scaling. Check <=30 km per dimension on both client and server; area is derived. The backend intersects the rectangle with *all* imported ADM2 polygons by positive intersection area, preserving provenance and unknown coverage. A point-only `ST_Covers` lookup is insufficient for this operation.

## Scope and sequencing

1. Approve owner/authorization and SavedPlace HTTP transport contracts, review the prepared migration, and run the opt-in CRUD checks on a real PostGIS test database. Only then wire the repository into the application. Existing read-only area intersections are separate from saved-place storage.
2. Add a focused React place hook and a draft/bbox map interaction with keyboard-accessible resize/dimension inputs. Reuse existing country/region catalog and current API client.
3. Add save, selection, rename/delete, persisted reopen and district overlays. Do not integrate a new national gazetteer or large regional base-layer ingestion in this task.

**Out of scope:** full multi-user authentication, Tauri application packaging, bulk OSM imports, offline map packs and environmental assessment. Backend user ownership may require a separate approved prerequisite rather than weakening data privacy to fit the task.

## TDD and verification inventory

| Oracle | New test required before implementation |
| --- | --- |
| `PLACE-A01` | Web region/search disabled state, coordinate parsing and catalog unavailable cases |
| `PLACE-A02` | Geodesic bbox center, width/height limits and date/longitude/latitude edge cases; map draft interaction |
| `PLACE-A03` | Real PostGIS migration/CRUD persistence, ownership isolation, failed transactions, restart/reopen |
| `PLACE-A04` | PostGIS bbox crossing 0/1/2/many districts, edge-only touching, missing/partial ADM2 reference coverage |
| `PLACE-A05` | Browser state transitions, abort/stale responses and coordinate privacy assertions |

Run relevant unit/contract/architecture checks plus `sh ./run-tests.sh` and browser E2E with a migrated test PostGIS. A mocked query or green lint result is not evidence of persistence correctness. Tauri/SQLite selection requires a separate approved task and checks.

## Exit evidence and developer gates

No feature acceptance is recorded. The read-only, unsaved area query does not require user ownership or a data migration. Activating saved-place persistence and public CRUD remains blocked until the developer approves the exact ownership/privacy strategy and transport contract. The disconnected adapter is not authorization to expose private places. After implementation, retain only current integration design and executable evidence; Git and `archive/` retain significant superseded decisions.
