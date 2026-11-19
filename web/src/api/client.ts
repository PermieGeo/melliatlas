import {
  decodeCountries,
  decodeSettlementSuggestions,
  decodeAreaDistrictResult,
  decodeSources,
  decodeSaturnPage,
  decodeWeatherForecast,
  decodeInvestigation,
  decodeScenarios,
  decodeTerritories,
  decodeTerritoryGeometry,
  decodeTerritoryAtPoint,
  WireError,
} from "./validation";
import type {
  Country,
  SettlementSuggestion,
  AreaDistrictResult,
  ExternalSource,
  SaturnNoticePage,
  WeatherForecast,
  Position,
  CountryCode,
  Investigation,
  InvestigationCreate,
  ScenarioListing,
  Territory,
  TerritoryGeometry,
  TerritoryAtPoint,
} from "./types";

export type ApiResult<T> =
  | { kind: "ok"; data: T }
  | { kind: "error"; status: number | null; code: string; message: string };

function isAbort(error: unknown): boolean {
  return (
    typeof error === "object" &&
    error !== null &&
    "name" in error &&
    error.name === "AbortError"
  );
}

function abortedResult(): ApiResult<never> {
  return {
    kind: "error",
    status: null,
    code: "ABORTED",
    message: "Запрос отменён",
  };
}

function errorMessage(
  response: unknown,
): { code: string; message: string } | null {
  if (
    typeof response !== "object" ||
    response === null ||
    Array.isArray(response)
  )
    return null;
  if (!("error" in response)) return null;
  const envelope = response.error;
  if (
    typeof envelope !== "object" ||
    envelope === null ||
    Array.isArray(envelope)
  )
    return null;
  if (!("code" in envelope) || !("message" in envelope)) return null;
  if (typeof envelope.code !== "string" || typeof envelope.message !== "string")
    return null;
  return { code: envelope.code, message: envelope.message };
}

async function request<T>(
  path: string,
  signal: AbortSignal,
  decode: (value: unknown) => T,
  init?: RequestInit,
): Promise<ApiResult<T>> {
  if (signal.aborted) return abortedResult();
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      signal,
      headers: { Accept: "application/json", ...init?.headers },
    });
  } catch (error) {
    if (signal.aborted || isAbort(error)) return abortedResult();
    return {
      kind: "error",
      status: null,
      code: "NETWORK_ERROR",
      message: "API недоступен. Проверьте запуск backend.",
    };
  }
  if (signal.aborted) return abortedResult();
  let payload: unknown;
  try {
    payload = await response.json();
  } catch (error) {
    if (signal.aborted || isAbort(error)) return abortedResult();
    return {
      kind: "error",
      status: response.status,
      code: "INVALID_RESPONSE",
      message: "Ответ API не является JSON",
    };
  }
  if (signal.aborted) return abortedResult();
  if (!response.ok) {
    const details = errorMessage(payload);
    return {
      kind: "error",
      status: response.status,
      code: details?.code ?? "HTTP_ERROR",
      message: details?.message ?? `HTTP ${response.status}`,
    };
  }
  try {
    return { kind: "ok", data: decode(payload) };
  } catch (error) {
    if (signal.aborted || isAbort(error)) return abortedResult();
    if (error instanceof WireError) {
      return {
        kind: "error",
        status: response.status,
        code: "INVALID_RESPONSE",
        message: error.message,
      };
    }
    // An unexpected decoder defect is not a transport failure or a malformed wire value.
    return {
      kind: "error",
      status: response.status,
      code: "CLIENT_ERROR",
      message: "Внутренняя ошибка обработки ответа API.",
    };
  }
}

export function listCountries(
  signal: AbortSignal,
): Promise<ApiResult<Country[]>> {
  return request("/api/v1/territories/countries", signal, decodeCountries);
}
export function listRegions(
  country: CountryCode,
  signal: AbortSignal,
): Promise<ApiResult<Territory[]>> {
  return request(
    `/api/v1/territories/regions?country=${encodeURIComponent(country)}`,
    signal,
    decodeTerritories,
  );
}
export function listDistricts(
  regionId: string,
  signal: AbortSignal,
): Promise<ApiResult<Territory[]>> {
  return request(
    `/api/v1/territories/districts?region_id=${encodeURIComponent(regionId)}`,
    signal,
    decodeTerritories,
  );
}
/** Name search is opt-in, server-proxied and unrelated to the private point resolver. */
export function searchSettlements(
  country: CountryCode,
  query: string,
  locale: "ru" | "en",
  signal: AbortSignal,
): Promise<ApiResult<SettlementSuggestion[]>> {
  return request(
    "/api/v1/sources/geocoding/settlements",
    signal,
    decodeSettlementSuggestions,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ country, query, language: locale }),
    },
  );
}

/** Keep private map click coordinates in a POST body, never the URL. */
export function resolveTerritoryPoint(
  country: CountryCode,
  point: Position,
  signal: AbortSignal,
): Promise<ApiResult<TerritoryAtPoint>> {
  return request(
    "/api/v1/territories/resolve-point",
    signal,
    decodeTerritoryAtPoint,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        country,
        longitude: point.longitude,
        latitude: point.latitude,
      }),
    },
  );
}

/** Send unsaved private coordinates in a POST body; the server does not persist them. */
export function lookupIntersectingDistricts(
  draft: {
    country: CountryCode;
    regionId: string;
    center: Position;
    widthKm: number;
    heightKm: number;
  },
  signal: AbortSignal,
): Promise<ApiResult<AreaDistrictResult>> {
  return request(
    "/api/v1/territories/intersecting-districts",
    signal,
    decodeAreaDistrictResult,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        country: draft.country,
        region_id: draft.regionId,
        latitude: draft.center.latitude,
        longitude: draft.center.longitude,
        width_km: draft.widthKm,
        height_km: draft.heightKm,
      }),
    },
  );
}

/** Read a validated WGS84 reference shape; no synthetic fallbacks. */
export function getTerritoryGeometry(
  territoryId: string,
  signal: AbortSignal,
): Promise<ApiResult<TerritoryGeometry>> {
  return request(
    `/api/v1/territories/geometry/${encodeURIComponent(territoryId)}`,
    signal,
    decodeTerritoryGeometry,
  );
}
/** Discover actual executable scenarios; an empty list means none for that country. */
export function listScenarios(
  country: CountryCode,
  signal: AbortSignal,
): Promise<ApiResult<ScenarioListing[]>> {
  return request(
    `/api/v1/investigations/scenarios?country=${encodeURIComponent(country)}`,
    signal,
    decodeScenarios,
  );
}

export function startInvestigation(
  body: InvestigationCreate,
  signal: AbortSignal,
): Promise<ApiResult<Investigation>> {
  return request("/api/v1/investigations", signal, decodeInvestigation, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
export function getInvestigation(
  id: string,
  signal: AbortSignal,
): Promise<ApiResult<Investigation>> {
  return request(
    `/api/v1/investigations/${encodeURIComponent(id)}`,
    signal,
    decodeInvestigation,
  );
}

/** Discover enabled external sources for a country; never infer from its name. */
export function listExternalSources(
  country: CountryCode,
  signal: AbortSignal,
): Promise<ApiResult<ExternalSource[]>> {
  return request(
    `/api/v1/sources?country=${encodeURIComponent(country)}`,
    signal,
    decodeSources,
  );
}

/** One manual, bounded public-source read; no automatic pagination or retries. */
export function readSaturnPage(
  country: CountryCode,
  region: number | string,
  pageNumber: number,
  signal: AbortSignal,
  scope?: { districtId: string; dateStart: string; dateEnd: string },
): Promise<ApiResult<SaturnNoticePage>> {
  return request(
    "/api/v1/sources/saturn/treatments",
    signal,
    decodeSaturnPage,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        country,
        ...(typeof region === "number"
          ? { region_code: region }
          : { region_id: region }),
        page_number: pageNumber,
        ...(scope
          ? {
              district_id: scope.districtId,
              date_start: scope.dateStart,
              date_end: scope.dateEnd,
            }
          : {}),
      }),
    },
  );
}

/** Read one short-range forecast only when a user explicitly selects a point. */
export function readWeatherForecast(
  point: Position,
  signal: AbortSignal,
): Promise<ApiResult<WeatherForecast>> {
  return request(
    "/api/v1/sources/weather/forecast",
    signal,
    decodeWeatherForecast,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        latitude: point.latitude,
        longitude: point.longitude,
      }),
    },
  );
}
