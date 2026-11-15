import type {
  Assessment,
  Country,
  CountryCode,
  GeoPosition,
  ReferenceShape,
  TerritoryGeometry,
  Decision,
  Evidence,
  ExternalSource,
  WeatherForecast,
  SaturnNoticePage,
  SaturnNotice,
  Investigation,
  Replanning,
  ReportedProduct,
  Screening,
  ScenarioListing,
  SeasonPlan,
  Stop,
  Territory,
  TreatmentReview,
} from "./types";

/** Boundary rejection for malformed or unsupported server response data. */
class WireError extends Error {
  constructor(field: string) {
    super(`Invalid API response field: ${field}`);
    this.name = "WireError";
  }
}
export { WireError };

function record(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new WireError(field);
  }
  return Object.fromEntries(Object.entries(value));
}
function text(value: unknown, field: string): string {
  if (typeof value !== "string") throw new WireError(field);
  return value;
}
function nonEmpty(value: unknown, field: string): string {
  const result = text(value, field);
  if (!result.trim()) throw new WireError(field);
  return result;
}
function numeric(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isFinite(value))
    throw new WireError(field);
  return value;
}
function integer(value: unknown, field: string): number {
  const result = numeric(value, field);
  if (!Number.isInteger(result) || result < 0) throw new WireError(field);
  return result;
}
function booleanTrue(value: unknown, field: string): true {
  if (value !== true) throw new WireError(field);
  return true;
}
function oneOf<const T extends string>(
  value: unknown,
  field: string,
  choices: readonly T[],
): T {
  for (const choice of choices) {
    if (value === choice) return choice;
  }
  throw new WireError(field);
}
function maybe<T>(
  value: unknown,
  reader: (entry: unknown, field: string) => T,
  field: string,
): T | null {
  return value === null ? null : reader(value, field);
}
function list<T>(
  value: unknown,
  field: string,
  reader: (entry: unknown, field: string) => T,
): T[] {
  if (!Array.isArray(value)) throw new WireError(field);
  return value.map((item: unknown, index: number) =>
    reader(item, `${field}[${index}]`),
  );
}
const strings = (value: unknown, field: string): string[] =>
  list(value, field, text);

const statuses = ["QUEUED", "RUNNING", "COMPLETED", "FAILED"] as const;
const outcomes = [
  "PLAN_FOUND",
  "INSUFFICIENT_EVIDENCE",
  "NO_FEASIBLE_ALTERNATIVE",
] as const;
const ecology = ["ELIGIBLE", "EXCLUDED", "CAUTION", "UNKNOWN"] as const;
const proximity = [
  "FIELD_INTERSECTION",
  "NEAR_REPORTED_FIELD",
  "OUTSIDE_SCREEN_RADIUS",
  "UNKNOWN_GEOMETRY",
  "OUTSIDE_STATED_PERIOD",
  "UNKNOWN_PERIOD",
] as const;
const decisionKinds = [
  "INITIAL",
  "ECOLOGY_CHECK",
  "TREATMENT_CHECK",
  "REVISION",
  "TERMINAL",
  "LIMIT_REACHED",
] as const;

function country(value: unknown, field: string): CountryCode {
  const code = text(value, field);
  if (!/^[A-Z]{2}$/.test(code)) throw new WireError(field);
  return code;
}
export function decodeCountries(value: unknown): Country[] {
  return list(value, "countries", (entry, path) => {
    const item = record(entry, path);
    return {
      code: country(item.code, `${path}.code`),
      name: nonEmpty(item.name, `${path}.name`),
    };
  });
}
/** Validate dynamic source availability without allowing untrusted dates or cross-country scopes. */
export function decodeScenarios(value: unknown): ScenarioListing[] {
  const entries = list(value, "scenarios", (entry, path) => {
    const item = record(entry, path);
    const seasonStart = text(item.season_start, `${path}.season_start`);
    const seasonEnd = text(item.season_end, `${path}.season_end`);
    if (
      !isIsoDate(seasonStart) ||
      !isIsoDate(seasonEnd) ||
      seasonStart > seasonEnd
    )
      throw new WireError(`${path}.season`);
    if (typeof item.is_default !== "boolean")
      throw new WireError(`${path}.is_default`);
    return {
      id: nonEmpty(item.id, `${path}.id`),
      name: nonEmpty(item.name, `${path}.name`),
      country: country(item.country, `${path}.country`),
      territory_id: nonEmpty(item.territory_id, `${path}.territory_id`),
      territory_name: nonEmpty(item.territory_name, `${path}.territory_name`),
      source_mode: oneOf(item.source_mode, `${path}.source_mode`, [
        "SYNTHETIC",
      ]),
      season_start: seasonStart,
      season_end: seasonEnd,
      is_default: item.is_default,
    };
  });
  const ids = entries.map((item) => item.id);
  if (
    new Set(ids).size !== ids.length ||
    entries.filter((item) => item.is_default).length > 1
  )
    throw new WireError("scenarios");
  return entries;
}

/** Reject malformed or normalized calendar dates at the API boundary. */
function isIsoDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return (
    Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value
  );
}

export function decodeTerritories(value: unknown): Territory[] {
  return list(value, "territories", (entry, path) => {
    const item = record(entry, path);
    return {
      id: nonEmpty(item.id, `${path}.id`),
      country: country(item.country, `${path}.country`),
      kind: oneOf(item.kind, `${path}.kind`, ["country", "region", "district"]),
      name: nonEmpty(item.name, `${path}.name`),
      parent_id: maybe(item.parent_id, text, `${path}.parent_id`),
      reference_id: nonEmpty(item.reference_id, `${path}.reference_id`),
      valid_on: text(item.valid_on, `${path}.valid_on`),
      geometry_status: oneOf(item.geometry_status, `${path}.geometry_status`, [
        "available",
        "missing",
        "invalid",
      ]),
    };
  });
}
/** Decode a WGS84 polygon response without trusting backend JSON shapes implicitly. */
function position(value: unknown, field: string): GeoPosition {
  if (!Array.isArray(value) || value.length !== 2) throw new WireError(field);
  const longitude = numeric(value[0], `${field}[0]`);
  const latitude = numeric(value[1], `${field}[1]`);
  if (Math.abs(longitude) > 180 || Math.abs(latitude) > 90)
    throw new WireError(field);
  return [longitude, latitude];
}
function ring(value: unknown, field: string): GeoPosition[] {
  const positions = list(value, field, position);
  if (positions.length < 4) throw new WireError(field);
  const first = positions[0];
  const last = positions[positions.length - 1];
  if (!first || !last || first[0] !== last[0] || first[1] !== last[1])
    throw new WireError(field);
  return positions;
}
function polygonCoordinates(value: unknown, field: string): GeoPosition[][] {
  const rings = list(value, field, ring);
  if (!rings.length) throw new WireError(field);
  return rings;
}
function referenceShape(value: unknown, field: string): ReferenceShape {
  const object = record(value, field);
  if (object.type === "Polygon") {
    return {
      type: "Polygon",
      coordinates: polygonCoordinates(
        object.coordinates,
        `${field}.coordinates`,
      ),
    };
  }
  if (object.type === "MultiPolygon") {
    const polygons = list(
      object.coordinates,
      `${field}.coordinates`,
      polygonCoordinates,
    );
    if (!polygons.length) throw new WireError(field);
    return { type: "MultiPolygon", coordinates: polygons };
  }
  throw new WireError(`${field}.type`);
}
export function decodeTerritoryGeometry(value: unknown): TerritoryGeometry {
  const object = record(value, "territoryGeometry");
  return {
    territory_id: nonEmpty(
      object.territory_id,
      "territoryGeometry.territory_id",
    ),
    reference_id: nonEmpty(
      object.reference_id,
      "territoryGeometry.reference_id",
    ),
    coordinate_system: oneOf(
      object.coordinate_system,
      "territoryGeometry.coordinate_system",
      ["EPSG:4326"],
    ),
    geometry: referenceShape(object.geometry, "territoryGeometry.geometry"),
  };
}

function stop(value: unknown, path: string): Stop {
  const v = record(value, path);
  const longitude = numeric(v.longitude, `${path}.longitude`);
  const latitude = numeric(v.latitude, `${path}.latitude`);
  if (Math.abs(longitude) > 180 || Math.abs(latitude) > 90)
    throw new WireError(path);
  return {
    site_id: nonEmpty(v.site_id, `${path}.site_id`),
    longitude,
    latitude,
    start: text(v.start, `${path}.start`),
    end: text(v.end, `${path}.end`),
    forage_level: oneOf(v.forage_level, `${path}.forage_level`, [
      "LOW",
      "MEDIUM",
      "HIGH",
    ]),
    evidence_ids: strings(v.evidence_ids, `${path}.evidence_ids`),
  };
}
function plan(value: unknown, path: string): SeasonPlan {
  const v = record(value, path);
  return {
    stops: list(v.stops, `${path}.stops`, stop),
    relocations: integer(v.relocations, `${path}.relocations`),
    rationale: text(v.rationale, `${path}.rationale`),
  };
}
function assessment(value: unknown, path: string): Assessment {
  const v = record(value, path);
  return {
    site_id: nonEmpty(v.site_id, `${path}.site_id`),
    status: oneOf(v.status, `${path}.status`, ecology),
    evidence_ids: strings(v.evidence_ids, `${path}.evidence_ids`),
    rule_ids: strings(v.rule_ids, `${path}.rule_ids`),
    reasons: strings(v.reasons, `${path}.reasons`),
    unknowns: strings(v.unknowns, `${path}.unknowns`),
    synthetic: booleanTrue(v.synthetic, `${path}.synthetic`),
  };
}
function decision(value: unknown, path: string): Decision {
  const v = record(value, path);
  return {
    kind: oneOf(v.kind, `${path}.kind`, decisionKinds),
    site_ids: strings(v.site_ids, `${path}.site_ids`),
    evidence_ids: strings(v.evidence_ids, `${path}.evidence_ids`),
    rule_ids: strings(v.rule_ids, `${path}.rule_ids`),
    note: text(v.note, `${path}.note`),
  };
}
function replanning(value: unknown, path: string): Replanning {
  const v = record(value, path);
  return {
    outcome: oneOf(v.outcome, `${path}.outcome`, [
      "PLAN_FOUND",
      "NO_FEASIBLE_ALTERNATIVE",
      "CHECK_LIMIT_REACHED",
    ]),
    assessments: list(v.assessments, `${path}.assessments`, assessment),
    excluded_site_ids: strings(
      v.excluded_site_ids,
      `${path}.excluded_site_ids`,
    ),
    unknown_site_ids: strings(v.unknown_site_ids, `${path}.unknown_site_ids`),
    decisions: list(v.decisions, `${path}.decisions`, decision),
    checks_used: integer(v.checks_used, `${path}.checks_used`),
    warnings: strings(v.warnings, `${path}.warnings`),
  };
}
function product(value: unknown, path: string): ReportedProduct {
  const v = record(value, path);
  const hazard = v.bee_hazard_class;
  if (hazard !== null && hazard !== 1 && hazard !== 2 && hazard !== 3)
    throw new WireError(`${path}.bee_hazard_class`);
  return {
    name: maybe(v.name, text, `${path}.name`),
    crop: maybe(v.crop, text, `${path}.crop`),
    bee_hazard_class: hazard,
  };
}
function screening(value: unknown, path: string): Screening {
  const v = record(value, path);
  return {
    site_id: nonEmpty(v.site_id, `${path}.site_id`),
    source_record_id: nonEmpty(v.source_record_id, `${path}.source_record_id`),
    source_id: nonEmpty(v.source_id, `${path}.source_id`),
    proximity: oneOf(v.proximity, `${path}.proximity`, proximity),
    approximate_distance_km: maybe(
      v.approximate_distance_km,
      numeric,
      `${path}.approximate_distance_km`,
    ),
    warnings: strings(v.warnings, `${path}.warnings`),
    captured_at: maybe(v.captured_at, text, `${path}.captured_at`),
    scheduled_start: maybe(v.scheduled_start, text, `${path}.scheduled_start`),
    scheduled_end: maybe(v.scheduled_end, text, `${path}.scheduled_end`),
    source_uri: maybe(v.source_uri, text, `${path}.source_uri`),
    products: list(v.products, `${path}.products`, product),
  };
}
function review(value: unknown, path: string): TreatmentReview {
  const v = record(value, path);
  return {
    screenings: list(v.screenings, `${path}.screenings`, screening),
    avoided_site_ids: strings(v.avoided_site_ids, `${path}.avoided_site_ids`),
    warnings: strings(v.warnings, `${path}.warnings`),
  };
}
function evidence(value: unknown, path: string): Evidence {
  const v = record(value, path);
  return {
    id: nonEmpty(v.id, `${path}.id`),
    source_id: nonEmpty(v.source_id, `${path}.source_id`),
    source_mode: oneOf(v.source_mode, `${path}.source_mode`, ["FIXTURE"]),
    synthetic: booleanTrue(v.synthetic, `${path}.synthetic`),
    effective_start: text(v.effective_start, `${path}.effective_start`),
    effective_end: text(v.effective_end, `${path}.effective_end`),
    uncertainty: text(v.uncertainty, `${path}.uncertainty`),
  };
}
export function decodeInvestigation(value: unknown): Investigation {
  const v = record(value, "investigation");
  const request = record(v.request, "request");
  if ("starting_point" in request)
    throw new WireError("request.starting_point");
  return {
    id: nonEmpty(v.id, "id"),
    status: oneOf(v.status, "status", statuses),
    request: {
      country: country(request.country, "request.country"),
      territory_id: nonEmpty(request.territory_id, "request.territory_id"),
      scenario_id: nonEmpty(request.scenario_id, "request.scenario_id"),
      season_start: text(request.season_start, "request.season_start"),
      season_end: text(request.season_end, "request.season_end"),
    },
    created_at: text(v.created_at, "created_at"),
    updated_at: text(v.updated_at, "updated_at"),
    outcome: maybe(
      v.outcome,
      (entry, field) => oneOf(entry, field, outcomes),
      "outcome",
    ),
    plan: maybe(v.plan, plan, "plan"),
    replanning: maybe(v.replanning, replanning, "replanning"),
    treatment_review: maybe(v.treatment_review, review, "treatment_review"),
    evidence: list(v.evidence, "evidence", evidence),
    decision_trace: strings(v.decision_trace, "decision_trace"),
    diagnostics: strings(v.diagnostics, "diagnostics"),
    reference_version: text(v.reference_version, "reference_version"),
    limitations: strings(v.limitations, "limitations"),
    synthetic: booleanTrue(v.synthetic, "synthetic"),
  };
}

/** Strictly decode the server-advertised source capability and matching kind. */
export function decodeSources(value: unknown): ExternalSource[] {
  return list(value, "sources", (entry, path) => {
    const v = record(entry, path);
    const id = oneOf(v.id, `${path}.id`, ["saturn", "open-meteo"]);
    const kind = oneOf(v.kind, `${path}.kind`, [
      "TREATMENT_NOTICE",
      "WEATHER_FORECAST",
    ]);
    const common = {
      country: country(v.country, `${path}.country`),
      mode: oneOf(v.mode, `${path}.mode`, ["LIVE"]),
      status: oneOf(v.status, `${path}.status`, ["EXPERIMENTAL"]),
    };
    if (id === "saturn" && kind === "TREATMENT_NOTICE") {
      return { id, kind, ...common };
    }
    if (id === "open-meteo" && kind === "WEATHER_FORECAST") {
      return { id, kind, ...common };
    }
    throw new WireError(`${path}.sourceKind`);
  });
}

/** Do not convert missing weather values to zero or accept swapped units/time. */
export function decodeWeatherForecast(value: unknown): WeatherForecast {
  const v = record(value, "weather");
  const source_id = oneOf(v.source_id, "weather.source_id", [
    "open-meteo:forecast",
  ]);
  if (v.synthetic !== false) throw new WireError("weather.synthetic");
  const latitude = numeric(v.requested_latitude, "weather.requested_latitude");
  const longitude = numeric(
    v.requested_longitude,
    "weather.requested_longitude",
  );
  const grid_latitude = numeric(v.grid_latitude, "weather.grid_latitude");
  const grid_longitude = numeric(v.grid_longitude, "weather.grid_longitude");
  if (
    Math.abs(latitude) > 90 ||
    Math.abs(grid_latitude) > 90 ||
    Math.abs(longitude) > 180 ||
    Math.abs(grid_longitude) > 180
  ) {
    throw new WireError("weather.coordinates");
  }
  const hours = list(v.hours, "weather.hours", (entry, path) => {
    const hour = record(entry, path);
    const optional = (name: string, min: number, max: number) => {
      const number = maybe(hour[name], numeric, `${path}.${name}`);
      if (number !== null && (number < min || number > max))
        throw new WireError(`${path}.${name}`);
      return number;
    };
    const time = nonEmpty(hour.time, `${path}.time`);
    if (!/(Z|\+00:00)$/.test(time) || !Number.isFinite(Date.parse(time))) {
      throw new WireError(`${path}.time`);
    }
    return {
      time,
      wind_speed_kmh: optional("wind_speed_kmh", 0, 500),
      wind_direction_degrees: optional("wind_direction_degrees", 0, 360),
      wind_gusts_kmh: optional("wind_gusts_kmh", 0, 600),
      precipitation_mm: optional("precipitation_mm", 0, 1000),
    };
  });
  if (hours.length !== 24) throw new WireError("weather.hours");
  let previousTime: number | null = null;
  for (const hour of hours) {
    const currentTime = Date.parse(hour.time);
    if (previousTime !== null && currentTime - previousTime !== 3_600_000) {
      throw new WireError("weather.hours");
    }
    previousTime = currentTime;
  }
  const uncertainties = strings(v.uncertainties, "weather.uncertainties");
  if (uncertainties.length === 0) throw new WireError("weather.uncertainties");
  return {
    source_id,
    source_uri: nonEmpty(v.source_uri, "weather.source_uri"),
    source_mode: oneOf(v.source_mode, "weather.source_mode", ["LIVE"]),
    synthetic: false,
    captured_at: nonEmpty(v.captured_at, "weather.captured_at"),
    requested_latitude: latitude,
    requested_longitude: longitude,
    grid_latitude,
    grid_longitude,
    hours,
    uncertainties,
  };
}

function saturnProduct(
  value: unknown,
  field: string,
): SaturnNotice["products"][number] {
  const v = record(value, field);
  const hazard = v.reported_bee_hazard_class;
  if (hazard !== null && hazard !== 1 && hazard !== 2 && hazard !== 3) {
    throw new WireError(`${field}.reported_bee_hazard_class`);
  }
  return {
    name: maybe(v.name, text, `${field}.name`),
    crop: maybe(v.crop, text, `${field}.crop`),
    reported_bee_hazard_class: hazard,
  };
}

function saturnNotice(value: unknown, field: string): SaturnNotice {
  const v = record(value, field);
  if (v.synthetic !== false) throw new WireError(`${field}.synthetic`);
  const revised = v.revised;
  if (revised !== null && typeof revised !== "boolean")
    throw new WireError(`${field}.revised`);
  return {
    record_id: nonEmpty(v.record_id, `${field}.record_id`),
    plan_id: maybe(v.plan_id, text, `${field}.plan_id`),
    country: country(v.country, `${field}.country`),
    source_id: nonEmpty(v.source_id, `${field}.source_id`),
    source_uri: maybe(v.source_uri, text, `${field}.source_uri`),
    source_mode: oneOf(v.source_mode, `${field}.source_mode`, ["LIVE"]),
    synthetic: false,
    captured_at: nonEmpty(v.captured_at, `${field}.captured_at`),
    published_at: maybe(v.published_at, text, `${field}.published_at`),
    scheduled_start: maybe(v.scheduled_start, text, `${field}.scheduled_start`),
    scheduled_end: maybe(v.scheduled_end, text, `${field}.scheduled_end`),
    revised,
    cadastral_number: maybe(
      v.cadastral_number,
      text,
      `${field}.cadastral_number`,
    ),
    geometry: maybe(v.geometry, referenceShape, `${field}.geometry`),
    products: list(v.products, `${field}.products`, saturnProduct),
    uncertainties: strings(v.uncertainties, `${field}.uncertainties`),
  };
}

/** Reject cross-country/mismatched pages before exposing real field geometries. */
export function decodeSaturnPage(value: unknown): SaturnNoticePage {
  const v = record(value, "saturnPage");
  if (v.coverage_complete !== false)
    throw new WireError("saturnPage.coverage_complete");
  const page = {
    source_id: nonEmpty(v.source_id, "saturnPage.source_id"),
    country: country(v.country, "saturnPage.country"),
    region_code: integer(v.region_code, "saturnPage.region_code"),
    captured_at: nonEmpty(v.captured_at, "saturnPage.captured_at"),
    page_number: integer(v.page_number, "saturnPage.page_number"),
    next_page: maybe(v.next_page, integer, "saturnPage.next_page"),
    total_elements: maybe(
      v.total_elements,
      integer,
      "saturnPage.total_elements",
    ),
    unidentified_records: integer(
      v.unidentified_records,
      "saturnPage.unidentified_records",
    ),
    notices: list(v.notices, "saturnPage.notices", saturnNotice),
    coverage_complete: false as const,
  };
  if (
    page.notices.some(
      (notice) =>
        notice.country !== page.country || notice.source_id !== page.source_id,
    )
  ) {
    throw new WireError("saturnPage.noticeScope");
  }
  return page;
}
