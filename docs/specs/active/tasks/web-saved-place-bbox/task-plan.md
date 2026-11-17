# WEB-PLACE-01 — Task Implementation Plan

- **Status:** DESIGN ONLY — no new backend or UI implementation is claimed.
- **Normative context:** [task](task.md), [Web sub-spec](../../subspecs/subspec-01-web-mvp.md), [umbrella](../../../umbrella_spec_melliatlas.md).
- **Task ID:** `WEB-PLACE-01`; proposed criteria `PLACE-A01`–`PLACE-A05`.

## Public contracts and integration design

**Current interfaces to inspect before coding:** `backend/src/melliatlas/territories/api.py` + `contract.md`, `backend/src/melliatlas/persistence/api.py` + `contract.md`, `backend/src/melliatlas/api/contract.md`, `web/src/api/{types,client,validation}.ts` + `contract.md`, and geographic invariants in `backend/src/melliatlas/geography/coordinates.py`. Read concrete `persistence/geography.py`, `api/routes_territories.py`, `web/src/{App,components/MapPanel}.tsx` and their tests **only when changing those modules**. Use public APIs/contracts for remaining dependencies.

**Proposed backend public boundary (requires approval):** a `SavedPlaceRepository` port for owner-scoped create/read/list/rename/update/delete, immutable `SavedPlace` and `AnalysisArea` typed values and an independent `IntersectingDistricts` geographic query returning reviewed district identities plus explicit coverage status. Place IDs must not encode coordinates or provider IDs. The geographic query must use server-authoritative geometry and reject invalid/out-of-region or ambiguous datasets; exact SQL belongs to persistence implementations, never `contract.md`.

**Proposed transport (not implemented):** same-origin `/api/v1/places` CRUD with typed DTO validation and stable error codes, plus read-only bbox/district resolution as an operation with distinct incomplete coverage. Never expose other users' saved coordinates. Until owner authentication/authorization is available, permit persistence only in an explicitly confined single-user/loopback development deployment. A publicly reachable unauthenticated list-by-ID or list-all endpoint is prohibited. Define ownership, access checks, CSRF/cross-origin policy and deletion behavior before choosing concrete API shapes.

**Proposed web boundary:** `SavedPlace` wire values are decoded in `web/src/api/` before use. An isolated place workflow manages one draft, the selected saved ID, pending mutations, cancelled requests and optimistic UI rollback. Map presentation receives typed point/bbox/outline props; it does not know PostGIS, Saturn identifiers or weather provider URLs. Persist private geometry only through approved place actions. Existing synthetic investigations remain separate.

**Area geometry:** construct a rectangle with physical dimensions measured in kilometres around WGS84 point; calculate geodesically or in a justified local projection, including latitude-dependent longitude scaling. Check <=30 km per dimension on both client and server; area is derived. The backend intersects the rectangle with *all* imported ADM2 polygons by positive intersection area, preserving provenance and unknown coverage. A point-only `ST_Covers` lookup is insufficient for this operation.

## Scope and sequencing

1. First establish place/domain/transport contracts and failing backend tests, then migration + persistence and real PostGIS checks.
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

No implementation acceptance is recorded by preparing this plan. Before writing the first feature code PATCH, approve the exact normative change, privacy/ownership strategy and public API shape. After implementation, retain only the current integration design and executable evidence; Git and `archive/` retain any significant superseded decisions.
