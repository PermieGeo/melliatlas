import {
  decodeCountries,
  decodeInvestigation,
  decodeScenarios,
  decodeTerritories,
  decodeTerritoryGeometry,
  WireError,
} from "./validation";
import type {
  Country,
  CountryCode,
  Investigation,
  InvestigationCreate,
  ScenarioListing,
  Territory,
  TerritoryGeometry,
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
  try {
    const response = await fetch(path, {
      ...init,
      signal,
      headers: { Accept: "application/json", ...init?.headers },
    });
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
      if (error instanceof WireError) {
        return {
          kind: "error",
          status: response.status,
          code: "INVALID_RESPONSE",
          message: error.message,
        };
      }
      throw error;
    }
  } catch (error) {
    if (signal.aborted || isAbort(error)) return abortedResult();
    return {
      kind: "error",
      status: null,
      code: "NETWORK_ERROR",
      message: "API недоступен. Проверьте запуск backend.",
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
