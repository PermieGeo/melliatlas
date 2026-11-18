# WEB-PLACE-01 — Saved analysis place and editable bbox

- **Task ID:** `WEB-PLACE-01`.
- **Status:** PARTIAL IMPLEMENTATION — place-first Web layout, read-only geographic bounds/district lookup, an unsaved React area-draft preview with verified coordinate entry, and an inactive owner-scoped persistence adapter; private saved-place CRUD remains gated.
- **Workstream:** `mvp-01-web`; [current Web sub-spec](../../subspecs/subspec-01-web-mvp.md); [task plan](task-plan.md).
- **Existing requirement anchors:** `MVP01-WEB-R01`, `MVP01-WEB-R02`, `MVP01-WEB-R08`, `MVP01-WEB-R12`, `MVP01-WEB-R13`. New saved-place and data-handling behavior must be incorporated into approved normative requirements before implementation.
- **Acceptance:** NOT CLAIMED. This task defines an independently testable first redesign slice, not the full planned product.

## User-visible outcome

A beekeeper selects a country and an **administrative region** (for example Smolensk Oblast), then creates and saves a named place composed of a WGS84 point and an editable, geographically measured bounding rectangle. Saved places are durable on the backend; they are not merely entries in browser localStorage.

## Bounded behavior proposed for approval

1. Place the country selector and settings access in the top-right header. Below, present **Region** and a combined settlement-or-coordinate search. Search remains disabled until a valid region is selected; distinguish missing region geography from an empty search result. A coordinate input must be validated against WGS84 and the selected region before becoming a place draft. The current Web search accepts a coordinate pair and reports that settlement lookup is unavailable; a regional gazetteer and thematic layers require separate approved capabilities.
2. Clicking the map creates or moves **one active draft point** and centers a default **15 km × 15 km** bbox around it. A draft can be resized interactively or by dimension input, with each dimension no larger than **30 km** and greater than zero; display width, height and computed area in km². Respect longitude scaling and geographic edge cases; do not equate a degree of longitude with a degree of latitude.
3. Repeated clicks while editing move the existing draft, not persisted places. After saving, a later click starts a new draft. Editing an existing saved place is an explicit action, with cancel/rollback behavior. A saved point is distinguished from its analysis rectangle. Selecting a search result recenters the map **without changing its zoom**; this alone does not save the place.
4. Saving requires a nonempty user name and valid point/bbox. Backend persistence uses stable IDs and verifies geometry server-side. Upon saving, identify **all reviewed ADM2 districts with positive-area overlap with the bbox** and highlight their boundaries; do not stop after one or two districts or rely on a point-only district lookup. Keep a distinct state when coverage is missing or ambiguous. District identities will later scope source discovery, including country-specific alternatives to RU-only Saturn for Belarus.
5. List saved places and allow select, rename and delete. Reopening a saved place restores its point and bbox and highlights it on the map, without pretending that weather, treatments, safety scores or report snapshots have already been computed. Handle server errors and stale requests visibly. Do not leak private coordinates through URLs, logs or telemetry.

## Explicit non-goals for this task

No mandatory Tauri/SQLite runtime integration, full offline synchronization, settlement/autocomplete dataset ingestion, regional roads/rivers/fields/forests/protected-areas import, 15-day weather forecast expansion, Saturn area-wide collection, temporal pesticide exposure model, safety rating, or final report. These are later independent tasks and are not implicitly approved or implemented here.

## Observable completion criteria (proposed, not accepted)

- **PLACE-A01:** Search is unavailable before region selection; after a valid region selection coordinate parsing and any available settlement lookup operate only in that region, with explicit unsupported catalog status.
- **PLACE-A02:** A map click creates a 15×15 km draft, subsequent clicks move it until save; resizing never permits either dimension above 30 km; distance/area and WGS84 edge cases are checked.
- **PLACE-A03:** Save/rename/delete/reopen survive browser reload using authenticated or appropriately isolated backend persistence; unsuccessful writes never appear as synchronized.
- **PLACE-A04:** Exactly the set of known positive-area bbox-overlapping districts is returned without a fixed maximum, and missing ADM2 coverage is not reported as an empty verified set.
- **PLACE-A05:** The selected place and map remain coherent across country/region changes, cancellations and failed requests, with no exposure of private coordinates in URL/logs.

## Approval gates

Read-only geographic bounds, district-query contracts, the unsaved browser draft preview, and server-verified coordinate entry are implemented. An owner-scoped PostgreSQL storage adapter and optional migration are prepared for review but **are not registered in the running backend**. Enabling saved-place CRUD still requires explicit approval of an authentication/privacy model, transport contracts, database migration/integration test access, and draft-versus-saved semantics. The current `STATE.json` workstream phase does not grant acceptance of this task.
