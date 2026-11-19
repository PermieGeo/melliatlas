# WEB-MVP-T04 — Synthetic investigation lifecycle and reopening (Task)

- **Task ID:** `WEB-MVP-T04`.
- **Workstream:** [MVP-01 Web](subspec.md).
- **Status:** PARTIAL — developer-only synthetic route exists.
- **Partition:** `frontend` — one change partition per task/PATCH.
- **Requirements:** `MVP01-WEB-R03, R04, R08, R10` (existing normative IDs; no new approval implied).
- **Dependencies:** WEB-MVP-T01.
- **Implementation plan:** [paired plan](task_impl_plan_04_investigation_flow.md).
- **Authorization:** only previously approved W01 work is authorized; all new gated behavior needs explicit developer approval.
- **Acceptance:** PENDING.

## Required outcome

An explicit, separately labeled synthetic investigation can be started, polled, canceled and reopened by opaque ID without being confused with live evidence.

## Constraints

Respect server-discovered scenarios and dates; show QUEUED/RUNNING/COMPLETED/FAILED, no plan and typed failures. Ignore stale responses and avoid persisting private points.

## Non-goals

No production live planner, backend investigation algorithm, or automatic fixture execution in normal browser workspace.

## Acceptance oracles

- **WEB-MVP-T04-A01:** Developer demo scenario starts and reopens with server-owned supported dates and accurate synthetic labeling.
- **WEB-MVP-T04-A02:** Polling cancellation, 404/409/422/503 and a completed no-plan outcome are visible rather than converted into a fictional plan.
