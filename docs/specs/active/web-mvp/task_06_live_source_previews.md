# WEB-MVP-T06 — Manual live weather and Saturn previews (Task)

- **Task ID:** `WEB-MVP-T06`.
- **Workstream:** [MVP-01 Web](subspec.md).
- **Status:** PARTIAL — explicit previews exist; live upstream acceptance pending.
- **Partition:** `frontend` — one change partition per task/PATCH.
- **Requirements:** `MVP01-WEB-R08, R11, R12` (existing normative IDs; no new approval implied).
- **Dependencies:** WEB-MVP-T01, WEB-MVP-T02.
- **Implementation plan:** [paired plan](task_impl_plan_06_live_source_previews.md).
- **Authorization:** only previously approved W01 work is authorized; all new gated behavior needs explicit developer approval.
- **Acceptance:** PENDING.

## Required outcome

Manual weather/Saturn controls show actual opt-in source availability, bounded progress, date selection and actionable error/empty/partial outcomes, never synthetic stand-ins.

## Constraints

Persist only the non-sensitive date interval, not coordinates. Live Saturn requests require a verified mapped district and must not expand to region-wide collection or bbox claims. Weather is a separate attributed forecast capability; neither source proves safety.

## Non-goals

No new provider transport, automatic Saturn crawling, area-wide treatment synthesis, or commercial rights assertion.

## Acceptance oracles

- **WEB-MVP-T06-A01:** A manual preview has an observable pending state and finishes with attributed content, empty, unavailable or error, with no silent button.
- **WEB-MVP-T06-A02:** RU/BY source gating, unmapped district, canceled date change and persisted non-sensitive date interval remain coherent.
