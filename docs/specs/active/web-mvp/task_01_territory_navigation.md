# WEB-MVP-T01 — Territory navigation and accessible map shell (Task)

- **Task ID:** `WEB-MVP-T01`.
- **Workstream:** [MVP-01 Web](subspec.md).
- **Status:** PARTIAL — implementation exists; browser acceptance pending.
- **Partition:** `frontend` — one change partition per task/PATCH.
- **Requirements:** `MVP01-WEB-R01, R02, R08, R09, R13` (existing normative IDs; no new approval implied).
- **Dependencies:** None.
- **Implementation plan:** [paired plan](task_impl_plan_01_territory_navigation.md).
- **Authorization:** only previously approved W01 work is authorized; all new gated behavior needs explicit developer approval.
- **Acceptance:** PENDING.

## Required outcome

A beekeeper can navigate real RU/BY geographic references in a responsive, keyboard-accessible map workspace without fictional administrative coverage.

## Constraints

Show unavailable/partial reference states; attribute the OSM basemap, disclose viewport requests, and retain an immediate tile opt-out. Do not put private coordinates into persisted preferences or URLs.

## Non-goals

No new reference-data importer, postgis schema, or test harness in this task.

## Acceptance oracles

- **WEB-MVP-T01-A01:** The map and territory controls remain available with valid regions and explain 503, unsupported districts and missing outlines without substitutes.
- **WEB-MVP-T01-A02:** The tile disclosure and toggle remain accessible across desktop and narrow layouts; tile loss does not erase accessible geography.
