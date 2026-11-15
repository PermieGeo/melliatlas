/** Wire contracts mirror FastAPI InvestigationResponse and territory DTOs. */
export type CountryCode = "RU" | "BY";
export type InvestigationStatus = "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED";
export type Outcome =
  "PLAN_FOUND" | "INSUFFICIENT_EVIDENCE" | "NO_FEASIBLE_ALTERNATIVE";
export type EcologyStatus = "ELIGIBLE" | "EXCLUDED" | "CAUTION" | "UNKNOWN";
export type Proximity =
  | "FIELD_INTERSECTION"
  | "NEAR_REPORTED_FIELD"
  | "OUTSIDE_SCREEN_RADIUS"
  | "UNKNOWN_GEOMETRY"
  | "OUTSIDE_STATED_PERIOD"
  | "UNKNOWN_PERIOD";

export interface Country {
  code: CountryCode;
  name: string;
}
export interface Territory {
  id: string;
  country: CountryCode;
  kind: "country" | "region" | "district";
  name: string;
  parent_id: string | null;
  reference_id: string;
  valid_on: string;
  geometry_status: "available" | "missing" | "invalid";
}

export interface Position {
  longitude: number;
  latitude: number;
}
export interface InvestigationCreate {
  country: CountryCode;
  territory_id: string;
  scenario_id: string;
  season_start: string;
  season_end: string;
  starting_point?: Position;
}
export interface Stop extends Position {
  site_id: string;
  start: string;
  end: string;
  forage_level: "LOW" | "MEDIUM" | "HIGH";
  evidence_ids: string[];
}
export interface SeasonPlan {
  stops: Stop[];
  relocations: number;
  rationale: string;
}
export interface Evidence {
  id: string;
  source_id: string;
  source_mode: "FIXTURE";
  synthetic: true;
  effective_start: string;
  effective_end: string;
  uncertainty: string;
}
export interface Assessment {
  site_id: string;
  status: EcologyStatus;
  evidence_ids: string[];
  rule_ids: string[];
  reasons: string[];
  unknowns: string[];
  synthetic: true;
}
export interface Decision {
  kind:
    | "INITIAL"
    | "ECOLOGY_CHECK"
    | "TREATMENT_CHECK"
    | "REVISION"
    | "TERMINAL"
    | "LIMIT_REACHED";
  site_ids: string[];
  evidence_ids: string[];
  rule_ids: string[];
  note: string;
}
export interface Replanning {
  outcome: "PLAN_FOUND" | "NO_FEASIBLE_ALTERNATIVE" | "CHECK_LIMIT_REACHED";
  assessments: Assessment[];
  excluded_site_ids: string[];
  unknown_site_ids: string[];
  decisions: Decision[];
  checks_used: number;
  warnings: string[];
}
export interface ReportedProduct {
  name: string | null;
  crop: string | null;
  bee_hazard_class: 1 | 2 | 3 | null;
}
export interface Screening {
  site_id: string;
  source_record_id: string;
  source_id: string;
  proximity: Proximity;
  approximate_distance_km: number | null;
  warnings: string[];
  captured_at: string | null;
  scheduled_start: string | null;
  scheduled_end: string | null;
  source_uri: string | null;
  products: ReportedProduct[];
}
export interface TreatmentReview {
  screenings: Screening[];
  avoided_site_ids: string[];
  warnings: string[];
}
export interface Investigation {
  id: string;
  status: InvestigationStatus;
  request: Omit<InvestigationCreate, "starting_point">;
  created_at: string;
  updated_at: string;
  outcome: Outcome | null;
  plan: SeasonPlan | null;
  replanning: Replanning | null;
  treatment_review: TreatmentReview | null;
  evidence: Evidence[];
  decision_trace: string[];
  diagnostics: string[];
  reference_version: string;
  limitations: string[];
  synthetic: true;
}
