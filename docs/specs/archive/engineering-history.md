# Engineering Decision History (Non-normative)

This file is historical context only. Do not read during ordinary task implementation; current specifications, contracts and code are authoritative. Git records exact source changes.

## 2026-11-17 — Consolidated Web planning context

- **Context:** the active Web plan accumulated W01 follow-up narratives about reference geography, Saturn district scope, weather and UI adjustments after the matching code and tests existed.
- **Decision:** retain the stable workstream specification and a concise active integration plan; select bounded work via a `task.md`/`task-plan.md` pair and `STATE.json.selectedTaskPath`.
- **Rationale:** avoid competing historical descriptions in normal implementation context while retaining separate approval, implementation and acceptance states.
- **Current contracts:** `backend/src/melliatlas/api/contract.md`, `backend/src/melliatlas/territories/contract.md`, `backend/src/melliatlas/sources/contract.md`, `web/src/api/contract.md`.
