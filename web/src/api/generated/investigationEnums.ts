// Generated from backend investigation enums. Do not edit manually.
export const INVESTIGATION_STATUSES = [
  "QUEUED",
  "RUNNING",
  "COMPLETED",
  "FAILED",
] as const;
export type InvestigationStatus = (typeof INVESTIGATION_STATUSES)[number];

export const INVESTIGATION_OUTCOMES = [
  "PLAN_FOUND",
  "INSUFFICIENT_EVIDENCE",
  "NO_FEASIBLE_ALTERNATIVE",
] as const;
export type Outcome = (typeof INVESTIGATION_OUTCOMES)[number];
