/** Wire contracts mirror FastAPI InvestigationResponse and territory DTOs. */
/** ISO 3166-1 alpha-2 code supplied by the country catalog, not a closed UI enum. */
export type CountryCode = string;
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

/** ISO country identity reported by the server; its name is a fallback for locale rendering. */
export interface Country {
  code: CountryCode;
  name: string;
}
/** Versioned geographic reference entry, never proof of complete regional coverage. */
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

/** An executable scenario advertised by the server, independently of validated territory references. */
export interface ScenarioListing {
  id: string;
  name: string;
  country: CountryCode;
  territory_id: string;
  territory_name: string;
  source_mode: "SYNTHETIC";
  season_start: string;
  season_end: string;
  is_default: boolean;
}

/** User-supplied WGS84 longitude and latitude, sent only in an investigation body. */
export interface Position {
  longitude: number;
  latitude: number;
}
/** Request contract; the optional private point must not be echoed in reads. */
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
/** Ordered relocation proposal, distinct from evidence of real-world safety. */
export interface SeasonPlan {
  stops: Stop[];
  relocations: number;
  rationale: string;
}
/** Attribution for one fictional source record and its stated uncertainty. */
export interface Evidence {
  id: string;
  source_id: string;
  source_mode: "FIXTURE";
  synthetic: true;
  effective_start: string;
  effective_end: string;
  uncertainty: string;
}
/** Fictional ecological decision with traceable evidence and rules. */
export interface Assessment {
  site_id: string;
  status: EcologyStatus;
  evidence_ids: string[];
  rule_ids: string[];
  reasons: string[];
  unknowns: string[];
  synthetic: true;
}
/** An ordered, typed decision from the bounded planner. */
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
/** Final ecology and treatment-aware decision details, including unknowns. */
export interface Replanning {
  outcome: "PLAN_FOUND" | "NO_FEASIBLE_ALTERNATIVE" | "CHECK_LIMIT_REACHED";
  assessments: Assessment[];
  excluded_site_ids: string[];
  unknown_site_ids: string[];
  decisions: Decision[];
  checks_used: number;
  warnings: string[];
}
/** Unverified source-reported pesticide and hazard-class claim. */
export interface ReportedProduct {
  name: string | null;
  crop: string | null;
  bee_hazard_class: 1 | 2 | 3 | null;
}
/** Spatial/temporal notice comparison, not a validated exposure model. */
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
/** Source observations together with candidates withheld from the provisional plan. */
export interface TreatmentReview {
  screenings: Screening[];
  avoided_site_ids: string[];
  warnings: string[];
}
/** Immutable HTTP result; execution status and domain outcome are independent. */
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
