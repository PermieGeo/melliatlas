# WEB-MVP-T02 — Settlement and coordinate search UX (Task)

- **Task ID:** `WEB-MVP-T02`.
- **Workstream:** [MVP-01 Web](subspec.md).
- **Status:** PARTIAL — search UI and provider endpoint exist; integration acceptance pending.
- **Partition:** `frontend` — one change partition per task/PATCH.
- **Requirements:** `MVP01-WEB-R02, R08, R12` (existing normative IDs; no new approval implied).
- **Dependencies:** WEB-MVP-T01.
- **Implementation plan:** [paired plan](task_impl_plan_02_settlement_search.md).
- **Authorization:** only previously approved W01 work is authorized; all new gated behavior needs explicit developer approval.
- **Acceptance:** PENDING.

## Required outcome

A single labeled Search control accepts explicit WGS84 coordinates or an on-demand populated-place name and offers attributed, region-validated selection.

## Constraints

Never treat geocoding suggestions as canonical administrative IDs. Validate membership through the existing territory point resolver before changing map/draft state; reject stale responses, invalid coordinates and provider failures visibly. Field help is available on hover, focus and activation.

## Non-goals

No backend geocoder implementation, bulk gazetteer, automatic requests on typing, or source-terms changes.

## Acceptance oracles

- **WEB-MVP-T02-A01:** No request is issued before an explicit search; a country/region mismatch cannot move the point.
- **WEB-MVP-T02-A02:** Malformed coordinates, empty/no-result queries, upstream failure and cancellation have distinct accessible feedback without saving location data.
